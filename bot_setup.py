from aiogram import types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import get_required_channels, get_bot_data, is_user_subscribed_requests

async def setup_handlers(dp):

    @dp.message(Command("start"))
    async def start_handler(message: types.Message):
        user = message.from_user
        user_id = user.id

        # 🔹 Extract bot info
        bot_info = await message.bot.get_me()
        bot_id = str(bot_info.id)
        bot_token = message.bot.token

        # 🔹 Check if user subscribed
        subscribed = await is_user_subscribed_requests(
            bot_token=bot_token,
            bot_id=bot_id,
            user_id=user_id
        )

        if not subscribed:
            # ❗ User not subscribed → show join channels
            required_channels = get_required_channels(bot_id)
            builder = InlineKeyboardBuilder()
            text = "📢 कृपया नीचे दिए गए सभी चैनल्स को जॉइन करें फिर /start भेजें:\n\n"

            for channel in required_channels:
                if channel.startswith("@"):
                    link = f"https://t.me/{channel[1:]}"
                elif channel.startswith("https://t.me/"):
                    link = channel
                else:
                    link = f"https://t.me/{channel}"

                text += f"🔗 {link}\n"
                builder.row(types.InlineKeyboardButton(text="📢 Join Channel", url=link))

            bot_username = bot_info.username
            builder.row(types.InlineKeyboardButton(
                text="➕ Add me to your group",
                url=f"https://t.me/{bot_username}?startgroup=true"
            ))

            await message.answer(text, reply_markup=builder.as_markup())
            return

        # 🔹 Load welcome message from bot_data.json
        bot_data = get_bot_data(bot_id)
        root = bot_data.get("data", {})
        template = root.get("description", "Welcome to Singodiya Tech!")

        # 🔄 Replace placeholders
        user_data = {
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "id": str(user.id),
            "username": user.username or "",
            "mention": f"[{user.first_name}](tg://user?id={user.id})",
            "link": f"tg://user?id={user.id}"
        }

        for key, value in user_data.items():
            template = template.replace(f"${{{key}}}", value)

        # 🔹 Send final message
        await message.answer(template, parse_mode="Markdown")
