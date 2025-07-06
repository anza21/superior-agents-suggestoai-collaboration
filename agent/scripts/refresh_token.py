import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("EBAY_CLIENT_ID")
client_secret = os.getenv("EBAY_CLIENT_SECRET")
refresh_token = os.getenv("EBAY_REFRESH_TOKEN")

auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
url = "https://api.ebay.com/identity/v1/oauth2/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {auth}"
}
data = {
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
    "scope": "https://api.ebay.com/oauth/api_scope"
}

response = requests.post(url, headers=headers, data=data)
print("Status:", response.status_code)
try:
    data = response.json()
    if response.status_code == 200 and "access_token" in data:
        print("\nYour new eBay access token is:\n")
        print(data["access_token"])
        print("\nExpires in:", data.get("expires_in", "?"), "seconds")
    else:
        print("Error:", data)
except Exception as e:
    print("Error parsing response:", e) 