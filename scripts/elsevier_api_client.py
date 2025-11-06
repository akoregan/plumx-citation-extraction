import time
import json
import requests
import os
import datetime
import dotenv
import typing
import csv
import IPython

def iterate_search_info (data) :
    """Helper function for search_database: extracts entry metadata and pagination information in case of multi-page ScienceDirect & Scopus search requests.

    Args:
        data (dict): Dictionary data that's returned from search request.

    Returns:
        tuple: entry metadata (dict), total hits (int), starting entry no. (int), no. entries per page (int)
    """
    
    try :

        search_results = data['search-results']

        entries = search_results.get ('entry')

        total = int (search_results.get ('opensearch:totalResults'))
        start = int (search_results.get ('opensearch:startIndex'))
        per_page = int (search_results.get ('opensearch:itemsPerPage'))
        
        return entries, total, start, per_page
    
    except :

        print ("Key error: 'search-results' does not exist in output. See response below.")
        print (data)

def fetch_data (url, headers, params = None) :
    """Executes an API request.

    Args:
        url (str): web address used to access an API
        headers (dict): parameters passed to the headers arguments
        params (dict, optional): additional query parameters for specifying request. Defaults to None.

    Raises:
        ValueError: Raised when the API response content-type is XML. JSON format is required.

    Returns:
        requests.Response | dict: Returns the raw response object for image or PDF content, or a parsed dictionary for JSON content.
    """

    if params :
        response = requests.get (url, headers=headers, params=params)
    else :
        response = requests.get (url, headers=headers)
    
    content_type = response.headers.get('content-type', '')

    if "image" in content_type or "pdf" in content_type :
        return response
    elif "json" in content_type :
        return response.json ()
    elif "xml" in content_type :
        raise ValueError ("Output is in XML. Specify 'application/json' in headers.")

def write_query (keywords = None, subjs = None, author_ids = None, authors = None, date_range = None) :
    """Builds a query dictionary with hard-coded start, count, and field keys, an input data range, and 
    query string generated from optional input parameters. 

    Args:
        keywords (list, optional): list of keywords to search in title fields. Defaults to None.
        subjs (list, optional): list of subject areas to filter by. Defaults to None.
        author_ids (list, optional): list of author IDs to filter results. Defaults to None.
        authors (list, optional): list of author names to search for. Defaults to None.
        date_range (str, optional): date range filter in the format expected by the API. Defaults to None.

    Raises:
        ValueError: Raised when no search criteria are provided, resulting in an empty query string.

    Returns:
        dict: A parameters dictionary containing the constructed query string along with pagination 
        settings (start, count), date range, and requested fields (DOI, title, publication name, 
        publication date, creator).
    """

    params = {
        "start" : 0, 
        "count" : 50,
        "field" : "prism:doi,dc:title,prism:publicationName,prism:coverDate,dc:creator"
        }
    
    if date_range :
        params["date"] = date_range

    query_list = [] 

    if keywords :
        keywords = [f"'{keyword}'" for keyword in keywords]
        keywords = join_with_operator (keywords, "AND")
        query_list.append (f"TITLE({keywords})")
    if subjs :
        subjs = join_with_operator (subjs, "OR")
        query_list.append (f"SUBJAREA({subjs})")
    if author_ids :
        author_ids = [f"AU-ID({str(id)})" for id in author_ids]
        author_ids = join_with_operator (author_ids, "OR")
        query_list.append (author_ids)
    if authors :
        authors = join_with_operator (authors, "OR")
        query_list.append (f"AUTHOR-NAME({authors})")
    
    params["query"] = join_with_operator (query_list, "AND")

    if params["query"] == "" :
        raise ValueError ("Query parameter cannot be empty.")
    else :
        return params    

def filepath_to_output (output_name) : 

    if IPython.get_ipython () :
        __file__ = "placeholder_for_jupyter.will_not_run_in_py"
    else :
        pass

    current_dir = os.path.dirname (os.path.abspath (__file__))
    output_dir = os.path.join (current_dir, "..", "results", output_name)

    return output_dir  

def extract_count (categories, citation_type, kind):
    """Searches through the nested structure of the PlumX API response categories to identify citation 
    counts of specified type & kind.

    Args:
        categories (list): list of category dictionaries.
        citation_type (str): the type of citation to search for.
        kind (str): the category name to search for.

    Returns:
        int: The total count of the specified citation type or 0 if citation type or kind is not found.
    """

    for c in categories:
        if c["name"] == kind:
            types = c["count_types"]
            for t in types:
                if citation_type in t["name"].lower():
                    return t["total"]
                
    return 0

