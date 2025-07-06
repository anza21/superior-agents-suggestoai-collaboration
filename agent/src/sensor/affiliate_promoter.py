from datetime import datetime, timedelta
from functools import partial
import os
import tweepy
from dotenv import load_dotenv
import requests

from src.twitter import TweepyTwitterClient, TweetData
from loguru import logger
from result import UnwrapError


MOCK_TIME = datetime(2025, 1, 31, 10, 0, 0)
MOCK_TWEETS = [
	TweetData(
		id="1750812345678901234",
		text="Just loaded up on more $SOL 🚀 Paper hands can't see the vision. We're going to MOON soon! #DiamondHands #Solana",
		created_at=(MOCK_TIME - timedelta(minutes=15)).isoformat(),
		author_id="8675309111",
		author_username="cryptomoonboy",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901235",
		text="1/5 Why $ETH is still undervalued: A thread 🧵\nThe merge was just the beginning. Layer 2 scaling is changing everything...",
		created_at=(MOCK_TIME - timedelta(hours=1)).isoformat(),
		author_id="8675309222",
		author_username="eth_maxi_chad",
		thread_id="1750812345678901235",
	),
	TweetData(
		id="1750812345678901236",
		text="WAGMI fam! Just deployed my first NFT collection on OpenSea. Whitelist spots available for true believers 👀 #NFTs #web3",
		created_at=(MOCK_TIME - timedelta(hours=2)).isoformat(),
		author_id="8675309333",
		author_username="nft_degen_life",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901237",
		text="If you're not staking your $BTC with 100x leverage, do you even crypto? NFA but bears are about to get rekt 📈",
		created_at=(MOCK_TIME - timedelta(hours=3)).isoformat(),
		author_id="8675309444",
		author_username="leverage_king",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901238",
		text="This is financial advice: Buy high, sell low 🤡 Just kidding! But seriously, accumulate $BTC under 100k while you still can!",
		created_at=(MOCK_TIME - timedelta(hours=4)).isoformat(),
		author_id="8675309555",
		author_username="satoshi_disciple",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901239",
		text="🚨 ALPHA LEAK 🚨\nNew DeFi protocol launching next week. Already got my nodes set up. Early adopters will make it.",
		created_at=(MOCK_TIME - timedelta(hours=5)).isoformat(),
		author_id="8675309666",
		author_username="defi_alpha_leaks",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901240",
		text="Remember when they said crypto was dead? Look at us now! Stack sats and ignore the FUD. Time in the market > timing the market 💎",
		created_at=(MOCK_TIME - timedelta(hours=6)).isoformat(),
		author_id="8675309777",
		author_username="hodl_guru",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901241",
		text="GM future millionaires! Daily reminder to zoom out on the $BTC chart and touch grass. We're still so early! ☀️",
		created_at=(MOCK_TIME - timedelta(hours=7)).isoformat(),
		author_id="8675309888",
		author_username="crypto_mindset",
		thread_id=None,
	),
	TweetData(
		id="1750812345678901242",
		text="Why I sold my house to buy $PEPE: A thread 🐸\nNo one understands memecoins like me. This is financial advice.",
		created_at=(MOCK_TIME - timedelta(hours=8)).isoformat(),
		author_id="8675309999",
		author_username="meme_coin_chad",
		thread_id="1750812345678901242",
	),
	TweetData(
		id="1750812345678901243",
		text="Just finished my 69th YouTube video on why $BTC will hit 1 million by EOY. Like and subscribe for more hopium! 🚀",
		created_at=(MOCK_TIME - timedelta(hours=9)).isoformat(),
		author_id="8675309000",
		author_username="crypto_influencer_420",
		thread_id=None,
	),
]
MOCK_NUMBER = 27


