import json
import os

input_directory = "/Users/adamoregan/Documents/mep_internship/plumx-citation-extraction/development" 
input_ipynb_filename = "pipeline_development.ipynb" # .ipynb file to access
output_directory = "/Users/adamoregan/Documents/mep_internship/plumx-citation-extraction/scripts"
output_py_filename = "elsevier_api_client.py" # .py file to (over)write

tag_name = "service"
action = "w" # a = append or w = write


#####  #####   #####   #####   #####   #####   #####   #####   #####

ans = "y"

path_to_output = os.path.join (output_directory, output_py_filename)

if os.path.exists (path_to_output) :

    ans = input ("Output already exists. Proceed? ")
    ans = ans.lower().strip()

if ans in ["y" , "yes" , "true" , "t"] :
    
    path_to_ipynb = os.path.join (input_directory, input_ipynb_filename)
    with open(path_to_ipynb, 'r') as f:
        nb = json.load(f)

    exported_code = []
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            tags = cell.get('metadata', {}).get('tags', [])
            if tag_name in tags:
                exported_code.append(''.join(cell['source']))

    with open(path_to_output, action) as f:
        f.write('\n\n'.join(exported_code))

else :
    print ("Exiting program.")