def access_citation_counts (plumx_response, citation_type):
    """Extracts and returns citation count data from a PlumX response object. Supports querying 
    for news mentions, policy citations, or both types simultaneously.

    Args:
        plumx_response (dict): a PlumX API response dictionary.
        citation_type (str): the type of citation to retrieve. Must be one of: "news", "policy", 
        or "both".

    Raises:
        ValueError: Raised when citation_type is not one of the valid options.

    Returns:
        dict: A dictionary containing the requested citation count(s).
    """
    
    citation_type = citation_type.lower().strip()
    
    try:
        categories = plumx_response["count_categories"]
    except:
        try:
            print(f"No PlumX data for: {plumx_response['id_value']}")
            
            if citation_type == "both" :
                return {"news": None, "policy": None}
            else :
                return {citation_type : None}
            
        except:
            print("No PlumX data. Article missing DOI.")
            
            if citation_type == "both" :
                return {"news": None, "policy": None}
            else :
                return {citation_type : None}
    
    if citation_type == "both":
        news_count = extract_count(categories, "news", "mention")
        policy_count = extract_count(categories, "policy", "citation")
        return {"news": news_count, "policy": policy_count}
    
    elif citation_type == "news":
        kind = "mention"
    elif citation_type == "policy":
        kind = "citation"
    else:
        raise ValueError("Citation type must be 'news', 'policy', or 'both'.")
    
    count = extract_count(categories, citation_type, kind)
    
    return {citation_type : count}

