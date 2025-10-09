import os
from dotenv import load_dotenv
load_dotenv()
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://127.0.0.1:8000")
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BOTS_FILE = os.path.join(BASE_PATH, "bots.json") 
BOT_DATA_FOLDER = os.path.join(BASE_PATH, "BOTS_DATA")
os.makedirs(BOT_DATA_FOLDER, exist_ok=True)
