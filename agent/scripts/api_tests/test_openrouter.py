import os
import requests
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
response = requests.get("https://openrouter.ai/api/v1/auth/me", headers=headers)
print("Status:", response.status_code)
print("Response:", response.json()) 