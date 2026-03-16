import logging
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_IDS = os.environ.get('ADMIN_IDS', '').split(',')  # Comma-separated admin Telegram user IDs

# Database setup
def init_db():
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Insert default values if table is empty
    default_settings = [
        ('button1_text', os.environ.get('BUTTON1_TEXT', 'Agent Link 1')),
        ('button1_url', os.environ.get('BUTTON1_URL', 'https://t.me/your_channel1')),
        ('button2_text', os.environ.get('BUTTON2_TEXT', 'Agent Link 2')),
        ('button2_url', os.environ.get('BUTTON2_URL', 'https://t.me/your_channel2')),
        ('continue_text', os.environ.get('CONTINUE_TEXT', 'Continue')),
        ('bot_photo', os.environ.get('BOT_PHOTO', '')),
        ('bot_message', os.environ.get('BOT_MESSAGE', '''Google Maps
5 Star Rating + Review

- Must Join All Channels To GET ₹180 + ₹200 AGENT
- Process ~ After Joining Click Joined Button ✅
- You Will Get Automatically NSE (₹180 + ₹200) Agent 😊!!'''))
    ]
    
    for key, value in default_settings:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def update_setting(key, value):
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    c.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

# Initialize database
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with buttons when /start is issued."""
    await send_main_message(update, context)

async def send_main_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the main message with buttons."""
    # Get current settings from database
    button1_text = get_setting('button1_text')
    button1_url = get_setting('button1_url')
    button2_text = get_setting('button2_text')
    button2_url = get_setting('button2_url')
    continue_text = get_setting('continue_text')
    bot_photo = get_setting('bot_photo')
    bot_message = get_setting('bot_message')
    
    keyboard = [
        [InlineKeyboardButton(button1_text, url=button1_url)],
        [InlineKeyboardButton(button2_text, url=button2_url)],
        [InlineKeyboardButton(continue_text, callback_data='continue')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get chat_id
    if update.callback_query:
        chat_id = update.callback_query.message.chat_id
        message = update.callback_query.message
    else:
        chat_id = update.effective_chat.id
        message = None
    
    # Send photo if available, otherwise just text
    if bot_photo:
        try:
            if message:
                await message.delete()
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=bot_photo,
                caption=bot_message,
                reply_markup=reply_markup
            )
        except:
            try:
                if message:
                    await message.delete()
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=bot_photo,
                    caption=bot_message,
                    reply_markup=reply_markup
                )
            except:
                if message:
                    await message.edit_text(
                        text=bot_message,
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(
                        text=bot_message,
                        reply_markup=reply_markup
                    )
    else:
        if message:
            await message.edit_text(
                text=bot_message,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=bot_message,
                reply_markup=reply_markup
            )
    
    if update.callback_query:
        await update.callback_query.answer()

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callback queries."""
    query = update.callback_query
    
    if query.data == 'continue':
        await send_main_message(update, context)

# Admin Commands
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel to change bot settings."""
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not authorized to use admin commands.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📝 Change Button 1", callback_data='admin_btn1')],
        [InlineKeyboardButton("📝 Change Button 2", callback_data='admin_btn2')],
        [InlineKeyboardButton("🔄 Change Continue Button", callback_data='admin_continue')],
        [InlineKeyboardButton("📷 Change Photo", callback_data='admin_photo')],
        [InlineKeyboardButton("✏️ Change Message Text", callback_data='admin_text')],
        [InlineKeyboardButton("👁️ View Current Settings", callback_data='admin_view')],
        [InlineKeyboardButton("❌ Close", callback_data='admin_close')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ *Admin Panel*\n\nSelect what you want to change:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin panel callbacks."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await query.answer("⛔ Unauthorized", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'admin_btn1':
        context.user_data['admin_action'] = 'set_btn1_text'
        await query.edit_message_text(
            "📝 Send me the new text for *Button 1*:",
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_btn2':
        context.user_data['admin_action'] = 'set_btn2_text'
        await query.edit_message_text(
            "📝 Send me the new text for *Button 2*:",
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_continue':
        context.user_data['admin_action'] = 'set_continue_text'
        await query.edit_message_text(
            "🔄 Send me the new text for *Continue button*:",
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_photo':
        context.user_data['admin_action'] = 'set_photo'
        await query.edit_message_text(
            "📷 Send me a new photo or a photo file_id:",
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_text':
        context.user_data['admin_action'] = 'set_message'
        await query.edit_message_text(
            "✏️ Send me the new message text:",
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_view':
        settings_text = f"*Current Settings:*\n\n"
        settings_text += f"*Button 1:* {get_setting('button1_text')}\n"
        settings_text += f"*Button 1 URL:* {get_setting('button1_url')}\n"
        settings_text += f"*Button 2:* {get_setting('button2_text')}\n"
        settings_text += f"*Button 2 URL:* {get_setting('button2_url')}\n"
        settings_text += f"*Continue:* {get_setting('continue_text')}\n"
        settings_text += f"*Photo:* {'Set' if get_setting('bot_photo') else 'Not set'}\n"
        settings_text += f"*Message:*\n{get_setting('bot_message')[:100]}..."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_back':
        # Recreate admin panel
        keyboard = [
            [InlineKeyboardButton("📝 Change Button 1", callback_data='admin_btn1')],
            [InlineKeyboardButton("📝 Change Button 2", callback_data='admin_btn2')],
            [InlineKeyboardButton("🔄 Change Continue Button", callback_data='admin_continue')],
            [InlineKeyboardButton("📷 Change Photo", callback_data='admin_photo')],
            [InlineKeyboardButton("✏️ Change Message Text", callback_data='admin_text')],
            [InlineKeyboardButton("👁️ View Current Settings", callback_data='admin_view')],
            [InlineKeyboardButton("❌ Close", callback_data='admin_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⚙️ *Admin Panel*\n\nSelect what you want to change:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == 'admin_close':
        await query.edit_message_text("✅ Admin panel closed.")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input from admin for settings changes."""
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS or 'admin_action' not in context.user_data:
        return
    
    action = context.user_data['admin_action']
    text = update.message.text
    
    if action == 'set_btn1_text':
        context.user_data['admin_action'] = 'set_btn1_url'
        context.user_data['temp_btn1_text'] = text
        await update.message.reply_text(
            f"✅ Button 1 text set to: *{text}*\n\nNow send me the URL for Button 1:",
            parse_mode='Markdown'
        )
    
    elif action == 'set_btn1_url':
        update_setting('button1_text', context.user_data.get('temp_btn1_text', 'Agent Link 1'))
        update_setting('button1_url', text)
        context.user_data.pop('temp_btn1_text', None)
        context.user_data.pop('admin_action', None)
        await update.message.reply_text(
            f"✅ Button 1 updated!\n\nText: *{get_setting('button1_text')}*\nURL: *{get_setting('button1_url')}*",
            parse_mode='Markdown'
        )
        await admin_panel(update, context)
    
    elif action == 'set_btn2_text':
        context.user_data['admin_action'] = 'set_btn2_url'
        context.user_data['temp_btn2_text'] = text
        await update.message.reply_text(
            f"✅ Button 2 text set to: *{text}*\n\nNow send me the URL for Button 2:",
            parse_mode='Markdown'
        )
    
    elif action == 'set_btn2_url':
        update_setting('button2_text', context.user_data.get('temp_btn2_text', 'Agent Link 2'))
        update_setting('button2_url', text)
        context.user_data.pop('temp_btn2_text', None)
        context.user_data.pop('admin_action', None)
        await update.message.reply_text(
            f"✅ Button 2 updated!\n\nText: *{get_setting('button2_text')}*\nURL: *{get_setting('button2_url')}*",
            parse_mode='Markdown'
        )
        await admin_panel(update, context)
    
    elif action == 'set_continue_text':
        update_setting('continue_text', text)
        context.user_data.pop('admin_action', None)
        await update.message.reply_text(
            f"✅ Continue button text updated to: *{text}*",
            parse_mode='Markdown'
        )
        await admin_panel(update, context)
    
    elif action == 'set_message':
        update_setting('bot_message', text)
        context.user_data.pop('admin_action', None)
        await update.message.reply_text(
            f"✅ Message text updated!",
            parse_mode='Markdown'
        )
        await admin_panel(update, context)

async def handle_admin_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo input from admin."""
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS or context.user_data.get('admin_action') != 'set_photo':
        return
    
    if update.message.photo:
        photo = update.message.photo[-1]
        update_setting('bot_photo', photo.file_id)
    elif update.message.text:
        update_setting('bot_photo', update.message.text)
    else:
        await update.message.reply_text("❌ Please send a photo or a valid file_id/URL.")
        return
    
    context.user_data.pop('admin_action', None)
    await update.message.reply_text("✅ Photo updated successfully!")
    await admin_panel(update, context)

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^continue$'))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern='^admin_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_input))
    application.add_handler(MessageHandler(filters.PHOTO, handle_admin_photo))

    # Start the Bot
    print("Bot started! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
