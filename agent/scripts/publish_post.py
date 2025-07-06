import os
import subprocess
from datetime import datetime

SITE_DIR = "/home/anza/suggestoai-site"
AGGREGATOR = os.path.join(SITE_DIR, "ai-recommends.html")
POSTS_DIR = SITE_DIR  # Τα posts μπαίνουν στο root, μπορείς να το αλλάξεις αν θες

def generate_html_post(title, desc, img, afflink, review, pros=None, cons=None, qas=None, seller_trust=None, shipping_info=None, price=None, currency="USD"):
    meta_tags = f'''
    <title>{title} | SuggestoAI</title>
    <meta name="description" content="{desc}">
    <meta name="keywords" content="{title}, review, affiliate, SuggestoAI, product, comparison, AI">
    <meta property="og:title" content="{title} | SuggestoAI">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="{img}">
    <link rel="canonical" href="{afflink}">
    '''
    disclosure = '<div class="disclosure"><strong>Affiliate Disclosure:</strong> This post contains affiliate links. We may earn a commission if you buy through our links. All recommendations are AI-generated and unbiased.</div>'
    pros_html = f'<h3>Pros</h3><ul>' + ''.join(f'<li>{p}</li>' for p in (pros or [])) + '</ul>' if pros else ''
    cons_html = f'<h3>Cons</h3><ul>' + ''.join(f'<li>{c}</li>' for c in (cons or [])) + '</ul>' if cons else ''
    qas_html = ''
    if qas:
        qas_html = '<h3>Q&A</h3><ul>' + ''.join(f'<li><strong>Q:</strong> {qa[0]}<br><strong>A:</strong> {qa[1]}</li>' for qa in qas) + '</ul>'
    seller_html = f'<p><strong>Seller trust:</strong> {seller_trust}</p>' if seller_trust else ''
    shipping_html = f'<p><strong>Shipping info:</strong> {shipping_info}</p>' if shipping_info else ''
    # Structured data (schema.org Product/Review)
    structured_data = f'''
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "{title}",
      "image": "{img}",
      "description": "{desc}",
      "offers": {{
        "@type": "Offer",
        "url": "{afflink}",
        "price": "{price or ''}",
        "priceCurrency": "{currency}",
        "availability": "https://schema.org/InStock"
      }},
      "review": {{
        "@type": "Review",
        "reviewBody": "{review}",
        "author": {{"@type": "Person", "name": "SuggestoAI Agent"}}
      }}
    }}
    </script>
    '''
    html = f'''
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {meta_tags}
    {structured_data}
    <link rel="stylesheet" href="/style.css">
    <style>
    body {{ font-family: Arial, sans-serif; max-width: 700px; margin: auto; padding: 1em; }}
    img {{ max-width: 100%; height: auto; }}
    .disclosure {{ background: #f9f9f9; border-left: 4px solid #007bff; padding: 0.5em 1em; margin: 1em 0; font-size: 0.95em; }}
    h1 {{ font-size: 2em; margin-bottom: 0.5em; }}
    h3 {{ margin-top: 1.5em; }}
    .review {{ background: #f4f4f4; padding: 1em; border-radius: 6px; margin-top: 1.5em; }}
    @media (max-width: 600px) {{ body {{ padding: 0.5em; }} h1 {{ font-size: 1.3em; }} }}
    </style>
    </head>
    <body>
    <h1>{title}</h1>
    <img src="{img}" alt="{title}">
    <p>{desc}</p>
    {disclosure}
    <p><a href="{afflink}" target="_blank" rel="nofollow sponsored">Buy here: {afflink}</a></p>
    {pros_html}
    {cons_html}
    {qas_html}
    {seller_html}
    {shipping_html}
    <div class="review">{review}</div>
    </body>
    </html>
    '''
    return html 

def add_entry_to_aggregator(title, desc, img, post_filename):
    with open(AGGREGATOR, "r", encoding="utf-8") as f:
        html = f.read()
    # Εντοπίζουμε το EN section
    insert_point = html.find('<div class="features"')
    if insert_point == -1:
        print("❌ Δεν βρέθηκε το .features section στο aggregator!")
        return
    # Βρίσκουμε το σημείο μετά το πρώτο > του div
    start = html.find('>', insert_point) + 1
    # Δημιουργούμε το νέο entry
    entry = f'''\n        <div class="feature" style="max-width:320px;">
          <img src="{img}" alt="{title}">
          <h3>{title}</h3>
          <p>{desc}</p>
          <a href="{post_filename}" class="cta-btn" style="font-size:1rem;">Read More</a>
          <div class="social-btns">
            <a class="social-btn" href="https://twitter.com/intent/tweet?text=Check+out+this+AI+product+pick:+{title.replace(' ','+')}+by+SuggestoAI&url=https://suggestoai.com/{post_filename}" target="_blank" title="Share on Twitter">&#128081;</a>
            <a class="social-btn" href="https://www.facebook.com/sharer/sharer.php?u=https://suggestoai.com/{post_filename}" target="_blank" title="Share on Facebook">&#128100;</a>
            <a class="social-btn" href="https://www.linkedin.com/shareArticle?mini=true&url=https://suggestoai.com/{post_filename}" target="_blank" title="Share on LinkedIn">&#128188;</a>
          </div>
        </div>\n'''
    # Εισάγουμε το entry αμέσως μετά το άνοιγμα του div.features
    new_html = html[:start] + entry + html[start:]
    with open(AGGREGATOR, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"✅ Προστέθηκε νέο entry aggregator για {title}")

def save_html_post(html, filename):
    path = os.path.join(POSTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Αποθηκεύτηκε το νέο post: {path}")

def git_publish():
    try:
        subprocess.run(["git", "add", "."], cwd=SITE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Add new AI product post"], cwd=SITE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_DIR, check=True)
        print("✅ Το νέο post ανέβηκε στο site!")
    except subprocess.CalledProcessError as e:
        print("❌ Κάτι πήγε στραβά με το git push:", e)

# Παράδειγμα χρήσης (θα το αντικαταστήσεις με integration στον agent)
if __name__ == "__main__":
    # Dummy data για demo
    title = "AI Product Demo"
    desc = "This is a demo AI-generated product recommendation."
    img = "https://source.unsplash.com/320x180/?demo,tech"
    afflink = "https://affiliate.example.com/demo"
    review = "<p>This is a detailed review of the demo product.</p>"
    post_filename = f"ai-product-demo-{datetime.now().strftime('%Y%m%d')}.html"
    html = generate_html_post(title, desc, img, afflink, review)
    save_html_post(html, post_filename)
    add_entry_to_aggregator(title, desc, img, post_filename)
    git_publish() 