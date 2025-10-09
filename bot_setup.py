from aiogram import types
from aiogram.filters import Command

dp_global = None

def setup_handlers(dp):
    global dp_global
    dp_global = dp

@dp_global.message(Command(commands=["start"]))
async def start_handler(message: types.Message):
    await message.answer("Hello! This is start message.")

@dp_global.message()
async def keyword_reply(message: types.Message):
    text = message.text.lower().strip()
    if "hi" in text:
        await message.answer("Hello there!")
