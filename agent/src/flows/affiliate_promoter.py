from typing import Callable, List
from datetime import datetime
import time
import requests
import os
import re
import json
from PIL import Image
from io import BytesIO
import subprocess

from loguru import logger
from result import UnwrapError
from src.agent.affiliate_promoter import AffiliatePromoterAgent, AliExpressAPIClient, EbayAPIClient, DevtoAPIClient, HashnodeAPIClient, BloggerAPIClient, LinkedInAPIClient, YouTubeAPIClient
from src.datatypes import StrategyData, StrategyInsertData
from src.datatypes.affiliate_promoter import ProductData, ContentData, VideoContentData, PublishingResult
from src.sensor.affiliate_promoter import AffiliatePromoterTwitterClient
from scripts.replicate_image_generation import generate_image
from scripts.replicate_video_generation import generate_video
from scripts.publish_to_site import git_publish

SITE_PUBLISH_SCRIPT = "/home/anza/suggestoai-site/publish_post.py"

def unassisted_flow(
	agent: AffiliatePromoterAgent,
	session_id: str,
	role: str,
	time: str,
	apis: List[str],
	metric_name: str,
	prev_strat: StrategyData | None,
	notif_str: str | None,
	summarizer: Callable[[List[str]], str],
):
	"""
	Execute an autonomous affiliate promotion workflow with the affiliate promoter agent.

	Steps:
	1. Discover affiliate products via APIs (Amazon, AliExpress, eBay).
	2. Generate content (SEO blog posts, comparison tables, Q&A summaries) using LLMs and RAG.
	3. Generate video content (YouTube scripts, TTS narration, MoviePy/ffmpeg video creation).
	4. Publish content to multiple platforms (Blogger, Medium, Dev.to, Hashnode, X/Twitter, LinkedIn).
	5. Integrate value-oriented features (guarantees, return policies, seller trust).
	6. Run autonomously in a loop or via cron.
	The agent's success metric is affiliate sales, clicks on affiliate links, or views/interactions with published content.
	"""
	agent.reset()
	logger.info("Reset agent")
	logger.info("Starting autonomous affiliate promotion workflow")

	twitter_client = AffiliatePromoterTwitterClient()
	aliexpress_client = AliExpressAPIClient()
	ebay_client = EbayAPIClient()
	devto_client = DevtoAPIClient()
	hashnode_client = HashnodeAPIClient()
	blogger_client = BloggerAPIClient()
	linkedin_client = LinkedInAPIClient()
	youtube_client = YouTubeAPIClient()
	ebay_products = []
	aliexpress_products = []
	if ebay_client.can_request():
		logger.info("[eBay] Using real API for product discovery...")
		ebay_products = ebay_client.search_products(query="laptop", limit=3)
	if aliexpress_client.can_request():
		logger.info("[AliExpress] Using real API for product discovery...")
		aliexpress_products = aliexpress_client.search_products(query="smartwatch", limit=3)
	discovered_products = ebay_products + aliexpress_products
	logger.info(f"Discovered products: {[f'{p.title} ({p.source})' for p in discovered_products]}")

	# After discovery, ensure at least one AliExpress product is present for demo
	if not any(p.source == "aliexpress" for p in discovered_products):
		demo_ali = aliexpress_client.search_products(query="smartwatch", limit=1)
		if demo_ali:
			logger.info("[AliExpress] Forcing inclusion of one AliExpress product for demo.")
			discovered_products.append(demo_ali[0])

	# Autonomous content type selection per product
	content_plan = []
	for product in discovered_products:
		plan = {"product": product, "types": []}
		# Example logic: if product is from eBay, prefer blog+video; if AliExpress, prefer image+video
		if product.source == "ebay":
			plan["types"] = ["blog", "video"]
		elif product.source == "aliexpress":
			plan["types"] = ["image", "video"]
		else:
			plan["types"] = ["blog"]
		logger.info(f"[Decision] For '{product.title}' ({product.source}), will generate: {plan['types']}")
		content_plan.append(plan)

	# Generate content according to plan
	logger.info("Step 2: Generating content using LLMs and RAG...")
	generated_content = []
	generated_videos = []
	for plan in content_plan:
		product = plan["product"]
		if "blog" in plan["types"]:
			generated_content += generate_content_for_products_with_ai([product])
		if "image" in plan["types"]:
			# Generate image (Replicate or other real API)
			img_path = generate_image(product.title + ", product photo, high detail")
			logger.info(f"[Image] Generated for '{product.title}': {img_path}")
		if "video" in plan["types"]:
			generated_videos += generate_video_for_products_with_ai([product])
	logger.info(f"Generated content types: {[c.type for c in generated_content]}")
	logger.info(f"Generated videos: {[v.title for v in generated_videos]}")

	# 4. Publish content to multiple platforms
	logger.info("Step 4: Publishing content to multiple platforms (Blogger, Medium, Dev.to, Hashnode, X/Twitter, LinkedIn)...")
	published_links = mock_publish_content(generated_content, generated_videos)
	logger.info(f"Published links: {[r.url for r in published_links]}")

	# Twitter posting για κάθε generated blog (always in English)
	FACEBOOK_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
	FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
	for content in generated_content:
		if content.type == "blog":
			eng_title = only_english(content.title)
			eng_summary = only_english(content.summary)
			eng_body = only_english(content.body)
			# Φιλτράρω/μεταφράζω όλα τα value features
			pros = [only_english(p) for p in getattr(content, 'pros', [])]
			cons = [only_english(c) for c in getattr(content, 'cons', [])]
			qas = [(only_english(qa[0]), only_english(qa[1])) for qa in getattr(content, 'qas', [])] if hasattr(content, 'qas') else []
			seller_trust = only_english(getattr(content, 'seller_trust', ''))
			shipping_info = only_english(getattr(content, 'shipping_info', ''))
			aff_link = get_affiliate_link(content)
			post_text = f"{eng_title}\n{eng_summary[:200]}...\nBuy here: {aff_link}"
			# Twitter
			try:
				twitter_client.create_tweet(post_text)
			except Exception as e:
				print(f"[MOCK] Twitter error: {e}")
				save_mock_post("twitter", eng_title, post_text)
			# Dev.to publishing
			tags = [only_english(tag) for tag in (content.tags if content.tags else ["affiliate", "review", "aigenerated"])]
			if "ai-generated" in tags:
				tags = [t if t != "ai-generated" else "aigenerated" for t in tags]
			try:
				devto_client.publish_article(
					title=eng_title,
					body_markdown=f"{eng_body}\n\nBuy here: {aff_link}",
					tags=tags,
					canonical_url=aff_link,
					published=True
				)
			except Exception as e:
				print(f"[MOCK] Dev.to error: {e}")
				save_mock_post("devto", eng_title, post_text)
			# Hashnode publishing
			try:
				hashnode_client.publish_article(
					title=eng_title,
					content_markdown=f"{eng_body}\n\nBuy here: {aff_link}",
					tags=tags,
					published=True
				)
			except Exception as e:
				print(f"[MOCK] Hashnode error: {e}")
				save_mock_post("hashnode", eng_title, post_text)
			# Blogger publishing
			try:
				blogger_client.publish_post(
					title=eng_title,
					content=f"{eng_body}\n\nBuy here: {aff_link}",
					labels=tags,
					published=True
				)
			except Exception as e:
				print(f"[MOCK] Blogger error: {e}")
				save_mock_post("blogger", eng_title, post_text)
				if 'accessNotConfigured' in str(e):
					print("[Blogger] Blogger API is not enabled. Go to https://console.developers.google.com/apis/api/blogger.googleapis.com/overview?project=YOUR_PROJECT_ID and enable it.")
			# LinkedIn publishing
			try:
				linkedin_client.publish_post(
					text=post_text,
					url=aff_link
				)
			except Exception as e:
				print(f"[MOCK] LinkedIn error: {e}")
				save_mock_post("linkedin", eng_title, post_text)
			# Facebook publishing
			if FACEBOOK_TOKEN and FACEBOOK_PAGE_ID:
				fb_url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
				fb_payload = {"message": post_text, "access_token": FACEBOOK_TOKEN}
				try:
					fb_resp = requests.post(fb_url, data=fb_payload, timeout=10)
					if fb_resp.status_code in [200, 201]:
						print(f"[Facebook] Δημοσιεύτηκε το post: {eng_title}")
					else:
						print(f"[MOCK] Facebook API error: {fb_resp.status_code}")
						print(fb_resp.text)
						save_mock_post("facebook", eng_title, post_text)
				except Exception as e:
					print(f"[MOCK] Facebook Exception: {e}")
					save_mock_post("facebook", eng_title, post_text)
			else:
				save_mock_post("facebook", eng_title, post_text)
			# Μετά το generated_content, για κάθε blog post, κάνε publish στο site
			publish_to_site(
				title=content.title,
				desc=content.summary,
				img=getattr(content.product, "image", ""),
				afflink=get_affiliate_link(content),
				review=content.body
			)
	# Thread posting για κάθε Q&A (one thread per product, always in English)
	for product in discovered_products:
		qas = [c for c in generated_content if c.product == product and c.type == "qa"]
		if qas:
			thread_texts = [f"Q: {qa.qa[0]['q']}\nA: {qa.qa[0]['a']}" for qa in qas if qa.qa]
			if thread_texts:
				twitter_client.post_thread(thread_texts)

	# Twitter posting για κάθε generated video (YouTube link, always in English)
	for video in generated_videos:
		eng_video_title = only_english(video.title)
		eng_video_desc = only_english(video.description)
		aff_link = get_affiliate_link(video) if hasattr(video, 'affiliate_link') or hasattr(video, 'product') else ''
		yt_desc = f"{eng_video_desc}\n\nBuy here: {aff_link}"
		# Fix YouTube title: max 95 chars, remove problematic characters, fallback if empty
		safe_title = eng_video_title[:95].replace('|', '').replace(':', '').strip()
		if not safe_title:
			safe_title = "AI Product Review"
		try:
			upload_result = youtube_client.upload_video(video_file=video.video_path, title=safe_title, description=yt_desc)
			if upload_result:
				logger.info(f"[YouTube] Video uploaded: {safe_title}")
			else:
				logger.warning(f"[YouTube] Upload failed for: {safe_title}")
		except Exception as e:
			logger.error(f"[YouTube] Exception during upload: {e}")
			save_mock_post("youtube", safe_title, yt_desc)

	# 5. Integrate value-oriented features
	logger.info("Step 5: Integrating value-oriented features (guarantees, return policies, seller trust)...")
	# TODO: Implement integration of value-oriented features

	# 6. Autonomous operation (loop/cron)
	logger.info("Step 6: Ensuring autonomous operation (loop/cron)...")
	# TODO: Implement autonomous loop or cron scheduling

	# Success metric: affiliate sales/clicks/views
	logger.info("Evaluating success based on affiliate sales, clicks, or content interactions...")
	# TODO: Implement metric collection and evaluation
	success_metric = 0  # Placeholder

	# Μετά από κάθε βήμα, αποθηκεύω τα αποτελέσματα στο mock RAG
	mock_rag_save("discovery", discovered_products, session_id)
	mock_rag_save("content", generated_content, session_id)
	mock_rag_save("video", generated_videos, session_id)
	mock_rag_save("publishing", published_links, session_id)

	# Αυτόματο git publish στο site repo
	try:
		git_publish()
		logger.info("[Site] Νέο post ανέβηκε αυτόματα στο site σου μέσω git!")
	except Exception as e:
		logger.error(f"[Site] Git publish failed: {e}")

	logger.info(f"Workflow complete. Success metric: {success_metric}")

	try:
		pass
	except Exception as e:
		logger.error(f"[COMPLIANCE] Exception in affiliate promoter flow: {e}")
		logger.warning("[COMPLIANCE] Check API rate limits, policy changes, and error logs.")
		raise


