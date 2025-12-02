import os
import threading
import requests
from pathlib import Path
from flask import Flask, send_from_directory, abort
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "8358684642:AAHntcN33numPcvFpsRICAhuL31DkH3Qn8Y"
VIDEO_DIR = "videos"
BASE_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")

os.makedirs(VIDEO_DIR, exist_ok=True)

app = Flask(__name__)

@app.route("/watch/<file>")
def stream(file):
    path = Path(VIDEO_DIR) / file
    if not path.exists():
        abort(404)
    return send_from_directory(VIDEO_DIR, file, mimetype="video/mp4")

def background_download(url, filename):
    save_path = Path(VIDEO_DIR) / filename
    r = requests.get(url, stream=True)
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(1024 * 256):
            if chunk:
                f.write(chunk)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # detect forwarded or normal video
    file = msg.video or msg.document

    if not file:
        await msg.reply_text("❌ Only video supported.")
        return

    file_id = file.file_id
    unique = file.file_unique_id + ".mp4"

    # Step 1: Get Telegram direct file path (CDN URL)
    info = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    ).json()

    if not info.get("ok"):
        await msg.reply_text("❌ Error fetching file.")
        return

    tg_path = info["result"]["file_path"]
    cdn_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_path}"

    # Step 2: Send streaming link instantly
    stream_link = f"https://{BASE_URL}/watch/{unique}"

    await msg.reply_text(
        f"🎬 *Your Streaming Link Ready!*\n\n▶️ {stream_link}",
        parse_mode="Markdown"
    )

    # Step 3: Background download (FAST)
    threading.Thread(target=background_download, args=(cdn_url, unique)).start()

def run_server():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

def run_bot():
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle))
    bot.run_polling()

threading.Thread(target=run_server).start()
threading.Thread(target=run_bot).start()
