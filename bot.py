import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
load_dotenv()



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")

bot = Bot(token="8692810587:AAF5ffeASDDQ7Az5if5ZYRI8AlGi9-5nL3o")
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Handle /start command"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🧱 Open LEGO Price Finder",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    
    await message.answer(
        "🧱 *LEGO Minifigure Price Finder*\n\n"
        "Welcome! This bot helps collectors find current prices for LEGO minifigures.\n\n"
        "📊 Features:\n"
        "• Search prices on BrickLink & Avito\n"
        "• AI photo recognition\n"
        "• Available in English & Russian\n\n"
        "Click the button below to open the app!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.message()
async def handle_webapp_data(message: types.Message):
    """Handle data received from WebApp"""
    if message.web_app_data:
        data = message.web_app_data.data
        await message.answer(f"✅ Received data from Mini App:\n`{data}`", parse_mode="Markdown")


async def set_menu_button():
    """Set the menu button to open the WebApp"""
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🧱 Price Finder",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )


async def main():
    await set_menu_button()
    logger.info("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
