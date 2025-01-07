import requests
import asyncio
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime

# Synchronous function to fetch the HTML content
def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5',
        
    }
    response = requests.get(url, headers=headers)
    return response.content

# Function to extract product details from a single product listing
def extract_product_info_from_search(product):
    title = product.h2.text.strip()

    # Get the product ASIN
    asin = product.get('data-asin', 'N/A')

    # Get the product price
    price_whole = product.find('span', {'class': 'a-price-whole'})
    price_fraction = product.find('span', {'class': 'a-price-fraction'})
    price_currency_symbol = product.find('span', {'class': 'a-price-symbol'})
    price_symbol = price_currency_symbol.text.strip() if price_currency_symbol else ""

    if price_whole:
        price_whole_text = price_whole.text.strip().replace(',', '')
        if price_fraction:
            price_fraction_text = price_fraction.text.strip()
            full_price_text = f"{price_whole_text}{price_fraction_text}"
        else:
            full_price_text = price_whole_text
        try:
            price = float(full_price_text)
        except ValueError:
            price = 0.0
    else:
        price = 0.0

    # Get the product rating
    try:
        rating_text = product.find('span', {'class': 'a-icon-alt'})
        rating = float(rating_text.text.replace(' out of 5 stars', ''))
    except:
        rating = 3.1

    # Get the product image
    image_tag = product.find('img', {'class': 's-image'})
    image_url = image_tag['src'] if image_tag else "No image available"

    return {
        'asin': asin,
        'name': title,
        'price_symbol': price_symbol,
        'price': price,
        'rating': rating,
        'image': image_url
    }

# Asynchronous function to scrape Amazon search results
async def scrape_amazon_search_results(
        country: str,
        keywords: List[str],
        search_index: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):
    keys = "+".join(keywords)
    url = f"https://www.amazon.{country}/s?language=en&k={keys}&i={search_index}"
    
    # Add price filters to the URL if provided
    if min_price is not None:
        url += f'&low-price={min_price}'
    if max_price is not None:
        url += f'&high-price={max_price}'

    # Call the synchronous function within the asynchronous context
    html = await asyncio.to_thread(get_html, url)
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all('div', {'data-component-type': 's-search-result'})

    product_dict = []
    # Extract details for each product and print them
    for product in products:
        product_info = extract_product_info_from_search(product)
        product_dict.append(product_info)
    return product_dict


# Function to extract product details from a single product listing
def extract_product_info_from_product(product):
    
    # Extract the product title
    title_tag = product.find('span', {'class': 'a-size-large product-title-word-break'})
    title = title_tag.text.strip() if title_tag else None

    # Get the product price
    price_whole = product.find('span', {'class': 'a-price-whole'})
    price_fraction = product.find('span', {'class': 'a-price-fraction'})
    price_currency_symbol = product.find('span', {'class': 'a-price-symbol'})
    price_symbol = price_currency_symbol.text.strip() if price_currency_symbol else ""

    if price_whole:
        price_whole_text = price_whole.text.strip().replace(',', '')
        if price_fraction:
            price_fraction_text = price_fraction.text.strip()
            full_price_text = f"{price_whole_text}{price_fraction_text}"
        else:
            full_price_text = price_whole_text
        try:
            price = float(full_price_text)
        except ValueError:
            price = 0.0
    else:
        price = 0.0

    # Get the product rating
    try:
        rating_text = product.find('span', {'class': 'a-icon-alt'})
        rating = float(rating_text.text.replace(' out of 5 stars', ''))
    except:
        rating = 3.1
    
    # Find all <li> elements that contain images
    image_list = product.find_all('span', {'class':'a-button-text'})
    
    # Extract all <img> tags within the <li> elements and get their 'src' attributes
    image_urls = [img_tag['src'].replace('._AC_US40_','._AC_UL500_') for li in image_list for img_tag in li.find_all('img')]

    return {
        'name': title,
        'price_symbol': price_symbol,
        'price': price,
        'rating': rating,
        'image_urls': image_urls[:-1]
    }

# Asynchronous function to scrape Amazon search results
async def scrape_amazon_product_page(
        country: str,
        asin: str
):

    product_url = f"https://www.amazon.{country}/dp/{asin}?language=en"
    # Call the synchronous function within the asynchronous context
    html = await asyncio.to_thread(get_html, product_url)
    product = BeautifulSoup(html, 'html.parser')

    product_info = extract_product_info_from_product(product)
    return product_info