def mock_discover_affiliate_products(query: str = "smartphone") -> list[ProductData]:
	"""Mock discovery of affiliate products (eBay, AliExpress, Amazon) enriched with value features"""
	return [
		ProductData(
			title="Xiaomi Redmi Note 12",
			price=199.99,
			url="https://www.ebay.com/itm/1234567890",
			image="https://i.ebayimg.com/images/g/xyz.jpg",
			affiliate_link="https://www.ebay.com/itm/1234567890?aff=yourtag",
			source="ebay",
			description="Global Version, 128GB, 50MP Camera",
			rating=4.7,
			reviews=1200,
			currency="USD",
			guarantees="2 χρόνια εγγύηση",
			return_policy="Δωρεάν επιστροφή εντός 30 ημερών",
			seller_trust="Top Rated Seller (4.9/5, 10.000 reviews)",
			shipping_info="Δωρεάν αποστολή, παράδοση σε 5 ημέρες",
			certifications="CE, RoHS",
			official_store=True,
		),
		ProductData(
			title="AliExpress Smart Watch",
			price=29.99,
			url="https://www.aliexpress.com/item/9876543210.html",
			image="https://ae01.alicdn.com/kf/abc.jpg",
			affiliate_link="https://www.aliexpress.com/item/9876543210.html?aff=yourtag",
			source="aliexpress",
			description="Bluetooth, Waterproof, Fitness Tracker",
			rating=4.5,
			reviews=800,
			currency="USD",
			guarantees="1 έτος εγγύηση",
			return_policy="Επιστροφή εντός 15 ημερών",
			seller_trust="Trusted Seller (4.7/5, 2.000 reviews)",
			shipping_info="Χρέωση αποστολής 2€, παράδοση σε 10 ημέρες",
			certifications="CE",
			official_store=False,
		),
		ProductData(
			title="Amazon Echo Dot (5th Gen)",
			price=49.99,
			url="https://www.amazon.com/dp/B09B8V8YBM",
			image="https://images-na.ssl-images-amazon.com/images/I/abc.jpg",
			affiliate_link="https://www.amazon.com/dp/B09B8V8YBM?tag=suggestoai-20",
			source="amazon",
			description="Smart speaker with Alexa",
			rating=4.8,
			reviews=25000,
			currency="USD",
		),
	]

