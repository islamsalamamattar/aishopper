import json
from bs4 import BeautifulSoup
from app.utils.scrapers.extraction_rules import extract_rules

'''
extract_rules = {
    "products": {
        "selector": ".productContainer",
        "fields": {
            "asin": {
                "selector": "a",
                "attribute": "id"  # Fetches the `id` attribute directly
            },
            "name": {
                "selector": ".sc-66eca60f-24",
                "attribute": "title"  # Fetches the `title` attribute directly
            },
            "currency": {
                "selector": ".currency",  # Directly selecting the currency
                "attribute": "text"  # Retrieves text content
            },
            "price": {
                "selector": ".amount",  # Directly selecting the price
                "attribute": "text"  # Retrieves text content
            },
            "rating": {
                "selector": ".sc-9cb63f72-2",  # Directly selecting the rating
                "attribute": "text"  # Retrieves text content
            },
            "images": {
                "selector": "img",  # Selects all img elements with the specified class
                "attribute": "src"  # Retrieves `src` attribute of each img
            }
        }
    }
}
'''

def noon_parse_search(data: str):
    soup = BeautifulSoup(data, 'html.parser')

    # Find all product containers
    product_containers = soup.select(extract_rules["products"]["selector"])
    print(product_containers)

    # Initialize the list to store extracted data
    extracted_data = []

    # Iterate over each product container until we have 8 valid products
    for container in product_containers:

        # Check for sponsored tag
        sponsored_tag = container.select_one('.sc-66eca60f-23.AkmCS')

        if sponsored_tag is None:
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
            
            # Process the ASIN if available
            if data['asin']:
                data['asin'] = data['asin'].split('-')[1] if '-' in data['asin'] else data['asin']
            
            # Collect all image URLs inside the productContainer
            image_tags = container.find_all('img')
            images = []
            for img in image_tags:
                if 'src' in img.attrs:
                    src = img['src']
                    # Filter for .jpg images and avoid .png or .svg images
                    if not src.lower().endswith('.png') and not src.lower().endswith('.svg'):
                        # Remove URL parameters
                        parsed_url = src.split('?')[0]
                        proxy_image_url = "https://api.arobah.com/image/" + parsed_url
                        images.append(proxy_image_url)
            
            # Remove duplicates and sort images
            data['images'] = sorted(list(set(images)))

            # Append data to the list
            extracted_data.append(data)

            # Break the loop if we have enough products
            if len(extracted_data) >= 8:
                break

    # Output the results as JSON
    return extracted_data
