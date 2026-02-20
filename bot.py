import telebot
import json
import os
import threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

OWNER_ID = 555142704   # ← PUT YOUR TELEGRAM ID
USERS_FILE = "users.json"

# ---------------- LOAD / SAVE USERS ---------------- #

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ---------------- JOIN REQUEST HANDLER ---------------- #

@bot.chat_join_request_handler()
def handle_join_request(join_request):
    user_id = join_request.from_user.id
    users = load_users()

    if user_id not in users:
        users.append(user_id)
        save_users(users)

        try:
            bot.send_message(
                user_id,
                "👋 <b>Welcome!</b>\n\n"
                "Your join request received ✅\n"
                "You will be approved soon.\n\n"
                "Stay ready for premium trading updates with Arshi 📈"
            )
        except:
            print("User didn't start bot")

# ---------------- BROADCAST TEXT ---------------- #

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

# ---------------- BROADCAST PHOTO ---------------- #

@bot.message_handler(commands=['broadcastphoto'])
def broadcast_photo(message):
    if message.from_user.id != OWNER_ID:
        return

    msg = bot.reply_to(message, "📸 Send photo with caption")
    bot.register_next_step_handler(msg, process_photo)

def process_photo(message):
    users = load_users()
    sent = 0

    if not message.photo:
        bot.reply_to(message, "❌ Send a photo.")
        return

    photo = message.photo[-1].file_id
    caption = message.caption if message.caption else ""

    for user in users:
        try:
            bot.send_photo(user, photo, caption=caption)
            sent += 1
        except:
            pass

    bot.reply_to(message, f"✅ Photo sent to {sent} users")

# ---------------- KEEP RENDER ALIVE WEB SERVER ---------------- #

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# ---------------- MAIN START ---------------- #

if __name__ == "__main__":
    print("Bot running...")
    threading.Thread(target=run_web).start()
    bot.infinity_polling()