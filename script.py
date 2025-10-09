import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from common_data import BOTS_FILE, BASE_PATH, BOT_DATA_FOLDER
# -------------------------
# 🔹 Setup folders & env
# -------------------------
#BOTS_FILE = "bots.json"
#BOT_DATA_FOLDER = "BOT_DATA"


load_dotenv()
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://telegram-bot-builder.onrender.com")

# -------------------------
# 🔹 FastAPI app
# -------------------------
app = FastAPI(title="Multi-Bot Manager")


# -------------------------
# 🔹 Bot JSON helpers
# -------------------------
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
