import os
import re
import discord
import feedparser
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
    "TWITTER_BBL": 123220709682132179  # adjust if needed
}

# ==== FEEDS BY CHANNEL ====
FEEDS_BY_CHANNEL = {
    AESPA_UPDATES_CHANNEL_ID: {
        # aespa official
        "Instagram_aespa": "https://rsshub-sc05.onrender.com/instagram/user/aespa_official",
        "Twitter_aespa": "https://rsshub-sc05.onrender.com/nitter/user/aespa_official",
        "TikTok": "https://rsshub-sc05.onrender.com/tiktok/user/aespa_official",
        "YouTube": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9GtSLeksfK4yuJ_g1lgQbg",

        # BBL Twitters
        "Twitter_rinabbl": "https://rsshub-sc05.onrender.com/nitter/user/rinabbls",
        "Twitter_winterbbl": "https://rsshub-sc05.onrender.com/nitter/user/winterbbls",
        "Twitter_ningbbl": "https://rsshub-sc05.onrender.com/nitter/user/ningtexts",
        "Twitter_aeribbl": "https://rsshub-sc05.onrender.com/nitter/user/aeribbls",
    },
    KARINA_CHANNEL_ID: {
        "Instagram_karina": "https://rsshub-sc05.onrender.com/instagram/user/katarinabluu",
    },
    WINTER_CHANNEL_ID: {
        "Instagram_winter": "https://rsshub-sc05.onrender.com/instagram/user/imwinter",
    },
    NINGNING_CHANNEL_ID: {
        "Instagram_ningning": "https://rsshub-sc05.onrender.com/instagram/user/imnotningning",
    },
    GISELLE_CHANNEL_ID: {
        "Instagram_aeri": "https://rsshub-sc05.onrender.com/instagram/user/aerichandesu",
    },
}

# ==== KEEP-ALIVE SERVER (for Replit/Render) ====
app = Flask("")

@app.route("/")
def home():
    return "✅ Bot is running."

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

# ==== DISCORD CLIENT SETUP ====
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

# ==== LAST SEEN POSTS CACHE ====
last_seen = {key: None for feeds in FEEDS_BY_CHANNEL.values() for key in feeds}

# ==== UTILS ====
def extract_thumbnail_from_summary(summary):
    match = re.search(r'<img[^>]+src="([^"]+)', summary)
    return match.group(1) if match else None

def get_latest_entry(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        return feed.entries[0] if feed.entries else None
    except Exception as e:
        print(f"❌ Failed to parse feed {feed_url}: {e}")
        return None

# ==== FEED CHECK LOOP ====
@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_feeds():
    for channel_id, feeds in FEEDS_BY_CHANNEL.items():
        channel = client.get_channel(channel_id)
        if not channel:
            print(f"❌ Channel not found for ID {channel_id}")
            continue

        for platform_key, url in feeds.items():
            entry = get_latest_entry(url)
            if not entry:
                print(f"❌ No entry found for {platform_key}.")
                continue

            link = entry.get("link") or entry.get("id")
            title = entry.get("title", f"New post on {platform_key}")
            summary = entry.get("summary", "")

            if link == last_seen.get(platform_key):
                print(f"ℹ️ No new post for {platform_key}.")
                continue

            # update cache
            last_seen[platform_key] = link

            # Instagram posts
            if platform_key.startswith("Instagram"):
                username = platform_key.split("_")[1]
                thumbnail_url = None
                if "media_content" in entry:
                    media = entry.media_content
                    if isinstance(media, list) and media:
                        thumbnail_url = media[0].get("url")
                if not thumbnail_url:
                    thumbnail_url = extract_thumbnail_from_summary(summary)

                embed = discord.Embed(
                    title=f"📸 New Instagram post by {username}",
                    description=summary,
                )
                if thumbnail_url:
                    embed.set_image(url=thumbnail_url)

                await channel.send(content=link, embed=embed)

            # Twitter posts
            elif platform_key.startswith("Twitter"):
                username = platform_key.split("_")[1]
                role_id = TWITTER_ROLE_IDS.get("TWITTER_BBL")
                mention = f"<@&{role_id}>" if role_id else ""
                await channel.send(f"🐦 {mention} New tweet by @{username}:\n**{title}**\n{link}")

            # YouTube / TikTok
            elif "YouTube" in platform_key:
                await channel.send(f"📢 New YouTube upload:\n**{title}**\n{link}")
            elif "TikTok" in platform_key:
                await channel.send(f"🎵 New TikTok post:\n**{title}**\n{link}")

@client.event
async def on_ready():
    await client.wait_until_ready()
    print(f"✅ Logged in as {client.user}")

    activity = discord.Activity(type=discord.ActivityType.listening, name="Dirty Work by aespa")
    await client.change_presence(status=discord.Status.online, activity=activity)

    check_feeds.start()

# ==== START BOT ====
keep_alive()

if TOKEN:
    client.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN is not set in environment variables.")

