extract_rules = {
    "products": {
        "selector": ".productContainer",
        "fields": {
            "asin": {
                "selector": "a",
                "attribute": "id"  # Fetches the `id` attribute directly
            },
            "name": {
                "selector": ".sc-95ea18ef-25", #sc-26c8c6bb-24",
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
