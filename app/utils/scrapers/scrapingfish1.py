from scrapingfish import noon_search
import asyncio

reply = asyncio.run(noon_search(
    country="ae",
    keywords=["keyboard", "wireless", "Mechancial"],
    search_index="default"
))

print(reply)
   
