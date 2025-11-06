# plumx-citation-extraction

This is a copy of a repository that I built for the Center for Scientific Integrity's Medical Evidence Project.

## Overview

Elsevier's PlumX Metrics compile insights into the public impact individual research publications have, such as their citations in policy guidelines and mentions in news stories. This repositiory provides an automated pipeline to search the ScienceDirect or Scopus database spanning a variety of criteria, to identify an article's PlumX Metrics, and to extract an article's objects (i.e. figures). It draws on APIs from both ScienceDirect and Scopus, which are distinct in the articles and article data that they provide. The table below displays the specific APIs implemented in the pipeline:

| ScienceDirect APIs  | Scopus APIs |
| ------------- | ------------- |
| ScienceDirect Search V2  | Scopus Search  |
| Article Retrieval  | Plumx Metrics  |
| Object Retrieval  |  |

For a list of all Elsevier APIs, including those for other platforms, see the available [Elsevier APIs](https://dev.elsevier.com/api_docs.html).

***Limitations*** to retrieval access include *(1)* Elsevier's throttling/query caps and *(2)* incongruencies across ScienceDirect and Scopus. See Elsevier's API-specific throttling and query caps: [Data Retrieval Settings](https://dev.elsevier.com/api_key_settings.html). Not all articles on ScienceDirect are listed on Scopus, and vice versa. Because PlumX is Scopus-based, only ScienceDirect articles that are cross-listed will include PlumX Metrics. Incongruencies across ScienceDirect and Scopus extend to other facets of the pipeline, such as search criteria. For example, only Scopus allows searching by an author's Scopus ID.

***Future Directions*** may query policy impact directly via Overton APIs and data services: [Overton APIs](https://app.overton.io/swagger.php?__hstc=168130942.8ba61be3869dac127a1b54268c8b2314.1758912226564.1759360819164.1759865019632.4&__hsfp=8ba61be3869dac127a1b54268c8b2314) and [Overton Data Snapshots](https://help.overton.io/article/overton-data-snapshots/).

## Getting Started
Prior to starting, download the repository and ensure that you:  

**(1)** pass your API Key 🔑 and Institutional Token 🪙 (if necessary) as follows to a .env file in the plumx-citation-extraction directory. Note *not* to include any spaces around the ```=```.
```
ELSEVIER_API_KEY=<YOUR API KEY HERE>
ELSEVIER_INST_TOKEN=<YOUR INSTITUTIONAL TOKEN HERE>
```

**(2)** install required packages to your environment. The plumx-citation-extraction pipeline uses the following Python packages:
```time, json, requests, os, datetime, dotenv, typing, csv```.






