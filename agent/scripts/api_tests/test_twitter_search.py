import os
import tweepy
from dotenv import load_dotenv

load_dotenv()
client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)

try:
    # Search for recent tweets containing "python"
    response = client.search_recent_tweets(query="python", max_results=10)
    print("Meta:", response.meta)
    if response.data:
        for tweet in response.data:
            print(tweet.text)
    else:
        print("No tweets found.")
except Exception as e:
    print("Error:", e) 