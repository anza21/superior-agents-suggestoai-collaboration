import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
headers = {
    "Authorization": f"Bearer {os.getenv('EBAY_USER_TOKEN')}",
    "Content-Type": "application/json"
}
params = {"q": "laptop", "limit": 3}
response = requests.get(url, headers=headers, params=params)
print("Status:", response.status_code)
try:
    print("Response:", response.json())
except Exception as e:
    print("Error parsing response:", e)
    print("Raw response:", response.text) 