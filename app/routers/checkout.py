# app/routers/cart.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, List

from app.models import Checkout
from app.core.database import DBSessionDep
from app.core.exceptions import NotFoundException

from app.utils.authUtils import authenticateToken


router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"],
    responses={404: {"description": "Not found"}},
)
@router.post("/cart", response_model=dict)
async def cart_link(
    token: str,
    products: List[dict],
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    
    user_id = user.id
    country = user.country
    platform = products[0]['platform']
    if platform == 'amazon':
        productIds = [product['asin'] for product in products]
        await Checkout.create(db, user_id, platform, country, 'cart', products )

        link_url = f"https://www.amazon.{country}/gp/aws/cart/add.html?language=en&AssociateTag=arobah-21"

        # Use enumerate to get both index and productId
        for i, productId in enumerate(productIds):
            link_url += f"&ASIN.{i+1}={productId}&Quantity.{i+1}=1"
    if platform == 'noon':
        localization= {
        "eg": "egypt-en",
        "ae": "uae-en",
        "sa": "saudi-en"
    }
        await Checkout.create(db, user_id, platform, country, 'cart', products )

        link_url = f"https://www.noon.com/{localization[country]}/{products[0]['asin']}/p/"

    return {'link_url': link_url}


@router.post("/product", response_model=dict)
async def product_link(
    token: str,
    product: dict,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id
    
    country = user.country

    await Checkout.create(db, user_id, product['platform'], country, 'product', [product] )

    if product['platform'] == 'amazon':
        link_url = f"https://www.amazon.{country}/dp/{product['asin']}?language=en&tag=arobah-21"
    elif product['platform'] == 'noon':
        localization= {
        "eg": "egypt-en",
        "ae": "uae-en",
        "sa": "saudi-en"
    }
        link_url = f"https://www.noon.com/{localization[country]}/{product['asin']}/p/"

    return {'link_url': link_url}



@router.get("/history", response_model=dict)
async def checkout_history(
    token: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")
    user_id = user.id

    history = await Checkout.find_by_user_id(db, user_id)
    history_dict= {}
    if history:
        for order in history:
            history_dict[f"{order.platform}.{order.country} - {order.created_at.strftime('%Y-%m-%d - %H:%M:%S')}"] = []
            for product in order.products:
                product_dict = {
                    'name': product['name'],
                    'image': product['images'][0],
                    'currency': product['currency'],
                    'price': product['price']
                }
                history_dict[f"{order.platform}.{order.country} - {order.created_at.strftime('%Y-%m-%d - %H:%M:%S')}"].append(product_dict)
             
    return history_dict
