import os
import json
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Update
import uvicorn

from script import app, load_bots, save_bots, get_bot_id, load_bot_config
from common_data import BOT_DATA_FOLDER, PUBLIC_URL
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
# ✏️ Edit & Save File Endpoints
# -------------------------
@app.get("/edit-file/{bot_token}", response_class=HTMLResponse)
async def edit_file(bot_token: str):
    bots = load_bots()
    valid_bot = next((info for name, info in bots.items() if info["token"] == bot_token), None)
    if not valid_bot:
        return HTMLResponse("<h3 style='color:red'>❌ Invalid Bot Token</h3>")

    bot_id = get_bot_id(bot_token)
    file_path = os.path.join(BOT_DATA_FOLDER, f"{bot_id}.json")
    if not os.path.exists(file_path):
        return HTMLResponse("<h3 style='color:red'>⚠️ Bot data file not found.</h3>")

    with open(file_path, "r") as f:
        file_content = f.read()

    html = f"""<html> ... <textarea name="content">{file_content}</textarea> ... </html>"""
    return HTMLResponse(html)


@app.post("/save-file/{bot_token}")
async def save_file(bot_token: str, content: str = Form(...)):
    bots = load_bots()
    valid_bot = next((info for name, info in bots.items() if info["token"] == bot_token), None)
    if not valid_bot:
        return HTMLResponse("<h3 style='color:red'>❌ Invalid Bot Token</h3>")

    bot_id = get_bot_id(bot_token)
    file_path = os.path.join(BOT_DATA_FOLDER, f"{bot_id}.json")

    try:
        json.loads(content)
        with open(file_path, "w") as f:
            f.write(content)
        return HTMLResponse("<h3 style='color:green'>✅ Changes saved successfully!</h3>")
    except Exception as e:
        return HTMLResponse(f"<h3 style='color:red'>❌ Invalid JSON Format: {e}</h3>")


# -------------------------
# 🤖 Webhook Receiver
# -------------------------
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    data = await request.json()
    bots = load_bots()
    bot_info = next(((name, info) for name, info in bots.items() if info["token"] == token), None)

    if not bot_info:
        return {"ok": False, "error": "Unknown bot"}

    bot_name, info = bot_info
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
