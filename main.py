import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup
from flask import Flask
import threading
import json
from datetime import datetime

app = Flask(__name__)

# Telegram Bot Configuration
API_ID = 27303400
API_HASH = "bcfc2fab8ad45bccdd13270669b16aef"
BOT_TOKEN = "7516781828:AAFWWfcB-u5LZpZmBGjtAm_XWgK4YkRYTng"

# Statistics and user tracking
def load_stats():
    try:
        with open('stats.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "total_users": 0,
            "total_downloads": 0,
            "successful_downloads": 0,
            "daily_downloads": {},
            "users": []
        }

def save_stats():
    with open('stats.json', 'w') as f:
        json.dump(stats, f)

stats = load_stats()
user_ids = set(stats["users"])

# Create a Pyrogram Client
bot = Client("insta_reels_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route('/')
def home():
    return 'Bot is running!'

@app.route('/keep_alive')
def keep_alive():
    return 'Bot is active!'

def create_keyboard(is_admin=False):
    buttons = [
        ["📥 Download Video", "❓ Help"],
        ["📊 Statistics"]
    ]
    if is_admin:
        buttons.extend([["🔧 Admin Panel"], ["📢 Broadcast"]])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def download_video(url):
    import time
    output_path = f"downloads/{int(time.time())}.%(ext)s"

    # Instagram-specific handling
    if "instagram.com" in url:
        ydl_opts = { 
            'format': 'best[ext=mp4]',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'max_filesize': 2000000000,  # 2GB limit
            'cookiefile': 'cookies.txt'
        }

    # **Enhanced YouTube Download Handling**
    elif "youtube.com" in url or "youtu.be" in url:
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': False,
            'noplaylist': True,
            'sleep_interval': 3,
            'max_sleep_interval': 7,
            'concurrent_fragment_downloads': 5,
            'extractor_args': {
                'youtube': {'player_client': 'android'},
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com/',
                'Cookie': 'PREF=f1=50000000&hl=en',
            },
            'throttling_method': 'adaptive',
            'nocheckcertificate': True,
            'cookiefile': 'cookies.txt' if os.path.exists("cookies.txt") else None
        }

    # Twitter/X specific options
    elif "twitter.com" in url or "x.com" in url:
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': output_path,
            'quiet': True,
            'cookiesfrombrowser': None,
            'extractor_args': {'twitter': {'max_retries': 3}},
            'max_filesize': 2000000000
        }

    # Facebook and other platforms
    else:
        ydl_opts = { 
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'max_filesize': 2000000000,
            'cookiefile': 'cookies.txt' if os.path.exists("cookies.txt") else None
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Download error: {str(e)}")
        raise

@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("Send me a video link to download.")

@bot.on_message(filters.text)
async def video_downloader(client, message):
    url = message.text.strip()
    supported_platforms = ["instagram.com", "youtube.com", "youtu.be", 
                         "facebook.com", "fb.watch", "twitter.com", "x.com"]

    if any(x in url for x in supported_platforms):
        msg = await message.reply_text("⏳ Downloading...")
        try:
            file_path = download_video(url)
            if os.path.exists(file_path):
                await message.reply_video(video=file_path, caption="🎥 Here's your video!")
                os.remove(file_path)
            else:
                await message.reply_text("⚠️ Video download failed.")
        except Exception as e:
            await message.reply_text(f"⚠️ Error: {str(e)}")
        await msg.delete()
    else:
        await message.reply_text("⚠️ Please send a valid video URL.")

def run_bot():
    os.makedirs("downloads", exist_ok=True)
    print("🤖 Bot is running...")
    bot.run()

def keep_alive():
    def run():
        app.run(host='0.0.0.0', port=8000, threaded=True)
    
    def ping_server():
        import time
        import urllib.request
        while True:
            try:
                urllib.request.urlopen("http://0.0.0.0:8000").read()
            except:
                pass
            time.sleep(180)  # Ping every 3 minutes
    
    server = threading.Thread(target=run)
    server.start()
    
    ping = threading.Thread(target=ping_server)
    ping.daemon = True
    ping.start()

if __name__ == "__main__":
    keep_alive()
    try:
        run_bot()
    except Exception as e:
        print(f"Bot encountered an error: {e}")
        run_bot()
