from dotenv import load_dotenv
import os
from typing import List, Optional
import requests
import json
from app.models import Product
from sqlalchemy.ext.asyncio import AsyncSession
from bs4 import BeautifulSoup
from extraction_rules import extract_rules

# Load environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("SCRAPERAPI_API_KEY")

localization = {
    "ae": {"url": "https://www.amazon.ae", "currency": "AED"},
    "eg": {"url": "https://www.amazon.eg", "currency": "EGP"},
    "sa": {"url": "https://www.amazon.sa", "currency": "SAR"},
    "us": {"url": "https://www.amazon.sa", "currency": "$"},
}


async def amazon_search(
        country: str,
        keywords: List[str],
        search_index: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):
    query = "+".join(keywords)

    url = f'https://www.amazon.{country}/s?language=en&k={query}&i={search_index}'

    # Add price filters to the URL if provided
    if min_price is not None:
        url += f'&low-price={min_price}'
    if max_price is not None:
        url += f'&high-price={max_price}'

    params = {
        'api_key': API_KEY,
        'url': url,
        #'country_code': 'us',
        #'tld': country,
        'autoparse': 'true',
        #'device_type': 'desktop',
        'premimum': True
    }

    r = requests.get('https://api.scraperapi.com/', params=params)
    results = json.loads(r.text)
    products_dict = []
    for product in results['results'][:7]:
        result = {
            "platform": "amazon",
            "country": country,
            "asin": product['asin'],
            "name": product['name'],
            "images": [product['image']],
            "currency": product.get('price_symbol', "Pice on selection"),
            "price": product.get('price', 0),
            "rating": product.get("stars", 3.2)
        }
        products_dict.append(result)

    return products_dict

async def amazon_products_details(db: AsyncSession, productId: str, country: str):
    url = f'https://amazon.{country}/dp/{productId}?language=en'

    params = {
        'api_key': API_KEY,
        'url': url,
        'country_code': 'us',
        'tld': country,
        'autoparse': 'true',
        'device_type': 'desktop'
    }
    r = requests.get('https://api.scraperapi.com/', params=params)

    product_details = json.loads(r.text)

    saved_product = await Product.find_by_asin(db,productId)

    new_params = {
        "platform": "amazon",
        "country": country,
        "asin": productId,
        "name": product_details.get("name", "No title"),
        "images": product_details.get("images", []),
        "currency": saved_product.price_symbol,
        "price": saved_product.price,
        "feature_bullets": product_details.get("feature_bullets", []),
        "rating": product_details.get("average_rating", 3.2)
    }

    return new_params



async def noon_search(
        country: str,
        keywords: List[str],
        search_index: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):
    query = "+".join(keywords)
    localization= {
        "eg": "egypt-en",
        "ae": "uae-en",
        "sa": "saudi-en"
    }

    url = f'https://www.noon.com/{localization[country]}/search/?q={query}'
    
    # Add price filters to the URL if provided
    if min_price is not None:
        url += f'&f%5Bprice%5D%5Bmin={min_price}'
    if max_price is not None:
        url += f'&f%5Bprice%5D%5Bmax={max_price}'

    params = {
        'api_key': API_KEY,
        'url': url,
        #'country_code': 'us',
        #'tld': country,
        #'autoparse': 'true',
        'device_type': 'desktop',
        'render': True,
        'premimum': True
    }

    r = requests.get('https://api.scraperapi.com/', params=params)
    results = json.loads(r.text)

    
    soup = BeautifulSoup(results, 'html.parser')

    # Find all product containers
    product_containers = soup.select(extract_rules["products"]["selector"])

    # Initialize the list to store extracted data
    extracted_data = []

    # Iterate over each product container
    for container in product_containers[:10]:
        data = {}
        # Extract the fields based on the updated rules
        for field, rule in extract_rules["products"]["fields"].items():
            selector = rule.get("selector")
            attribute = rule.get("attribute")
            
            element = container.select_one(selector)
            if element:
                if attribute == "text":
                    data[field] = element.get_text(strip=True)
                else:
                    data[field] = element.get(attribute)
            else:
                data[field] = None
        data['asin'] = data['asin'].split('-')[1]
        # Collect all image URLs inside the productContainer
        image_tags = container.find_all('img')
        images = []
        for img in image_tags:
            if 'src' in img.attrs:
                src = img['src']
                # Filter for .jpg images
                if not src.lower().endswith('.png') and not src.lower().endswith('.svg'):
                    # Remove URL parameters
                    parsed_url = src.split('?')[0]
                    images.append(parsed_url)
        
        data['images'] = sorted(list(set(images)))

        # Append data to the list
        extracted_data.append(data)

    # Output the results as JSON
    return json.dumps(extracted_data, indent=4, ensure_ascii=False)
