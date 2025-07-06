import os
import sys
from src.agent.affiliate_promoter import AliExpressAPIClient, EbayAPIClient
from dotenv import load_dotenv
import requests

load_dotenv()

# Μπορείς να αλλάξεις τα keywords εδώ ή να τα δώσεις ως arguments
KEYWORDS = sys.argv[1:] if len(sys.argv) > 1 else ["smartwatch", "laptop"]

print("\n=== Product Discovery Agent Demo ===\n")

aliexpress_client = AliExpressAPIClient()
ebays_client = EbayAPIClient()

for keyword in KEYWORDS:
    print(f"\n--- Results for: {keyword} ---\n")
    print("AliExpress:")
    products_ali = aliexpress_client.search_products(query=keyword, limit=3)
    if not products_ali:
        print("  No results from AliExpressAPIClient, trying direct API call...")
        # Fallback: direct API call as in test_aliexpress_search.py
        url = "https://aliexpress-data.p.rapidapi.com/product/search"
        querystring = {"query": keyword}
        headers = {
            "X-RapidAPI-Key": os.getenv("ALIEXPRESS_API_KEY"),
            "X-RapidAPI-Host": os.getenv("ALIEXPRESS_API_HOST"),
        }
        response = requests.get(url, headers=headers, params=querystring)
        print("Status:", response.status_code)
        try:
            data = response.json()
            if response.status_code == 200 and "result" in data:
                for item in data["result"][:3]:
                    print(f"- {item.get('title', '')} | {item.get('salePrice', {}).get('minPrice', '')} {item.get('salePrice', {}).get('currencyCode', '')} | {item.get('link', '')}")
                    print(f"  {item.get('description', '')}")
            else:
                print("  No results or API error.")
        except Exception as e:
            print("  Error parsing response:", e)
    else:
        for p in products_ali:
            print(f"- {p.title} | {p.price} {p.currency} | {p.affiliate_link or p.url}")
            print(f"  {p.description}")

    print("\neBay:")
    products_ebay = ebays_client.search_products(query=keyword, limit=3)
    if not products_ebay:
        print("  No results from EbayAPIClient, trying direct API call...")
        # Fallback: direct API call as in test_ebay.py
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        params = {"q": keyword, "limit": 3}
        headers = {
            "Authorization": f"Bearer {os.getenv('EBAY_USER_TOKEN')}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, params=params)
        print("Status:", response.status_code)
        try:
            data = response.json()
            if response.status_code == 200 and "itemSummaries" in data:
                for item in data["itemSummaries"]:
                    print(f"- {item.get('title', '')} | {item.get('price', {}).get('value', '')} {item.get('price', {}).get('currency', '')} | {item.get('itemWebUrl', '')}")
                    print(f"  {item.get('condition', '')}")
            elif response.status_code == 401:
                print("  Invalid or expired eBay token. Please get a new one from the eBay developer portal.")
                print("  Response:", data)
            else:
                print("  No results or API error.")
        except Exception as e:
            print("  Error parsing response:", e)
    else:
        for p in products_ebay:
            print(f"- {p.title} | {p.price} {p.currency} | {p.affiliate_link or p.url}")
            print(f"  {p.description}")

print("\nDemo complete!\n") 