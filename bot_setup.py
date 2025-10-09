# bot_setup.py
from aiogram import types
from aiogram.filters import Command

def setup_handlers(dp):
    @dp.message(Command(commands=["start"]))
    async def start_handler(message: types.Message):
        await message.answer("Hello! This is start message.")

    @dp.message()
    async def keyword_reply(message: types.Message):
        text = message.text.lower().strip()
        if "hi" in text:
            await message.answer("Hello there!")
