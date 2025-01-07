import requests
import json
import logging
import sys
from dotenv import load_dotenv
import os
import urllib.parse
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.scrapers.parse_noon import noon_parse_search
from app.models import Product



# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Adjust the level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Logs to stdout (captured by systemd)
        logging.FileHandler('/home/admin/arobah/arobah_api/logger.log'),  # Optional file logging
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("SCRAPING_FISH_API_KEY")


async def amazon_search(
        country: str,
        keywords: List[str],
        search_index: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):
    query = "+".join(keywords)

    url = f'https://amazon.{country}/s?language=en&k={query}&i={search_index}'

    # Add price filters to the URL if provided
    if min_price is not None:
        url += f'&low-price={min_price}'
    if max_price is not None:
        url += f'&high-price={max_price}'

    payload = {
    "api_key": API_KEY,
    "url": url,
    "extract_rules": json.dumps({
        "products": {
            "type": "all",
            "selector": ".s-result-item:not(.AdHolder)",
            "output": {
                "asin": {
                    "selector": ".a-declarative",
                    "output": "@data-csa-c-item-id"
                },
                "name": {
                    "selector": "h2",
                    "output": "text"
                },
                "currency": ".a-price-symbol",
                "price": ".a-price-whole",
                "rating": ".a-icon-alt",
                "image": {
                    "selector": ".s-image",
                    "output": "@src"
                }
            }
        }
    })
    }


    response = requests.get("https://scraping.narf.ai/api/v1/", params=payload)

    # Parse the JSON response
    content = json.loads(response.content.decode('utf-8'))

    # Initialize the results string
    products_dict = []

    # Iterate over the products
    for product in content['products'][:10]:
        # Check if the keys 'asin', 'title', 'currency', 'price', and 'image' exist

        if 'asin' in product and 'price' in product and product['price'] and product['asin']:
            if product['rating']:
                rating = float(product['rating'].split(' ')[0])
            else:
                rating = 3.4
            image = product['image'].split('_')[0] + 'jpg'
            result = {
            "platform": "amazon",
            "country": country,
            "asin": product['asin'].split(':')[0].split('.')[-1],
            "name": product['name'],
            "images": [image],
            "currency": product.get('currency', "Pice on selection"),
            "price": float(product['price'].replace(',', '')),
            "rating": rating
        }
            products_dict.append(result)
    return products_dict

async def amazon_products_details(db: AsyncSession, productId: str, country: str):
   
    saved_product = await Product.find_by_asin(db,productId)

    if not saved_product.feature_bullets:       
        url = f'https://amazon.{country}/dp/{productId}?language=en'
        payload = {
        "api_key": API_KEY,
        "url": url,
        "extract_rules": json.dumps({
            
            "feature_bullet": {
                "type": "all",
                "selector": ".a-list-item.a-size-base.a-color-base",
                "output": "text"
            },
            "images":{
                "type": "all",
                "selector": ".imageThumbnail",
                "output": {
                    "link": {
                        "selector": "img",
                        "output": "@src"
                    }
            }}
                })
        }
        response = requests.get("https://scraping.narf.ai/api/v1/", params=payload)
        # Parse the JSON response
        product_details = json.loads(response.content.decode('utf-8'))
        images = []
        for image in product_details['images']:
            link = image['link'].split('_')[0] + 'jpg'
            images.append(link)
        feature_bullets = []
        for feature in product_details['feature_bullet']:
            feature_bullets.append(feature)
        new_params = {
            "platform": "amazon",
            "country": country,
            "asin": productId,
            "name": saved_product.name,
            "currency": saved_product.price_symbol,
            "price": saved_product.price,
            "rating": saved_product.rating,

            "feature_bullets": feature_bullets,
            "images": images
        }
        await Product.patch(
            db=db,
            asin=productId,
            feature_bullets=new_params['feature_bullets'],
            images= new_params['images']
        )
    else:
        new_params = {
            "platform": "amazon",
            "country": country,
            "asin": productId,
            "name": saved_product.name,
            "currency": saved_product.price_symbol,
            "price": saved_product.price,
            "rating": saved_product.rating,

            "feature_bullets": saved_product.feature_bullets,
            "images": saved_product.images
        }  
    return new_params



async def noon_search(
        country: str,
        keywords: List[str],
        search_index: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):
    localization= {
        "eg": "egypt-en",
        "ae": "uae-en",
        "sa": "saudi-en"
    }

    base_url = f'https://www.noon.com/{localization[country]}/search/'
    query_params = {'q': keywords}
    encoded_query = urllib.parse.urlencode(query_params)
    url = f'{base_url}?{encoded_query}'

    # Add price filters to the URL if provided
    if min_price is not None:
        url += f'&f%5Bprice%5D%5Bmin%5D={min_price}'
    if max_price is not None:
        url += f'&f%5Bprice%5D%5Bmax%5D={max_price}'

    payload = {
    "api_key": API_KEY,
    "url": url,
    "geo": "us",
    #"render_js": "true",
    "js_scenario": json.dumps({"steps": [ {"wait": 250}]}) 
    }

    response = requests.get("https://scraping.narf.ai/api/v1/", params=payload)

    # Parse the JSON response
    results = noon_parse_search(response.content.decode('utf-8'))

    products_dict = []
    for product in results:
        if len(product['images']) >0:
            images = product['images']
        else:
            images = ['https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Noon_Website_Logo.svg/260px-Noon_Website_Logo.svg.png']
        if product['rating']:
                rating = float(product['rating'].split(' ')[0])
        else:
                rating = 3.4
        result = {
            "platform": "noon",
            "country": country,
            "asin": product['asin'],
            "name": product['name'],
            "images": images,
            "currency": product.get('currency', "Price on selection"),
            "price": float(product.get('price', 0).replace(',', '')),
            "rating": rating
        }
        products_dict.append(result)

    return products_dict



async def noon_products_details(db: AsyncSession, productId: str, country: str):
   saved_product = await Product.find_by_asin(db,productId)
   new_params = {
    "platform": "noon",
    "country": country,
    "asin": productId,
    "name": saved_product.name,
    "currency": saved_product.price_symbol,
    "price": saved_product.price,
    "rating": saved_product.rating,

    "feature_bullets": saved_product.feature_bullets,
    "images": saved_product.images
   }
   return new_params
   