import os
import re
import discord
import feedparser
from discord.ext import tasks
from discord.ext import commands
from flask import Flask
from threading import Thread

# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")
INSTAGRAM_CHANNEL_ID = 1232207096821321799
YOUTUBE_CHANNEL_ID = 1232680374057041970
KARINA_CHANNEL_ID = 1232593363350458369
GISELLE_CHANNEL_ID = 1232593424448749578
WINTER_CHANNEL_ID = 1232593476902719538
NINGNING_CHANNEL_ID = 1232593537770717234
CHECK_INTERVAL_MINUTES = 5

TWITTER_ROLE_IDS = {
    "Twitter_rinabbl": 1232593678757793852,
    "Twitter_winterbbl": 1232594368129667133,
    "Twitter_ningbbl": 1232594417773318196,
    "Twitter_aeribbl": 1232594310835470417
}

# ==== RSS feed URLs ====
FEEDS = {
    # Group Instagram, YouTube & TikTok
    "Instagram_aespa": "https://rsshub.app/instagram/user/aespa_official",
    "YouTube": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9GtSLeksfK4yuJ_g1lgQbg",
    "TikTok": "https://rss.app/feed/lySKpbrl5Df28zrd",

    # Members' Instagram Accounts
    "Instagram_karina": "https://rsshub.app/instagram/user/katarinabluu",
    "Instagram_winter": "https://rsshub.app/instagram/user/imwinter",
    "Instagram_ningning": "https://rsshub.app/instagram/user/imnotningning",
    "Instagram_aeri": "https://rsshub.app/instagram/user/aerichandesu",

    # Members' Twitter Accounts
    "Twitter_rinabbl": "https://rsshub.app/twitter/user/rinabbls",
    "Twitter_winterbbl": "https://rsshub.app/twitter/user/winterbbls",
    "Twitter_ningbbl": "https://rsshub.app/twitter/user/ningbbls",
    "Twitter_aeribbl": "https://rsshub.app/twitter/user/aeribbls"
}

# ==== KEEP-ALIVE SERVER (for Replit) ====
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
last_seen = {key: None for key in FEEDS}

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

@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_feeds():
    for platform_key, url in FEEDS.items():
        entry = get_latest_entry(url)
        if not entry:
            print(f"❌ No entry found for {platform_key}.")
            continue

        link = entry.get("link") or entry.get("id")
        title = entry.get("title", f"New post on {platform_key}")
        summary = entry.get("summary", "")

        if link != last_seen[platform_key]:
            last_seen[platform_key] = link

            # Instagram Posts
            if platform_key.startswith("Instagram"):
                username = platform_key.split("_")[1]
                thumbnail_url = None
                if "media_content" in entry:
                    media = entry.media_content
                    if isinstance(media, list) and media:
                        thumbnail_url = media[0].get("url")
                if not thumbnail_url:
                    thumbnail_url = extract_thumbnail_from_summary(summary)
                embed = discord.Embed(title=f"📸 New Instagram post by {username}", description=summary)
                if thumbnail_url:
                    embed.set_image(url=thumbnail_url)

                if username == "karina":
                    channel = client.get_channel(KARINA_CHANNEL_ID)
                elif username == "giselle":
                    channel = client.get_channel(GISELLE_CHANNEL_ID)
                elif username == "winter":
                    channel = client.get_channel(WINTER_CHANNEL_ID)
                elif username == "ningning":
                    channel = client.get_channel(NINGNING_CHANNEL_ID)
                elif username == "aespa":
                    channel = client.get_channel(INSTAGRAM_CHANNEL_ID)
                else:
                    channel = client.get_channel(YOUTUBE_CHANNEL_ID)

                if channel:
                    await channel.send(content=link, embed=embed)
                else:
                    print(f"❌ Channel not found for {username} Instagram")

            # Twitter Posts
            elif platform_key.startswith("Twitter"):
                username = platform_key.split("_")[1]
                channel = None
                role_id = TWITTER_ROLE_IDS.get(platform_key)

                if username == "rinabbl":
                    channel = client.get_channel(KARINA_CHANNEL_ID)
                elif username == "aeribbl":
                    channel = client.get_channel(GISELLE_CHANNEL_ID)
                elif username == "winterbbl":
                    channel = client.get_channel(WINTER_CHANNEL_ID)
                elif username == "ningbbl":
                    channel = client.get_channel(NINGNING_CHANNEL_ID)
                else:
                    channel = client.get_channel(INSTAGRAM_CHANNEL_ID)

                if channel:
                    mention = f"<@&{role_id}>" if role_id else ""
                    await channel.send(f"🐦 {mention} New tweet by @{username}:\n**{title}**\n{link}")
                else:
                    print(f"❌ Channel not found for {username} Twitter")

            # YouTube and TikTok
            else:
                icon = "📢" if "YouTube" in platform_key else "🎵"
                channel = client.get_channel(YOUTUBE_CHANNEL_ID)
                if channel:
                    await channel.send(f"{icon} New post:\n**{title}**\n{link}")
                else:
                    print(f"❌ Channel not found for {platform_key} (ID: {YOUTUBE_CHANNEL_ID})")

        else:
            print(f"ℹ️ No new post for {platform_key}.")

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