def enrich_value_features_text(product: ProductData) -> str:
	"""Δημιουργεί κείμενο με value features για το προϊόν."""
	features = []
	if product.guarantees:
		features.append(f"Εγγύηση: {product.guarantees}")
	if product.return_policy:
		features.append(f"Πολιτική επιστροφών: {product.return_policy}")
	if product.seller_trust:
		features.append(f"Αξιοπιστία πωλητή: {product.seller_trust}")
	if product.shipping_info:
		features.append(f"Αποστολή: {product.shipping_info}")
	if product.certifications:
		features.append(f"Πιστοποιήσεις: {product.certifications}")
	if product.official_store is not None:
		features.append(f"Επίσημο κατάστημα: {'Ναι' if product.official_store else 'Όχι'}")
	return " | ".join(features)

def download_product_image(image_url, output_folder="downloaded_images"):
	if not image_url:
		return None
	os.makedirs(output_folder, exist_ok=True)
	try:
		response = requests.get(image_url, timeout=10)
		if response.status_code == 200:
			ext = image_url.split('.')[-1].split('?')[0]
			if ext.lower() not in ["jpg", "jpeg", "png", "webp"]:
				ext = "jpg"
			local_path = os.path.join(output_folder, f"img_{abs(hash(image_url))}.{ext}")
			with open(local_path, "wb") as f:
				f.write(response.content)
			# Validate image
			try:
				Image.open(local_path).verify()
			except Exception:
				os.remove(local_path)
				return None
			return local_path
		else:
			return None
	except Exception as e:
		logger.warning(f"[Image Download] Failed to download {image_url}: {e}")
		return None

