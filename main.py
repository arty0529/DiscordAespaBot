import os
import re
import json
import discord
import feedparser
import requests
import random
from discord.ext import tasks
from flask import Flask
from threading import Thread

# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")

AESPA_UPDATES_CHANNEL_ID = 1232207096821321799
KARINA_CHANNEL_ID = 1232593363350458369
GISELLE_CHANNEL_ID = 1232593424448749578
WINTER_CHANNEL_ID = 1232593476902719538
NINGNING_CHANNEL_ID = 1232593537770717234
CHECK_INTERVAL_MINUTES = 5

TWITTER_ROLE_IDS = {
    "TWITTER_BBL": 123220709682132179
}

NITTER_INSTANCES = [
    "https://nitter.poast.org/",
    "https://nitter.net/",
    "https://nitter.42l.fr/",
    "https://nitter.kavin.rocks/",
]

songs = [
    "aespa - Supernova",
    "aespa - Drama",
    "aespa - Spicy",
    "aespa - Next Level"
]

FEEDS_BY_CHANNEL = {
    AESPA_UPDATES_CHANNEL_ID: {
        "Instagram_aespa": "https://rsshub-sc05.onrender.com/instagram/user/aespa_official",
        "Twitter_aespa": "aespa_official",
        "TikTok": "https://rsshub-sc05.onrender.com/tiktok/user/aespa_official",
        "YouTube": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9GtSLeksfK4yuJ_g1lgQbg",
    }
}

#  ==== KEEP-ALIVE SERVER (REQUIRED for Render Web Service) ====
app = Flask("")

@app.route("/")
def home():
    return "✅ Bot is running."

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

# ==== DISCORD CLIENT ====
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

# ==== CACHE ====
CACHE_FILE = "last_seen.json"

def load_last_seen():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_seen():
    with open(CACHE_FILE, "w") as f:
        json.dump(last_seen, f)

last_seen = load_last_seen()

# ==== UTILS ====
def get_feed_entries(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        return feed.entries if feed.entries else []
    except Exception as e:
        print(f"Failed feed: {e}")
        return []

def get_nitter_feed(username):
    for base in NITTER_INSTANCES:
        url = f"{base}/{username}/rss"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return url
        except:
            continue
    return None

# ==== LOOP ====
@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_feeds():
    for channel_id, feeds in FEEDS_BY_CHANNEL.items():
        channel = client.get_channel(channel_id)
        if not channel:
            continue

        for key, value in feeds.items():
            url = value

            if key.startswith("Twitter"):
                url = get_nitter_feed(value)
                if not url:
                    continue

            entries = get_feed_entries(url)
            if not entries:
                continue

            entry = entries[0]
            link = entry.get("link") or entry.get("id")

            if last_seen.get(key) == link:
                continue

            last_seen[key] = link
            save_last_seen()

            await channel.send(f"New update:\n{link}")

# ==== READY EVENT ====
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    song = random.choice(songs)

    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name=song
    )

    await client.change_presence(activity=activity)

    check_feeds.start()

# ==== START EVERYTHING ====
keep_alive()

if TOKEN:
    client.run(TOKEN)
else:
    print("DISCORD_TOKEN missing")
