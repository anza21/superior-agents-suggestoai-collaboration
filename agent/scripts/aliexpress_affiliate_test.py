import time
import hmac
import hashlib
import requests

PID = "suggestoai-agent"  # To PID sou

def make_signature(params, app_secret):
    sorted_items = sorted(params.items())
    concat = ''.join(f"{k}{v}" for k, v in sorted_items)
    signature = hmac.new(app_secret.encode('utf-8'), concat.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    return signature

app_key = "516276"
app_secret = "f0a77YkuSv2rtILV1SLDqQznqvMV7oGo"
timestamp = str(int(time.time() * 1000))
params = {
    "app_key": app_key,
    "timestamp": timestamp,
    "sign_method": "sha256",
    "method": "aliexpress.affiliate.product.query",
    "keywords": "smartwatch",
    "page_no": "1",
    "page_size": "3",
    "fields": "productId,productTitle,productUrl,productImage,originalPrice,salePrice,promotion_link,product_detail_url",
    "tracking_id": PID
}
sign = make_signature(params, app_secret)
params["sign"] = sign

url = "https://api-sg.aliexpress.com/sync"
response = requests.get(url, params=params)
print(response.status_code)
data = response.json()
products = data.get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
for i, item in enumerate(products):
    print(f"\n--- Product {i+1} ---")
    print("Title:", item.get("product_title"))
    affiliate_link = item.get("promotion_link") or item.get("product_detail_url", "")
    # Ensure tracking_id is in the link
    if affiliate_link and PID and "tracking_id" not in affiliate_link:
        if "?" in affiliate_link:
            affiliate_link += f"&tracking_id={PID}"
        else:
            affiliate_link += f"?tracking_id={PID}"
    print("Affiliate Link:", affiliate_link)
    if PID in affiliate_link:
        print("✅ tracking_id FOUND in affiliate link!")
    else:
        print("❌ tracking_id NOT FOUND in affiliate link!") 