def search_database (keywords = None,
                     date_range = None,
                     authors = None, 
                     subjs = None, 
                     author_ids = None, 
                     database_name = "scidir", 
                     max_results = 50,
                     save_to_csv = False
                     ) :
    """    
    Search the Science Direct or Scopus database within the parameters of keyword and date range inputs.

    Args:
        keywords (list of strs, optional): search keywords (ex: ["meta-analysis, depression"]). Defaults to None.
        date_range (str, optional): 4-digit years separated by a dash (ex: "2020-2025"). Defaults to None.
        authors (list of strs, optional): author names (ex: ["Abdellasset", "Fujii"] or ["Abdellasset, W"]). Defaults to None.
        subjs (list of strs, optional): scopus only - 4-letter scopus subject code (ex: ["MEDI"]). Defaults to None.
        author_ids (list of strs, optional): scopus only - scopus author ID number. Defaults to None.
        database_name (str, optional): "scopus" or "sciencedirect", "scidir". Defaults to "scidir". 
        max_results (int, optional): safeguard to prevent exhausting API resources; set to None to return all entries. Defaults to 25.
        save_to_csv (bool, optional): saves API request to a csv file if True in addition to default json file. Defaults to False.

    Returns:
        list of dicts: Each dict includes entry metadata (doi, title, publication name, etc.)
    """
    
    api_key, inst_token = load_api_credentials ()
    
    database_name = database_name.lower().strip()
    if database_name == "scopus" :
        search_url = "https://api.elsevier.com/content/search/scopus"
    elif database_name == "sciencedirect" or database_name == "scidir" :
        search_url = "https://api.elsevier.com/content/search/sciencedirect"
    
    if author_ids and "sciencedirect" in search_url :
        raise ValueError ("SciDir does not accept subject or author ID. Provide author name or use Scopus.")
    if subjs and "sciencedirect" in search_url :
        raise ValueError ("SciDir does not accept the subject query parameter. Use Scopus.")

    headers = write_headers (api_key, inst_token, accept = "application/json")
    params = write_query (keywords=keywords, subjs=subjs, author_ids=author_ids, authors=authors, date_range=date_range)
    print (params)

    all_entries = []

    while True :

        my_request = fetch_data (search_url, headers = headers, params = params)
        entries, total, start, per_page = iterate_search_info (my_request)
        
        all_entries.extend (entries)

        next_start = start + len (entries)
        print (f'Fetched {next_start}/{total} entries.')

        if next_start >= total : 
            break
        if max_results and len (all_entries) >= max_results :
            break
        
        params['start'] = str (next_start)
        time.sleep (5.0)

    output_dir = filepath_to_output ("search_queries")
    os.makedirs (output_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    with open (f"{output_dir}/{database_name}_search_{timestamp}.json", "w") as f :
        json.dump (all_entries, f)

    if save_to_csv == True :
        
        with open (f"{output_dir}/{database_name}_search_{timestamp}.csv", "w") as f :
            writer = csv.writer (f)
            writer.writerow (all_entries[0].keys()) # write column headers
            writer.writerows([entry.values() for entry in all_entries])

    return all_entries

def get_plumx_metrics (entries, save_to_file = True) :
    """Accesses PlumX news and policy metrics for a list of input articles, identified via DOI.

    Args:
        entries (list of dicts): List of entries - each represented by a dict with "prism:doi" key.
        save_to_file (bool, optional): saves API request to a csv file if True. Defaults to True.

    Returns:
        list of dicts: Equivalent to input parameter entries except with entry-specific PlumX data 
        appended to each dict.
    """     

    api_key, inst_token = load_api_credentials ()

    for i in range (len (entries)) :

        try :
            article_doi = entries[i]["prism:doi"]
        except :
            print (f"Article no. {i} missing DOI.")
            entries[i]["policy_citation_count"] = None
            entries[i]["news_mentions"] = None
            pass

        plumx_url = f"https://api.elsevier.com/analytics/plumx/doi/{article_doi}"
        headers = write_headers (api_key, inst_token, accept = "application/json")
        
        my_request = fetch_data (plumx_url, headers = headers)

        citation_counts = access_citation_counts (my_request, "both")
        entries[i]["policy_citation_count"] = citation_counts["policy"]
        entries[i]["news_mentions"] = citation_counts["news"]
    
    entries = [entry for entry in entries if "policy_citation_count" in entry and "news_mentions" in entry]
    
    entry_sorter = lambda item: (
        item["policy_citation_count"] if item["policy_citation_count"] is not None else float("-inf"), 
        item["news_mentions"] if item["policy_citation_count"] is not None else float("-inf")
    )

    entries = sorted (entries, key=entry_sorter, reverse=True)

    if save_to_file == True :

        output_dir = filepath_to_output ("search_queries")
        os.makedirs (output_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        with open (f"{output_dir}/plumx_output_{timestamp}.csv", "w") as f :
            writer = csv.writer (f)
            writer.writerow (entries[0].keys()) # write column headers
            writer.writerows([entry.values() for entry in entries])
    
    return entries

def retrieve_article_graphics (article_dictionary, save_manuscript = False) :
    """Saves all graphics in high-res for a specified article to the input directory. 

    Args:
        article_dictionary (dict): Article metadata dictionary, including the key "prism:doi".
        save_manuscript (bool, optional): Saves any PDFs associated with article to specified directory. Defaults to False.
        filepath (str, optional): Directory in which to store retrieved objects. Defaults to "./object_retrieval_data".

    Raises:
        KeyError: The article dictionary parameter must include the key "prism:doi".
    """
    
    api_key, inst_token = load_api_credentials ()

    article_doi = article_dictionary.get ("prism:doi")
    if not article_doi :
        print ("DOI not found in article_dictionary.")
        return

    try :
        
        object_retrieval_url = f"https://api.elsevier.com/content/object/doi/{article_doi}"
        headers = write_headers (api_key, inst_token, accept = "application/json")
        object_data = fetch_data (object_retrieval_url, headers=headers)

    except :

        print (f"Trouble executing article retrieval API for article: {article_doi}")
        return
    
    try :

        object_data = object_data['choices']['choice']
        graphics = sorted (list ({obj["@ref"] for obj in object_data if "gr" in obj["@ref"]}))
    
    except :

        print (f"Could not find any graphic renderings in article retrieval response: {article_doi}. May not exist.")
        graphics = None

    output_dir = filepath_to_output ("object_requests")
    graphic_renderings_dir = os.path.join (output_dir, "graphic_renderings")
    os.makedirs (graphic_renderings_dir, exist_ok=True)
    if save_manuscript:
        author_manuscripts_dir = os.path.join(output_dir, "author_manuscripts")
        os.makedirs(author_manuscripts_dir, exist_ok=True)
    
    headers ["Accept"] = "*/*"

    if graphics :
        for gr in graphics :
            
            try :
                object_specified_url = f"{object_retrieval_url}/ref/{gr}/high"
                object_request = fetch_data (object_specified_url, headers=headers)
            
                timestamp = datetime.datetime.now().strftime("%Y%m%d")
                a_filepath = os.path.join (graphic_renderings_dir, f"{article_doi.replace('/','.')}_{gr}_{timestamp}.jpg")
                save_binary_file (a_filepath, object_request)
            
            except :
                print (f"Could not retrieve {gr} from article: {article_doi}")
                continue

    if save_manuscript == True :

        try :

            man_urls = list ({obj["$"] for obj in object_data if "am" in obj["@ref"].lower() and "pdf" in obj["@type"].lower()})

            if not man_urls :
                print (f"No PDFs found for manuscript: {article_doi}.")
                return
        
        except :

            print (f"Could not find any author manuscripts in article retrieval response: {article_doi}. May not exist.")
            man_urls = None

        if man_urls :
            for man_url in man_urls : 

                try :
                        
                    pdf_request = fetch_data (man_url, headers = headers)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    a_filepath = os.path.join (author_manuscripts_dir, f"manuscript_{timestamp}.pdf")
                    save_binary_file (a_filepath, pdf_request)
        
                except :

                    print (f"Could not download author manuscript for article: {article_doi}")
                    return
