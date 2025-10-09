import os
import json
import aiohttp

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BOT_DATA_FOLDER = os.path.join(BASE_PATH, "BOTS_DATA")


def get_required_channels(bot_id: str):
    """Load required channels list from REQUIRED_CHANNELS.json"""
    file_path = os.path.join(BOT_DATA_FOLDER, bot_id, "REQUIRED_CHANNELS.json")
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [ch.strip() for ch in data if ch.strip()]
        if isinstance(data, str):
            return [ch.strip() for ch in data.split(",") if ch.strip()]
    except Exception:
        pass
    return []


def get_author_ids(bot_id: str):
    """Load owners/admins from AUTHOR.JSON"""
    file_path = os.path.join(BOT_DATA_FOLDER, bot_id, "AUTHOR.JSON")
    if not os.path.exists(file_path):
        return {"owner": [], "admin": []}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            owners = data.get("owner", [])
            admins = data.get("admin", [])
            return {"owner": owners, "admin": admins}
    except Exception:
        return {"owner": [], "admin": []}


async def is_user_subscribed_requests(bot_token: str, bot_id: str, user_id: int):
    """
    Checks if a user is subscribed to all required channels.
    Notifies bot owners if bot is missing from a channel.
    """
    channels = get_required_channels(bot_id)
    if not channels:
        return True  # कोई चैनल नहीं → always True

    authors = get_author_ids(bot_id)
    owners = authors.get("owner", [])

    async with aiohttp.ClientSession() as session:
        for channel in channels:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
            params = {"chat_id": channel, "user_id": user_id}

            try:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                # अगर bot उस चैनल में नहीं है
                if not data.get("ok"):
                    for owner_id in owners:
                        notify_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        text = f"⚠️ कृपया मुझे चैनल में ऐड करें: {channel}"
                        await session.get(notify_url, params={"chat_id": owner_id, "text": text})
                    continue  # skip this channel but do not block user

                status = data["result"]["status"]
                if status in ["left", "kicked"]:
                    return False  # user not subscribed

            except Exception as e:
                print(f"❌ Error checking {channel}: {e}")
                continue

    return True
