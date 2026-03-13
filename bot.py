import telebot
from telebot import types
import json
import os
import base64

TOKEN = "8388764592:AAEkBbwJPSykxjNRO5YxzvDnC8EQU1XOYcw"
ADMIN_ID = 1912548374

bot = telebot.TeleBot(TOKEN)

CHANNEL_FILE = "channels.json"
LINK_FILE = "links.json"
USER_FILE = "users.json"


# ------------------------
# File helpers
# ------------------------

def load_file(file):
    if not os.path.exists(file):
        return []
    with open(file,"r") as f:
        return json.load(f)

def save_file(file,data):
    with open(file,"w") as f:
        json.dump(data,f)


# ------------------------
# Save user
# ------------------------

def save_user(user_id):

    users = load_file(USER_FILE)

    if user_id not in users:
        users.append(user_id)
        save_file(USER_FILE,users)


# ------------------------
# Check join
# ------------------------

def check_join(user_id):

    channels = load_file(CHANNEL_FILE)

    not_joined = []

    for ch in channels:

        try:
            member = bot.get_chat_member(ch,user_id)

            if member.status in ["left","kicked"]:
                not_joined.append(ch)

        except:
            not_joined.append(ch)

    return not_joined


# ------------------------
# Encode decode
# ------------------------

def encode_link(link):
    return base64.urlsafe_b64encode(link.encode()).decode()

def decode_link(code):
    return base64.urlsafe_b64decode(code.encode()).decode()


# ------------------------
# Start command
# ------------------------

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    save_user(user_id)

    args = message.text.split()

    # Admin panel
    if user_id == ADMIN_ID and len(args) == 1:

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        markup.row("📊 Stats","📢 Broadcast")
        markup.row("🔗 Create Link","📢 Channels")

        bot.send_message(
            message.chat.id,
            "👑 Admin Panel",
            reply_markup=markup
        )
        return


    if len(args) > 1:

        code = args[1]

        try:
            link = decode_link(code)

        except:
            bot.send_message(message.chat.id,"Invalid link")
            return

        not_joined = check_join(user_id)

        if not not_joined:

            bot.send_message(
                message.chat.id,
                f"✅ Access Granted\n\n{link}"
            )
            return


        markup = types.InlineKeyboardMarkup()

        for ch in not_joined:

            markup.add(
                types.InlineKeyboardButton(
                    "Join Channel",
                    url=f"https://t.me/{ch.replace('@','')}"
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "Verify",
                callback_data=f"verify|{code}"
            )
        )

        bot.send_message(
            message.chat.id,
            "⚠️ Join all channels first.",
            reply_markup=markup
        )

    else:

        bot.send_message(message.chat.id,"Send protected link to access content.")


# ------------------------
# Verify
# ------------------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify"))
def verify(call):

    code = call.data.split("|")[1]

    link = decode_link(code)

    not_joined = check_join(call.from_user.id)

    if not not_joined:

        bot.send_message(
            call.message.chat.id,
            f"✅ Access Granted\n\n{link}"
        )

    else:

        bot.answer_callback_query(call.id,"❌ Join channels first")


# ------------------------
# Add channel
# ------------------------

@bot.message_handler(commands=['addchannel'])
def add_channel(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        ch = message.text.split()[1]

        channels = load_file(CHANNEL_FILE)

        if ch not in channels:

            channels.append(ch)

            save_file(CHANNEL_FILE,channels)

            bot.reply_to(message,f"✅ Channel added\n{ch}")

    except:

        bot.reply_to(message,"Usage:\n/addchannel @channel")


# ------------------------
# Admin panel buttons
# ------------------------

@bot.message_handler(func=lambda message: message.text=="📊 Stats")
def stats(message):

    if message.from_user.id != ADMIN_ID:
        return

    users = load_file(USER_FILE)

    bot.send_message(
        message.chat.id,
        f"👥 Total Users: {len(users)}"
    )


# ------------------------
# Create protected link
# ------------------------

@bot.message_handler(func=lambda message: message.text=="🔗 Create Link")
def ask_link(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "Send the link you want to protect:"
    )

    bot.register_next_step_handler(msg,create_link)


def create_link(message):

    link = message.text

    code = encode_link(link)

    protected = f"https://t.me/archiversXbot?start={code}"

    bot.send_message(
        message.chat.id,
        f"🔐 Protected Link:\n\n{protected}"
    )


# ------------------------
# Broadcast
# ------------------------

@bot.message_handler(func=lambda message: message.text=="📢 Broadcast")
def broadcast_start(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "Send message to broadcast:"
    )

    bot.register_next_step_handler(msg,send_broadcast)


def send_broadcast(message):

    users = load_file(USER_FILE)

    success = 0

    for user in users:

        try:

            bot.send_message(user,message.text)

            success += 1

        except:
            pass

    bot.send_message(
        message.chat.id,
        f"✅ Broadcast sent to {success} users"
    )


# ------------------------
# Show channels
# ------------------------

@bot.message_handler(func=lambda message: message.text=="📢 Channels")
def show_channels(message):

    if message.from_user.id != ADMIN_ID:
        return

    channels = load_file(CHANNEL_FILE)

    if not channels:

        bot.send_message(message.chat.id,"No channels added")
        return

    text="📢 Channels:\n\n"

    for ch in channels:
        text+=ch+"\n"

    bot.send_message(message.chat.id,text)


# ------------------------
# Run bot
# ------------------------

print("Bot running...")

bot.remove_webhook()

bot.infinity_polling()
