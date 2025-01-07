import requests
import asyncio
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime



async def search_products(
        country: str,
        keywords: List[str],
        search_index: str,
):
    query = "+".join(keywords)

    domain = f"https://amazon.{country}"

    url = f'{domain}/s?language=en&k={query}&i={search_index}'



    params = {
        'api_key': "0390fdf9a3303227c43bc102619ef328",
        'url': url,
        'country_code': 'us',
        'tld': country,
        'autoparse': 'true',
        'device_type': 'desktop'
    }

    r = requests.get('https://api.scraperapi.com/', params=params)

    results = r.text
    return results

# Run the asynchronous function
async def main():
    start = datetime.now()
    results = await search_products(
        "ae",
        ["keyboard","wireless", "mechnical"],
        "electronics"
    )
    finish_search = datetime.now() - start
    print("_++++++++++++++++++++++")
    print(f"Search Time:____________{finish_search} sec")



# Start the asyncio event loop
asyncio.run(main())