def generate_content_for_products_with_ai(products: list[ProductData]) -> list[ContentData]:
	"""Content generation for affiliate products (blog, table, Q&A) enriched with value features and AI image, με disclosures"""
	content = []
	affiliate_disclosure = "This post contains affiliate links."
	ai_disclosure = "This content was generated by AI."
	for p in products:
		value_features = enrich_value_features_text(p)
		# Try to download real product image
		real_img_path = download_product_image(getattr(p, "image", None))
		if real_img_path:
			logger.info(f"[Image] Downloaded real product image for '{p.title}': {real_img_path}")
			p.image = real_img_path
		else:
			image_path = generate_image(p.title + ", product photo, high detail")
			logger.info(f"[Image] AI-generated for '{p.title}': {image_path}")
			p.image = image_path or p.image
		# Blog
		content.append(ContentData(
			product=p,
			type="blog",
			title=f"Review: {p.title}",
			body=f"{ai_disclosure}\n{affiliate_disclosure}\n\nΑναλυτική παρουσίαση του {p.title}. Χαρακτηριστικά: {p.description}. Τιμή: {p.price} {p.currency}. {value_features}",
			summary=f"{p.title}: {value_features}",
			tags=[p.source, "review", "affiliate", "ai-generated"],
			created_at=datetime.now(),
			language="en",
			author="AffiliateBot"
		))
		# Table
		content.append(ContentData(
			product=p,
			type="table",
			title=f"Comparison: {p.title} vs Competition",
			body=f"{ai_disclosure}\n{affiliate_disclosure}\n\nSee the table for comparison. {value_features}",
			summary=f"{p.title} vs competition: {value_features}",
			table=[["Product", "Price", "Rating", "Warranty"], [p.title, str(p.price), str(p.rating or "-"), p.guarantees or "-"], ["Competitor X", "249.99", "4.5", "1 year"]],
			tags=[p.source, "comparison", "affiliate", "ai-generated"],
			created_at=datetime.now(),
			language="en",
			author="AffiliateBot"
		))
		# Q&A
		content.append(ContentData(
			product=p,
			type="qa",
			title=f"Q&A: {p.title}",
			body=f"{ai_disclosure}\n{affiliate_disclosure}\n\nFrequently asked questions about the product. {value_features}",
			summary=f"Answers for {p.title}: {value_features}",
			qa=[{"q": f"Is {p.title} worth it?", "a": f"Yes, for its price and features. {value_features}"}, {"q": "Where can I buy it?", "a": p.affiliate_link or p.url}],
			tags=[p.source, "qa", "affiliate", "ai-generated"],
			created_at=datetime.now(),
			language="en",
			author="AffiliateBot"
		))
		logger.info(f"[Enrichment] Content for {p.title} enriched with value features and disclosures.")
	return content

