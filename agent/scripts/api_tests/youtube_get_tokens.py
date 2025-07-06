import os
import requests
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI")
SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"

# 1. Get authorization code
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent"
}
auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
print("Open this URL in your browser and authorize the app:")
print(auth_url)
webbrowser.open(auth_url)
code = input("Paste the 'code' parameter from the redirected URL here: ").strip()

# 2. Exchange code for tokens
TOKEN_URL = "https://oauth2.googleapis.com/token"
data = {
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
}
response = requests.post(TOKEN_URL, data=data)
if response.status_code == 200:
    tokens = response.json()
    print("\nSUCCESS! Add these to your .env:")
    print(f"YOUTUBE_ACCESS_TOKEN={tokens['access_token']}")
    print(f"YOUTUBE_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
else:
    print("Error exchanging code for tokens:", response.text) 