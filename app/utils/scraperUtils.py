from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import requests
import json
from app.models import Product
from app.utils.amazon_localization import localization


# Load environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("SCRAPERAPI_API_KEY")


async def search_products(
        country: str,
        keywords: List[str],
        search_index: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):
    query = "+".join(keywords)

    domain = localization[country]["url"]

    url = f'{domain}/s?language=en&k={query}&i={search_index}'

    # Add price filters to the URL if provided
    if min_price is not None:
        url += f'&low-price={min_price}'
    if max_price is not None:
        url += f'&high-price={max_price}'

    params = {
        'api_key': API_KEY,
        'url': url,
        'country_code': 'us',
        'tld': country,
        'autoparse': 'true',
        'device_type': 'desktop'
    }

    r = requests.get('https://api.scraperapi.com/', params=params)

    results = r.text
    return results


async def extract_top_n(db: AsyncSession, products: List, country: str, n: int = 10):
    _response = json.loads(products)
    results = []
    for product in _response["results"][:n]:
        result = {
            "country": country,
            "asin": product.get("asin", "NOT AVAILABLE"),
            "name": product.get("name", "NOT AVAILABLE"),
            "images": [product.get("image", "image not avialable")],
            "price_symbol": product.get("price_symbol", "$"),
            "price": product.get("price", 0)
        }

        saved_product = await Product.find_by_asin(db, product["asin"])
        if not saved_product:
            new_product = await Product.create(db=db, **result)
            product_dict = {
                "asin": new_product.asin,
                "name": new_product.name,
                "currency": new_product.price_symbol,
                "price": new_product.price
            }
            results.append(product_dict)
        else:
            product_dict = {
                "asin": saved_product.asin,
                "name": saved_product.name,
                "currency": saved_product.price_symbol,
                "price": saved_product.price
            }
            results.append(product_dict)
    return results


async def display_products(db: AsyncSession, productIds: List):
    products = []
    for asin in productIds:
        product = await Product.find_by_asin(db, asin)
        product_dict = {
            "asin": product.asin,
            "name": product.name,
            "currency": product.price_symbol,
            "price": product.price,
            "image": product.images[0]
        }
        products.append(product_dict)
    return products


async def get_products_details(db: AsyncSession, productId: str, country: str):
    domain = localization[country]["url"]
    url = f'{domain}/dp/{productId}?language=en'

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
    images = product_details["images"]
    new_params = {
        "images": images,
        "product_category": str(product_details.get("product_category", "not defined")),
        "product_information": str(product_details["product_information"]),
        "feature_bullets": str(product_details.get("feature_bullets", None)),
        "customization_options": str(product_details.get("customization_options", None)),
        "brand": str(product_details.get("brand", "Generic")),
        "average_rating": str(product_details.get("average_rating", "not rated"))
    }

    new_product = await Product.patch(
        db=db,
        asin=productId,
        **new_params
    )
    summary = {k: v for k, v in new_params.items() if k != 'images'}

    return summary

async def get_product_images(db: AsyncSession, productId: str):
    product = await Product.find_by_asin(db, productId)
    return product.images
    

async def add_to_cart(
        productId: str
):
    response = {"message": "products to cart successfully"}
    return response