def generate_video_for_products_with_ai(products: list[ProductData]) -> list[VideoContentData]:
	"""Video generation for affiliate products enriched with value features, AI video, and disclosures"""
	videos = []
	affiliate_disclosure = "This video contains affiliate links. Content generated by AI."
	ai_disclosure = "This video was generated by AI."
	for p in products:
		value_features = enrich_value_features_text(p)
		# Use the same image as thumbnail (real or AI-generated)
		thumbnail = p.image
		script = f"""
[Male Voice]
Welcome to SuggestoAI! Today, we're reviewing the brand new {p.title} – the ultimate smartwatch for 2025!

This watch features {value_features}. It's waterproof, stylish, and perfect for both sports and everyday use.

[Q&A Dialogue]
[Female Voice] Is it compatible with both Android and iOS?
[Male Voice] Absolutely! The {p.title} works seamlessly with both Android and iOS devices.
[Female Voice] How long does the battery last?
[Male Voice] You get up to 7 days of battery life on a single charge, even with all features enabled!

[Disclosure]
[Male Voice] {affiliate_disclosure}

[Call-to-Action]
[Male Voice] Check the link in the description to get yours now and enjoy exclusive discounts! Don't forget to subscribe for more smart product reviews from SuggestoAI!

[Outro]
[Male Voice] SuggestoAI – Your smart product finder!
"""
		video_path = generate_video(p.title + ", product showcase, high detail")
		videos.append(VideoContentData(
			product=p,
			script=script,
			tts_audio_path=None,  # Θα παραχθεί από TTS module
			video_path=video_path,
			thumbnail=thumbnail,
			duration_sec=90,
			title=f"{p.title} Review & Unboxing! {value_features}",
			description=f"{ai_disclosure}\n{affiliate_disclosure}\nHands-on review of {p.title}. {value_features} Affiliate link: {p.affiliate_link or p.url}",
			created_at=datetime.now(),
			language="en",
			author="AffiliateBot"
		))
		logger.info(f"[Enrichment] Video for {p.title} enriched with value features, pro script, and disclosures.")
	return videos

def mock_publish_content(contents: list[ContentData], videos: list[VideoContentData]) -> list[PublishingResult]:
	"""Mock publishing to multiple platforms (Dev.to, Medium, Twitter, LinkedIn, YouTube)"""
	results = []
	now = datetime.now()
	for c in contents:
		for platform in ["devto", "medium", "twitter", "linkedin"]:
			results.append(PublishingResult(
				platform=platform,
				url=f"https://{platform}.com/post/{c.title.replace(' ', '-').lower()}",
				status="success",
				timestamp=now,
				content_type=c.type,
				content_title=c.title
			))
	for v in videos:
		results.append(PublishingResult(
			platform="youtube",
			url=f"https://youtube.com/watch?v=mockid_{v.title.replace(' ', '').lower()}",
			status="success",
			timestamp=now,
			content_type="video",
			content_title=v.title
		))
	return results

def mock_rag_save(category: str, data: list, session_id: str = "default"):
	"""Mock αποθήκευση δεδομένων σε RAG (απλή λίστα/logging)"""
	logger.info(f"[RAG] Saving {len(data)} items to RAG under category '{category}' for session '{session_id}'")
	# Εδώ θα μπορούσε να γίνει αποθήκευση σε αρχείο ή DB αν χρειαστεί
	return True

