import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = "https://aliexpress-data.p.rapidapi.com/product/search"
querystring = {"query": "smartwatch"}
headers = {
    "X-RapidAPI-Key": os.getenv("ALIEXPRESS_API_KEY"),
    "X-RapidAPI-Host": os.getenv("ALIEXPRESS_API_HOST"),
}
response = requests.get(url, headers=headers, params=querystring)
print("Status:", response.status_code)
print("Response:", response.json()) 