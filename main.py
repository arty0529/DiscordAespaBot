import discord
from discord.ext import tasks
import feedparser
import os
from flask import Flask
from threading import Thread
import random
import json
from datetime import time

# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")
UPDATE_CHANNEL_ID = 1232207096821321799
FACT_CHANNEL_ID = 1232181937846620195
CHECK_INTERVAL_MINUTES = 5

# aespa Official YouTube Channel Feed
YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UC9GtSLeksfK4yuJ_g1lgQbg"

# ==== AESPA FACTS ====
with open("aespa_facts.json", "r", encoding="utf-8") as f:
    aespa_facts = json.load(f)

# ==== KEEP-ALIVE SERVER ====
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

client = discord.Client(intents=intents)

# ==== LAST VIDEO CACHE ====
last_youtube = None

# ==== AESPA STATUS ROTATION ====
aespa_statuses = [
    " Switchblade",
    " WDA ft. G Dragon",
    " Lemonade",
    " Dirty Work",
    " Whiplash",
    " Supernova",
    " Armageddon",
    " Drama",
    " Spicy",
    " Better Things",
    " Next Level",
    " Savage",
    " Black Mamba",
    " Illusion",
    " Lucid Dream",
    " Salty & Sweet",
    " Set The Tone",
]

def get_latest_entry(feed_url):
    feed = feedparser.parse(feed_url)
    return feed.entries[0] if feed.entries else None

# ==== STATUS ROTATION ====
@tasks.loop(minutes=5)
async def rotate_status():
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=random.choice(aespa_statuses)
        )
    )

# ==== YOUTUBE CHECKER ====
@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_youtube():
    global last_youtube

    channel = client.get_channel(UPDATE_CHANNEL_ID)
    if not channel:
        return

    entry = get_latest_entry(YOUTUBE_FEED)

    if entry and entry.link != last_youtube:
        last_youtube = entry.link

        await channel.send(
            f"📢 **New aespa YouTube Upload!**\n"
            f"**{entry.title}**\n"
            f"{entry.link}"
        )

# ==== DAILY FACTS ==== 
@tasks.loop(time=time(hour=1, minute=0))
async def daily_fact():
    channel = client.get_channel(FACT_CHANNEL_ID)

    if channel:
        fact = random.choice(aespa_facts)

        embed = discord.Embed(
            title="💙 Daily aespa Fact",
            description=fact,
            color=0x7ED6DF
        )

        embed.set_footer(text="Come back tomorrow for another fact!")

        await channel.send(embed=embed)

# ==== BOT READY ====
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

    if not rotate_status.is_running():
        rotate_status.start()

    if not check_youtube.is_running():
        check_youtube.start()

        if not daily_fact.is_running():
        daily_fact.start()

    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=random.choice(aespa_statuses)
        )
    )

# ==== START ====
keep_alive()

if TOKEN:
    client.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN is not set.")
