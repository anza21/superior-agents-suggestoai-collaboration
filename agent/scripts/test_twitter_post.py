import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

# Πάρε τα tokens από το .env
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Έλεγχος αν όλα υπάρχουν
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    print("[ERROR] Λείπουν tokens από το .env!")
    exit(1)

# Tweepy setup (OAuth 1.0a, Free plan)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

try:
    tweet = api.update_status("Test tweet from Superior Agent free plan!")
    print(f"[SUCCESS] Tweet posted! ID: {tweet.id}")
except Exception as e:
    print(f"[ERROR] {e}") 