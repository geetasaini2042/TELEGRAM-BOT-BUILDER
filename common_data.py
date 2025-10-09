import os

load_dotenv()
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://127.0.0.1:8000")

BOTS_FILE
BOT_DATA_FOLDER
os.makedirs(BOT_DATA_FOLDER, exist_ok=True)
