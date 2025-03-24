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
    
    # Instagram-specific handling exactly as in original script
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
    
    # YouTube specific options
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
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10)',
            },
            'throttling_method': 'http',
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
            'max_filesize': 2000000000,  # 2GB limit
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
    if message.from_user.id not in user_ids:
        stats["total_users"] += 1
        user_ids.add(message.from_user.id)
        stats["users"].append(message.from_user.id)
        save_stats()
        
        # Send notification to admin
        admin_id = 7439517139
        user = message.from_user
        notification = f"🆕 New User Joined!\n\n👤 Name: {user.first_name}\n🆔 User ID: `{user.id}`\n📝 Username: @{user.username or 'None'}"
        try:
            await client.send_message(admin_id, notification)
        except:
            print("Could not send admin notification")
        
    is_admin = message.from_user.id == 7439517139
    welcome_text = """💫 Ultimate Videos Downloader 🚀

👀 Seamless Downloading for:
• 📸 Instagram Videos
• 📱 Facebook Reels
• 🐦 Twitter/X Videos
• 🎥 YouTube Videos

Features:
• ⚡ Ultra-Fast Downloads
• 🎥 High-Quality Video Capture
• 📊 Comprehensive Download Tracking

Simply send your video link!"""

    await message.reply_text(welcome_text, reply_markup=create_keyboard(is_admin=is_admin))

@bot.on_message(filters.regex("^❓ Help$") | filters.command("help"))
async def help_command(client, message):
    help_text = """🆘 Help & Instructions

1. To download a video, simply send a Instagram, Facebook, Twitter, or YouTube link.
2. The bot supports:
   • Instagram Videos & Reels
   • Facebook Videos & Reels
   • Twitter/X Videos
   • YouTube Videos
3. Maximum file size: 2GB
4. Large videos may be sent in multiple parts.
5. Use '📊 Statistics' to view your download stats.
6. If you encounter any issues, please try again or contact support.

For more assistance, contact @Biobhaiya"""
    is_admin = message.from_user.id == 7439517139
    await message.reply_text(help_text, reply_markup=create_keyboard(is_admin=is_admin))

@bot.on_message(filters.regex("^📊 Statistics$") | filters.command("stats"))
async def stats_command(client, message):
    today = datetime.now().strftime("%Y-%m-%d")
    daily_downloads = stats.get("daily_downloads", {}).get(today, 0)
    success_rate = (stats["successful_downloads"] / stats["total_downloads"] * 100) if stats["total_downloads"] > 0 else 0

    stats_text = f"""📊 Bot Statistics

👥 Total Users: {stats["total_users"]}
📥 Total Downloads: {stats["total_downloads"]}
✅ Successful Downloads: {stats["successful_downloads"]}
📅 Today's Downloads: {daily_downloads}
🔢 Success Rate: {success_rate:.2f}%"""
    is_admin = message.from_user.id == 7439517139
    await message.reply_text(stats_text, reply_markup=create_keyboard(is_admin=is_admin))

@bot.on_message(filters.regex("^📥 Download Video$"))
async def download_button(client, message):
    is_admin = message.from_user.id == 7439517139
    await message.reply_text("Please send me a video URL to download.", reply_markup=create_keyboard(is_admin=is_admin))

@bot.on_message(filters.regex("^🔧 Admin Panel$"))
async def admin_button(client, message):
    if message.from_user.id == 7439517139:
        admin_text = f"""🔧 Admin Panel

Current Statistics:
👥 Total Users: {stats["total_users"]}
📥 Total Downloads: {stats["total_downloads"]}
✅ Success Rate: {(stats["successful_downloads"] / stats["total_downloads"] * 100) if stats["total_downloads"] > 0 else 0:.2f}%"""
        await message.reply_text(admin_text, reply_markup=create_keyboard(is_admin=True))
    else:
        await message.reply_text("⚠️ Admin panel access is restricted.", reply_markup=create_keyboard())

@bot.on_message((filters.command("broadcast") | filters.regex("^📢 Broadcast$")) & filters.private)
async def broadcast_command(client, message):
    if message.text == "📢 Broadcast":
        await message.reply_text("To broadcast a message, use:\n/broadcast <your message>")
        return
    if message.from_user.id != 7439517139:
        await message.reply_text("⚠️ This command is only for admins.")
        return

    if len(message.text.split()) < 2:
        await message.reply_text("📝 Usage: /broadcast <message>")
        return

    broadcast_message = message.text.split(None, 1)[1]
    success_count = 0
    fail_count = 0

    progress_msg = await message.reply_text("🚀 Broadcasting message...")

    for user_id in user_ids:
        try:
            await client.send_message(user_id, f"📢 Broadcast Message:\n\n{broadcast_message}")
            success_count += 1
        except:
            fail_count += 1

    await progress_msg.edit_text(
        f"✅ Broadcast completed!\n"
        f"✓ Success: {success_count}\n"
        f"× Failed: {fail_count}"
    )

@bot.on_message(filters.text & filters.private)
async def video_downloader(client, message):
    url = message.text.strip()
    supported_platforms = ["instagram.com", "youtube.com", "youtu.be", 
                         "facebook.com", "fb.watch", "twitter.com", "x.com"]

    if any(x in url for x in supported_platforms):
        msg = await message.reply_text("⏳ Processing your download request...")
        today = datetime.now().strftime("%Y-%m-%d")
        stats["total_downloads"] += 1
        stats["daily_downloads"][today] = stats["daily_downloads"].get(today, 0) + 1
        save_stats()

        try:
            file_path = download_video(url)
            if os.path.exists(file_path):
                try:
                    await message.reply_video(
                        video=file_path,
                        caption="🎉 Here's your video! Enjoy watching! 🎥",
                        reply_markup=create_keyboard()
                    )
                    stats["successful_downloads"] += 1
                    save_stats()
                except Exception as e:
                    await message.reply_text(
                        "⚠️ Video file too large or format not supported. Try another video.",
                        reply_markup=create_keyboard()
                    )
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                await message.reply_text(
                    "⚠️ Sorry, this video is unavailable or private. Please check if the video exists and is publicly accessible.",
                    reply_markup=create_keyboard()
                )
        except Exception as e:
            error_message = str(e)
            if "Video unavailable" in error_message:
                await message.reply_text(
                    "⚠️ This video is no longer available or is private.",
                    reply_markup=create_keyboard()
                )
            else:
                await message.reply_text(
                    "⚠️ An error occurred while processing your request. Please try again later.",
                    reply_markup=create_keyboard()
                )
        finally:
            await msg.delete()
    else:
        await message.reply_text(
            "⚠️ Please send a valid Instagram, YouTube, Facebook, or Twitter video URL.",
            reply_markup=create_keyboard()
        )

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
    ping.daemon = True  # This ensures the thread exits when the main program exits
    ping.start()

if __name__ == "__main__":
    # Start the keep-alive server with self-pinging
    keep_alive()
    try:
        # Start the bot
        run_bot()
    except Exception as e:
        print(f"Bot encountered an error: {e}")
        # Restart the bot
        run_bot()
