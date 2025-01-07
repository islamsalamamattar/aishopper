available_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Returns a list of product details from an online marketplace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Search keywords"
                    },
                    "search_index": {
                        "type": "string",
                        "description": "The category to search within"
                    },
                    "min_price": {
                        "type": "integer",
                        "description": "Minimum price filter in EGP (optional)"
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "Maximum price filter in EGP (optional)"
                    }
                },
                "required": ["keywords", "search_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "display_products",
            "description": "Displays 3-10 products as cards with image, name and rice in the chat, based on a list of productIds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "productIds": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": "List of productIds (asin) for the products to be displayed",
                    }
                },
                "required": ["productIds"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Fetches detailed information and images for a specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "productId": {
                        "type": "string",
                        "description": "The ID (asin) of the product to fetch details for",
                    }
                },
                "required": ["productId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "display_product_images",
            "description": "Displays images for a specific product to the user in the chat",
            "parameters": {
                "type": "object",
                "properties": {
                    "productId": {
                        "type": "string",
                        "description": "The ID (asin) of the product to fetch details for",
                    }
                },
                "required": ["productId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Adds products to the user's cart based on a list of productIds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "productId": {
                        "type": "string",
                        "description": "ProductId (asin) for the product to be added to the cart",
                    }
                },
                "required": ["productId"],
            },
        },
    }
]