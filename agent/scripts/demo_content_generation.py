import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Mock προϊόντα (μπορείς να τα αλλάξεις με πραγματικά από eBay)
products = [
    {
        "title": "MILITARY INDESTRUCTIBLE SMARTWATCH",
        "price": 42.99,
        "affiliate_link": "https://www.ebay.com/itm/355590497010?...&campid=5339114405",
        "description": "Military grade, waterproof, Bluetooth, heart rate monitor."
    },
    {
        "title": "DELL LATITUDE 5420 | INTEL CORE I5-1145G7 2.6GHZ | 512GB | 16GB RAM | NO OS",
        "price": 209.99,
        "affiliate_link": "https://www.ebay.com/itm/197459628129?...&campid=5339114405",
        "description": "Refurbished Dell laptop, 16GB RAM, 512GB SSD, no OS."
    }
]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-3.5-turbo")

# Prompt template
PROMPT = """
Write a professional, SEO-optimized blog post for the following product:

Title: {title}
Description: {description}
Price: {price} USD
Affiliate Link: {affiliate_link}

Include:
- A catchy introduction
- Key features and pros/cons
- A short Q&A (2 questions)
- A call to action with the affiliate link
- Affiliate disclosure: 'This post contains affiliate links.'
"""

def generate_content(product):
    prompt = PROMPT.format(**product)
    if not OPENROUTER_API_KEY:
        print("[MOCK] No OpenRouter API key found. Returning mock content.")
        return f"[MOCK BLOG POST]\nProduct: {product['title']}\nDescription: {product['description']}\nAffiliate Link: {product['affiliate_link']}\nAffiliate disclosure: This post contains affiliate links."
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional affiliate content writer."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print("[OpenRouter] API error:", response.status_code, response.text)
            return f"[ERROR] OpenRouter API error: {response.status_code}"
    except Exception as e:
        print("[OpenRouter] Exception:", e)
        return f"[ERROR] Exception: {e}"

print("\n=== Content Generation Agent Demo ===\n")
for product in products:
    print(f"\n--- Content for: {product['title']} ---\n")
    content = generate_content(product)
    print(content)

print("\nDemo complete!\n") 