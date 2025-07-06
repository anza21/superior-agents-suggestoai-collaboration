import os
import requests
from dotenv import load_dotenv

load_dotenv()
DEVTO_API_KEY = os.getenv("DEVTO_API_KEY")
headers = {"api-key": DEVTO_API_KEY}
response = requests.get("https://dev.to/api/articles/me", headers=headers)
print("Status:", response.status_code)
print("Response:", response.json()) 