import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# -------- VARIABLES --------

PHOTO_URL = os.getenv("PHOTO_URL")

MESSAGE_TEXT = os.getenv("MESSAGE_TEXT")

BUTTON1_TEXT = os.getenv("BUTTON1_TEXT")
BUTTON1_LINK = os.getenv("BUTTON1_LINK")

BUTTON2_TEXT = os.getenv("BUTTON2_TEXT")
BUTTON2_LINK = os.getenv("BUTTON2_LINK")

# ---------------------------

def main_buttons():
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(BUTTON1_TEXT, url=BUTTON1_LINK),
        InlineKeyboardButton(BUTTON2_TEXT, url=BUTTON2_LINK)
    )

    kb.add(
        InlineKeyboardButton("👀 Continue", callback_data="continue")
    )

    return kb


@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await bot.send_photo(
        message.chat.id,
        PHOTO_URL,
        caption=MESSAGE_TEXT,
        reply_markup=main_buttons()
    )


# LOOP TRAP
@dp.callback_query_handler(lambda c: c.data == "continue")
async def continue_loop(call: types.CallbackQuery):

    await call.message.delete()

    await bot.send_photo(
        call.message.chat.id,
        PHOTO_URL,
        caption=MESSAGE_TEXT,
        reply_markup=main_buttons()
    )


# ADMIN PANEL
@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.reply(
        "Admin Panel\n\n"
        "/settext\n"
        "/setphoto\n"
        "/setbutton1\n"
        "/setbutton2"
    )


if __name__ == "__main__":
    executor.start_polling(dp)
