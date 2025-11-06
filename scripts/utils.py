import time
import json
import requests
import os
import datetime
import dotenv
import typing
import csv
import IPython

def load_api_credentials ():
    """Load credentials from .env file."""
    
    dotenv.load_dotenv ()

    api_key = os.getenv ("ELSEVIER_API_KEY")
    inst_token = os.getenv ("ELSEVIER_INST_TOKEN", "")

    return api_key, inst_token

def save_binary_file (filepath, data) :
    """Save binary content to file."""

    with open (filepath, "wb") as f :
        f.write (data.content)

def write_headers (api_key, inst_token, accept = "*/*") :
    """Generate header construction for API call."""

    headers = { "X-ELS-APIKey" : api_key , "Accept" : accept}

    if inst_token != "" :
        headers["X-ELS-Insttoken"] = inst_token
    
    return headers

def join_with_operator (search_terms: list, operator: typing.Literal["AND", "OR"]) -> str:
    """Generic list joining with operator."""

    if operator not in ["AND", "OR"] :
        raise ValueError ("Operator must be 'AND' or 'OR'.")

    return f" {operator} ".join (search_terms)