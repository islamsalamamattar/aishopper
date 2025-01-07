from dotenv import load_dotenv
import os
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import requests
import json
from app.models import Product, Profile
from app.utils.amazon_localization import localization


async def create_and_format_top_n(db: AsyncSession, products: List, country: str, n: int = 10):
    _response = json.loads(products) # for scraperapi

    results = []
    for product in _response['results'][:n]:
        images = []
        images.append(product.get("image", "image not avialable"))
        result = {
            "country": country,
            "asin": product['asin'],
            "name": product['name'],
            "images": images,
            "price_symbol": product.get("price_symbol", "$"),
            "price": product.get("price", 0),
            "rating": product.get("stars", 2.5)
        }

        saved_product = await Product.find_by_asin(db, product["asin"])
        if not saved_product:
            new_product = await Product.create(db=db, **result)
            product_dict = {
                "asin": new_product.asin,
                "name": new_product.name,
                "currency": new_product.price_symbol,
                "price": new_product.price,
                "rating": new_product.rating
            }
            results.append(product_dict)
        else:
            product_dict = {
                "asin": saved_product.asin,
                "name": saved_product.name,
                "currency": saved_product.price_symbol,
                "price": saved_product.price,
                "rating": saved_product.rating
            }
            results.append(product_dict)
    return results


async def create_and_format_top_amazon(db: AsyncSession, products: List, country: str):
    results = []
    for product in products[:8]:
        result = {
            "country": country,
            "asin": product['asin'],
            "name": product['name'],
            "image": product['image'],
            "price_symbol": product.get("price_symbol", "$"),
            "price": product.get("price", 0),
            "rating": product.get("rating", 3.2)
        }

        saved_product = await Product.find_by_asin(db, product["asin"])
        if not saved_product:
            new_product = await Product.create(db=db, **result)
            product_dict = {
                "asin": new_product.asin,
                "name": new_product.name,
                "currency": new_product.price_symbol,
                "price": new_product.price,
                "rating": new_product.rating
            }
            results.append(product_dict)
        else:
            product_dict = {
                "asin": saved_product.asin,
                "name": saved_product.name,
                "currency": saved_product.price_symbol,
                "price": saved_product.price,
                "rating": saved_product.rating
            }
            results.append(product_dict)
    return results

async def create_products(db: AsyncSession, products: List):
    for product in products:

        result = {
            "platform": product['platform'],
            "country": product['country'],
            "asin": product['asin'],
            "name": product['name'] or "Generic",
            "images": product['images'],
            "price_symbol": product['currency'],
            "price": product['price'],
            "rating": product['rating']
        }
        saved_product = await Product.find_by_asin(db, product["asin"])
        if not saved_product:
            await Product.create(db=db, **result)
        else:
            await Product.patch(db=db, **result)

async def display_products(db: AsyncSession, productIds: List):
    products = []
    for asin in productIds:
        product = await Product.find_by_asin(db, asin)
        product_dict = {
            'platform': product.platform,
            'country': product.country,
            'asin': product.asin,
            'name': product.name,
            'currency': product.price_symbol,
            'price': product.price,
            'images': product.images,
            'rating': product.rating
        }
        products.append(product_dict)
    return products

async def get_product_images(db: AsyncSession, productId: str):
    product = await Product.find_by_asin(db, productId)
    return product.images
    
async def add_to_cart(
        db: AsyncSession,
        user_id: str,
        productId: str
):
    product = await Product.find_by_asin(db, productId)
    new_product = {
        'platform': product.platform,
        'country': product.country,
        'asin': product.asin,
        'images': product.images,
        'name': product.name[:25],
        'price_symbol': product.price_symbol,
        'price': product.price
    }
    profile = await Profile.find_by_user_id(db, user_id)
    if profile is None:
        raise ValueError("Profile not found")

    # Update the profile's cart
    await Profile.add_to_cart(db=db, user_id=user_id, new_product=new_product)
    response = {"message": f"**{new_product['name']}** added to cart successfully"}
    return response
