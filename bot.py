import telebot
import os
import json
import threading
import requests
import base64
from flask import Flask

# ================== CONFIG ================== #

TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

OWNER_ID = 555142704   # ← your Telegram ID
REPO = "preal471-hub/Arshi_request_bot"
FILE_PATH = "users.json"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================== GITHUB DATABASE ================== #

def get_file_data():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode()
        return json.loads(content), data["sha"]
    return [], None

def load_users():
    users, _ = get_file_data()
    return users

def save_user(user_id):
    users, sha = get_file_data()

    if user_id in users:
        return

    users.append(user_id)

    encoded_content = base64.b64encode(json.dumps(users).encode()).decode()

    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    data = {
        "message": "New user added",
        "content": encoded_content,
        "sha": sha
    }

    requests.put(url, headers=headers, json=data)

# ================== JOIN REQUEST ================== #

@bot.chat_join_request_handler()
def handle_join_request(join_request):
    user_id = join_request.from_user.id

    save_user(user_id)

    try:
        bot.send_message(
            user_id,
            "👋 <b>Welcome!</b>\n\n"
            "Your join request received ✅\n"
            "You will be approved manually soon.\n\n"
            "Stay ready for premium trading updates 📈"
        )
    except:
        print("User has not started bot")

# ================== START COMMAND ================== #

@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.chat.id)

    bot.reply_to(
        message,
        "🤖 Bot Connected Successfully!\n\n"
        "You will receive updates here."
    )

# ================== BROADCAST TEXT ================== #

@bot.message_handler(commands=['broadcast'])
def broadcast_text(message):

    if message.from_user.id != OWNER_ID:
        return

    text = message.text.replace("/broadcast ", "")
    users = load_users()

    sent = 0
    for user in users:
        try:
            bot.send_message(user, text)
            sent += 1
        except:
            pass

    bot.reply_to(message, f"✅ Text sent to {sent} users")

# ================== BROADCAST PHOTO ================== #

@bot.message_handler(commands=['broadcastphoto'])
def broadcast_photo(message):

    if message.from_user.id != OWNER_ID:
        return

    msg = bot.reply_to(message, "📸 Send photo with caption")
    bot.register_next_step_handler(msg, process_photo)

def process_photo(message):

    if not message.photo:
        bot.reply_to(message, "❌ Send a photo.")
        return

    users = load_users()
    photo = message.photo[-1].file_id
    caption = message.caption if message.caption else ""

    sent = 0
    for user in users:
        try:
            bot.send_photo(user, photo, caption=caption)
            sent += 1
        except:
            pass

    bot.reply_to(message, f"✅ Photo sent to {sent} users")

# ================== FLASK SERVER (Railway) ================== #

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ================== MAIN ================== #

if __name__ == "__main__":
    print("Bot running...")

    threading.Thread(target=run_web).start()
    bot.infinity_polling()
