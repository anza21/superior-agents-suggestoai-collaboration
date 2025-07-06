import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}
response = requests.get("https://huggingface.co/api/whoami-v2", headers=headers)
print("Status:", response.status_code)
print("Response:", response.json()) 