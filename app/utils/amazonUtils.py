from typing import List


async def search_items(keywords: List, search_index: str):
    response = {
        "items": [
            {
                "itemId": "abc123",
                "itemTitle": "15.6\" Windows 11 Laptop, Intel Core i3-5005U, 16GB RAM, 512GB SSD, FHD IPS Display, 2.4G/5G WiFi, BT5.0, RJ45, Type C, Webcam, Long Battery Life - for Work, Study, and Entertainment",
                "currency": "EGP",
                "price": 14352
            },
            {
                "itemId": "abss34",
                "itemTitle": "Lenovo IdeaPad 1 Laptop, 15.6” FHD Display, AMD Ryzen 5 5500U, 8GB RAM, 512GB SSD, Windows 11 Home, 720p Camera w/Privacy Shutter, Smart Noise Cancelling, Cloud Grey",
                "currency": "EGP",
                "price": 14572.32
            },
            {
                "itemId": "kjhf55",
                "itemTitle": "HP Newest 14\" Ultral Light Laptop for Students and Business, Intel Quad-Core N4120, 8GB RAM, 192GB Storage(64GB eMMC+128GB Micro SD), 1 Year Office 365, Webcam, HDMI, WiFi, USB-A&C, Win 11 S",
                "currency": "EGP",
                "price": 11879.52
            },
            {
                "itemId": "lkjhd44",
                "itemTitle": "Dell Inspiron 15 3000 3520 Business Laptop Computer[Windows 11 Pro], 15.6'' FHD Touchscreen, 11th Gen Intel Quad-Core i5-1135G7, 16GB RAM, 1TB PCIe SSD, Numeric Keypad, Wi-Fi, Webcam, HDMI, Black",
                "currency": "EGP",
                "price": 24191.52
            },
            {
                "itemId": "lkjh44",
                "itemTitle": "Lenovo IdeaPad 1 14 Laptop, 14.0\" HD Display, Intel Celeron N4020, 4GB RAM, 64GB Storage, Intel UHD Graphics 600, Win 11 in S Mode, Cloud Grey",
                "currency": "EGP",
                "price": 7631.05
            },
            {
                "itemId": "llano-cooling-pad",
                "itemTitle": "Llano RGB Laptop Cooling Pad with Powerful Turbofan, Gaming Laptop Cooler with Infinitely Variable Speed, Touch Control, LCD Screen, Seal Foam for Rapid Cooling Laptop 15-19in",
                "currency": "EGP",
                "price": 5759.52
            },
            {
                "itemId": "acer-aspire-3",
                "itemTitle": "Acer Aspire 3 A315-58-74KE Slim Laptop | 15.6\" Full HD Display | Intel Core i7-1165G7 Processor | Intel Iris Xe Graphics | 8GB DDR4 | 512GB PCIe Gen4 SSD | Wi-Fi 6 | Windows 11 Home | Pure Silver",
                "currency": "EGP",
                "price": 23999.52
            },
            {
                "itemId": "samsung-galaxy-book3",
                "itemTitle": "SAMSUNG 15.6\" Galaxy Book3 Business Laptop Computer/Windows 11 PRO/16GB - 512GB/ 13th Gen Intel® Core™ i7 processor, 2023 Model, NP754XFG-KB1US, Silver",
                "currency": "EGP",
                "price": 31353.12
            }
        ]
    }

    return response

async def show_items(
        itemIds: List[str]
):
    response = {"show_items": itemIds, "status": "Items displayed successfully"}
    return response


async def add_to_cart(
        itemIds: List[str]
):
    response = {"message": "Items to cart successfully"}
    return response

