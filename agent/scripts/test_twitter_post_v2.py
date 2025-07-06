import os
import requests
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWEET_TEXT = "Test tweet from Superior Agent (v2 API)!"

if not BEARER_TOKEN:
    print("[ERROR] Λείπει το TWITTER_BEARER_TOKEN από το .env!")
    exit(1)

url = "https://api.twitter.com/2/tweets"
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}
data = {
    "text": TWEET_TEXT
}

response = requests.post(url, headers=headers, json=data)
print(f"Status code: {response.status_code}")
print(response.text) 