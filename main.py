import os
import json
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Update

app = FastAPI(title="Multi-Bot Manager")

BOTS_FILE = "bots.json"
BOT_DATA_FOLDER = "BOT_DATA"
os.makedirs(BOT_DATA_FOLDER, exist_ok=True)
from dotenv import load_dotenv

load_dotenv()

# 🔹 Env से लो, अगर ना हो तो default use करो
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://telegram-bot-builder.onrender.com")

print(PUBLIC_URL)
def load_bots():
    if os.path.exists(BOTS_FILE):
        with open(BOTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_bots(data):
    with open(BOTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_bot_id(token: str) -> str:
    """Return numeric prefix from token (e.g. 123456 from 123456:ABC...)"""
    return token.split(":")[0] if ":" in token else token

def load_bot_config(bot_id):
    path = os.path.join(BOT_DATA_FOLDER, f"{bot_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"start_msg": "Hello! I am your bot 🤖", "commands": {}, "keywords": {}}


# -------------------------
# ➕ Add New Bot
# -------------------------
@app.post("/add-bot")
async def add_bot(request: Request):
    data = await request.json()
    bot_name = data.get("bot_name")
    token = data.get("token")

    if not bot_name or not token:
        return {"ok": False, "error": "bot_name and token required"}

    bots = load_bots()
    if bot_name in bots:
        return {"ok": False, "error": "Bot already exists"}

    bots[bot_name] = {"token": token}
    save_bots(bots)

    # Create bot config file
    bot_id = get_bot_id(token)
    config_path = os.path.join(BOT_DATA_FOLDER, f"{bot_id}.json")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            json.dump(
                {
                    "start_msg": f"Hello! I am {bot_name} 🤖",
                    "commands": {},
                    "keywords": {}
                },
                f,
                indent=2
            )

    # Set webhook for this bot
    WEBHOOK_URL = f"{PUBLIC_URL}/webhook/{token}"

    try:
        new_bot = Bot(token=token)
        await new_bot.delete_webhook(drop_pending_updates=True)
        await new_bot.set_webhook(WEBHOOK_URL)
        await new_bot.session.close()
    except Exception as e:
        return {"ok": False, "error": f"Webhook setup failed: {e}"}

    return {"ok": True, "message": f"{bot_name} added successfully", "webhook": WEBHOOK_URL}


# -------------------------
# ✏️ Edit Bot JSON via HTML
# -------------------------
@app.get("/edit-file/{bot_token}", response_class=HTMLResponse)
async def edit_file(bot_token: str):
    bots = load_bots()
    valid_bot = None
    for name, info in bots.items():
        if info["token"] == bot_token:
            valid_bot = info
            break
    if not valid_bot:
        return HTMLResponse("<h3 style='color:red'>❌ Invalid Bot Token</h3>")

    bot_id = get_bot_id(bot_token)
    file_path = os.path.join(BOT_DATA_FOLDER, f"{bot_id}.json")

    if not os.path.exists(file_path):
        return HTMLResponse("<h3 style='color:red'>⚠️ Bot data file not found.</h3>")

    with open(file_path, "r") as f:
        file_content = f.read()

    html = f"""
    <html>
    <head>
        <title>Edit Bot File - {bot_id}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            textarea {{
                width: 100%;
                height: 70vh;
                font-family: monospace;
                font-size: 14px;
                border-radius: 8px;
                border: 1px solid #ccc;
                padding: 10px;
                resize: vertical;
            }}
            button {{
                background: #0084ff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{ background: #005fcc; }}
        </style>
    </head>
    <body>
        <h2>📝 Edit Config for Bot ID: {bot_id}</h2>
        <form method="post" action="/save-file/{bot_token}">
            <textarea name="content">{file_content}</textarea><br><br>
            <button type="submit">💾 Save Changes</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(html)


# -------------------------
# 💾 Save Edited File
# -------------------------
@app.post("/save-file/{bot_token}")
async def save_file(bot_token: str, content: str = Form(...)):
    bots = load_bots()
    valid_bot = None
    for name, info in bots.items():
        if info["token"] == bot_token:
            valid_bot = info
            break
    if not valid_bot:
        return HTMLResponse("<h3 style='color:red'>❌ Invalid Bot Token</h3>")

    bot_id = get_bot_id(bot_token)
    file_path = os.path.join(BOT_DATA_FOLDER, f"{bot_id}.json")

    try:
        json.loads(content)  # validate JSON
        with open(file_path, "w") as f:
            f.write(content)
        return HTMLResponse("<h3 style='color:green'>✅ Changes saved successfully!</h3>")
    except Exception as e:
        return HTMLResponse(f"<h3 style='color:red'>❌ Invalid JSON Format: {e}</h3>")


# -------------------------
# 🤖 Webhook Receiver (same as before)
# -------------------------
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    data = await request.json()
    bots = load_bots()

    bot_info = None
    bot_name = None
    for name, info in bots.items():
        if info["token"] == token:
            bot_info = info
            bot_name = name
            break
    if not bot_info:
        return {"ok": False, "error": "Unknown bot"}

    bot_id = get_bot_id(token)
    bot_config = load_bot_config(bot_id)

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(Command(commands=["start"]))
    async def start_handler(message: types.Message):
        await message.answer(bot_config.get("start_msg", "Hello!"))

    for cmd_name, reply_text in bot_config.get("commands", {}).items():
        def gen_handler(text):
            async def handler(message: types.Message):
                await message.answer(text)
            return handler
        dp.message(Command(commands=[cmd_name]))(gen_handler(reply_text))

    @dp.message()
    async def keyword_reply(message: types.Message):
        text = message.text.lower().strip()
        for key, reply in bot_config.get("keywords", {}).items():
            if key.lower() in text:
                await message.answer(reply)
                break

    try:
        update = Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"⚠️ Webhook error for {bot_name}: {e}")
    finally:
        await bot.session.close()

    return {"ok": True}


# -------------------------
# Startup/Shutdown
# -------------------------
@app.on_event("startup")
async def on_startup():

    bots = load_bots()
    for name, info in bots.items():
        token = info["token"]
        WEBHOOK_URL = f"{PUBLIC_URL}/webhook/{token}"
        try:
            bot = Bot(token=token)
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(WEBHOOK_URL)
            await bot.session.close()
            print(f"✅ Webhook set for {name}: {WEBHOOK_URL}")
        except Exception as e:
            print(f"⚠️ Failed to set webhook for {name}: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    bots = load_bots()
    for name, info in bots.items():
        try:
            bot = Bot(token=info["token"])
            await bot.delete_webhook()
            await bot.session.close()
        except:
            pass
    print("🛑 All bots stopped")


@app.get("/")
def home():
    return {"ok": True, "message": "Multi Telegram Bot Manager is running 🚀"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
