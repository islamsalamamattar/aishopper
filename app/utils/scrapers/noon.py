from typing import List, Optional
import json
import requests
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from extraction_rules import extract_rules
from parse_noon import noon_parse_search

def noon_search():
    base_url = 'https://noon.com/egypt-en/search/'
    query_params = {'q': 'hoodie'}
    encoded_query = urllib.parse.urlencode(query_params)
    url = f'{base_url}?{encoded_query}'
    print(url)

    start = datetime.now()
    payload = {
    "api_key": "wYo0i8hA1kEEueJEiTF7UqfRDtO9oKfX1v8VY8Z3RiitYNMsiflbN6unNC0RFpaZKHrMjKO2WjMiTJcXAG",
    "url": url,
    "geo": "us",
    #"render_js": "true",
    "js_scenario": json.dumps({"steps": [ {"wait": 100}]}) 
    }
    
    response = requests.get("https://scraping.narf.ai/api/v1/", params=payload)

    # Parse the JSON response
    content = noon_parse_search(response.content.decode('utf-8'))
    products = "\n"
    for product in content:
        product_dict =f"""
{product['asin']}
{product['name']}
{product['currency']} {product['price']}
{product['rating']}
"""
        for image in product['images']:
            product_dict += f"{image} \n"
        products += product_dict

    print(content)
    duration1 = datetime.now() - start
    duration2 = datetime.now() - start   


    print(f'scraping completed in : {duration1}')
    print(f'extraction completed in : {duration2 - duration1}')
    print(f'total time : {duration2}')

def main():
    noon_search()

if __name__ == "__main__":
    main()