class AffiliatePromoterTwitterClient:
	def __init__(self):
		self.client = tweepy.Client(
			bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
			consumer_key=os.getenv("TWITTER_API_KEY"),
			consumer_secret=os.getenv("TWITTER_API_SECRET"),
			access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
			access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
		)
		self.read_count = 0
		self.write_count = 0
		self.read_limit = 100
		self.write_limit = 500

	def can_search(self):
		return self.read_count < self.read_limit

	def can_post(self):
		return self.write_count < self.write_limit

	def search_recent_tweets(self, query, max_results=10):
		if not self.can_search():
			print("[Twitter] Search limit reached for this month!")
			return []
		try:
			response = self.client.search_recent_tweets(query=query, max_results=max_results)
			self.read_count += 1
			return response.data or []
		except Exception as e:
			print("[Twitter] Search error:", e)
			return []

	def create_tweet(self, text):
		if not self.can_post():
			print("[Twitter] Post limit reached for this month!")
			return None
		try:
			response = self.client.create_tweet(text=text)
			self.write_count += 1
			print(f"[Twitter] Tweet posted: {response.data}")
			return response.data
		except Exception as e:
			print("[Twitter] Post error:", e)
			return None

	def reply_to_tweet(self, text, in_reply_to_tweet_id):
		if not self.can_post():
			print("[Twitter] Post limit reached for this month!")
			return None
		try:
			response = self.client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to_tweet_id)
			self.write_count += 1
			print(f"[Twitter] Reply posted: {response.data}")
			return response.data
		except Exception as e:
			print("[Twitter] Reply error:", e)
			return None

	def create_tweet_with_youtube(self, text, youtube_url):
		tweet_text = f"{text}\nWatch on YouTube: {youtube_url}"
		return self.create_tweet(tweet_text)

	def is_relevant_tweet(self, tweet):
		# Φίλτρο: απαντά μόνο σε tweets με ερωτηματικό ή/και >10 followers
		if hasattr(tweet, 'text') and '?' in tweet.text:
			return True
		# Αν έχει user info, μπορείς να βάλεις φίλτρο followers (αν το API το επιστρέφει)
		return False

	def post_thread(self, tweets_list):
		"""Δημιουργεί thread στο Twitter από λίστα κειμένων."""
		if not tweets_list:
			return []
		thread_ids = []
		prev_tweet_id = None
		for text in tweets_list:
			if not self.can_post():
				print("[Twitter] Post limit reached for this month!")
				break
			try:
				if prev_tweet_id:
					response = self.client.create_tweet(text=text, in_reply_to_tweet_id=prev_tweet_id)
				else:
					response = self.client.create_tweet(text=text)
				self.write_count += 1
				tweet_id = response.data['id'] if response and response.data else None
				prev_tweet_id = tweet_id
				thread_ids.append(tweet_id)
				print(f"[Twitter] Thread tweet posted: {tweet_id}")
			except Exception as e:
				print("[Twitter] Thread post error:", e)
		return thread_ids

	def sentiment_analysis(self, text):
		"""Κάνει sentiment analysis με HuggingFace API (π.χ. distilbert-base-uncased-finetuned-sst-2-english)."""
		HF_TOKEN = os.getenv("HF_TOKEN")
		api_url = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
		headers = {"Authorization": f"Bearer {HF_TOKEN}"}
		payload = {"inputs": text}
		try:
			response = requests.post(api_url, headers=headers, json=payload, timeout=10)
			if response.status_code == 200:
				result = response.json()
				label = result[0][0]['label'] if result and isinstance(result[0], list) else None
				score = result[0][0]['score'] if result and isinstance(result[0], list) else None
				return label, score
			else:
				print(f"[HuggingFace] Sentiment API error: {response.status_code}")
				return None, None
		except Exception as e:
			print("[HuggingFace] Sentiment API exception:", e)
			return None, None


class AffiliatePromoterSensor:
	def __init__(self, twitter_client: TweepyTwitterClient):
		self.twitter_client = twitter_client

	def get_count_of_followers(self) -> int:
		try:
			count = self.twitter_client.get_count_of_followers().unwrap()
		except UnwrapError as e:
			e = e.result.err()
			logger.error(
				f"AffiliatePromoterSensor.get_count_of_followers: Failed getting follower number from twitter, err: \n{e}\ndefaulting..."
			)
			return 27

		return count

	def get_count_of_likes(self) -> int:
		try:
			count = self.twitter_client.get_count_of_me_likes().unwrap()
		except UnwrapError as e:
			e = e.result.err()
			logger.error(
				f"AffiliatePromoterSensor.get_count_of_likes: Failed getting follower number from twitter, err: \n{e}\ndefaulting..."
			)
			return 27 * 4

		return count

	def get_metric_fn(self, metric_name: str = "followers"):
		metrics = {
			"followers": partial(self.get_count_of_followers),
			"likes": partial(self.get_count_of_likes),
		}

		if metric_name not in metrics:
			raise ValueError(f"Unsupported metric: {metric_name}")

		return metrics[metric_name]