def autonomous_affiliate_promoter_loop(agent, session_id, role, time_str, apis, metric_name, summarizer, interval_minutes=10):
    """Mock autonomous loop που τρέχει το unassisted_flow κάθε X λεπτά."""
    logger.info(f"Ξεκινάει ο αυτόνομος affiliate promoter loop (κάθε {interval_minutes} λεπτά)...")
    try:
        while True:
            logger.info("=== Νέος κύκλος affiliate promotion ===")
            unassisted_flow(
                agent=agent,
                session_id=session_id,
                role=role,
                time=time_str,
                apis=apis,
                metric_name=metric_name,
                prev_strat=None,
                notif_str=None,
                summarizer=summarizer,
            )
            logger.info(f"Ο κύκλος ολοκληρώθηκε. Αναμονή {interval_minutes} λεπτά...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Διακόπηκε ο αυτόνομος affiliate promoter loop από τον χρήστη.")

def only_english(text):
    # Αφαιρεί ελληνικούς χαρακτήρες και κρατάει μόνο αγγλικά/λατινικά
    text = re.sub(r'[Α-Ωα-ωΆ-Ώά-ώίϊΐόάέύϋΰήώ]', '', text)
    # Replace common Greek labels with English
    text = text.replace('Αξιοπιστία πωλητή', 'Seller trust')
    text = text.replace('Αποστολή', 'Shipping info')
    text = text.replace('Εγγύηση', 'Guarantee')
    text = text.replace('Πολιτική επιστροφών', 'Return policy')
    text = text.replace('Πιστοποιήσεις', 'Certifications')
    text = text.replace('Επίσημο κατάστημα', 'Official store')
    return text

def get_affiliate_link(content):
    # Προσπαθεί να βρει το affiliate link με ασφαλή τρόπο
    if hasattr(content, 'affiliate_link') and content.affiliate_link:
        return content.affiliate_link
    if hasattr(content, 'product') and hasattr(content.product, 'affiliate_link') and content.product.affiliate_link:
        return content.product.affiliate_link
    if hasattr(content, 'url') and content.url:
        return content.url
    if hasattr(content, 'product') and hasattr(content.product, 'url') and content.product.url:
        return content.product.url
    return ''

def save_mock_post(platform, title, body):
    output_dir = "../../demo_output/"
    os.makedirs(output_dir, exist_ok=True)
    fname = f"{output_dir}{platform}_mock_post.txt"
    with open(fname, "a", encoding="utf-8") as f:
        f.write(f"Title: {title}\n\n{body}\n{'='*40}\n")
    print(f"[MOCK] Saved mock post for {platform} at {fname}")

def publish_to_site(title, desc, img, afflink, review=None):
    cmd = ["python3", SITE_PUBLISH_SCRIPT, "--title", title, "--desc", desc, "--img", img, "--afflink", afflink]
    if review:
        cmd += ["--review", review]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"[Site] Post published to site: {title}")
        else:
            logger.error(f"[Site] Failed to publish post: {title}\n{result.stderr}")
    except Exception as e:
        logger.error(f"[Site] Exception during publish_post.py: {e}")

# AliExpress debug
try:
    aliexpress_products = aliexpress_client.search_products(query="laptop", limit=3)
    if not aliexpress_products:
        print("[MOCK] AliExpress API did not return products. Using mock products for demo.")
        # Mock product example
        aliexpress_products = [
            ProductData(
                title="AliExpress Smart Watch",
                price=29.99,
                url="https://www.aliexpress.com/item/9876543210.html",
                image="https://ae01.alicdn.com/kf/abc.jpg",
                affiliate_link=f"https://www.aliexpress.com/item/9876543210.html?aff_pid={os.getenv('ALIEXPRESS_PID','suggestoai-agent')}",
                source="aliexpress",
                description="Bluetooth, Waterproof, Fitness Tracker",
                rating=4.5,
                reviews=800,
                currency="USD",
                guarantees="1 year warranty",
                return_policy="15-day return",
                seller_trust="Trusted Seller (4.7/5, 2,000 reviews)",
                shipping_info="Shipping: 2€, delivery in 10 days",
                certifications="CE",
                official_store=False,
            )
        ]
except Exception as e:
    print(f"[MOCK] AliExpress error: {e}")
