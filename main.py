import logging
import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_IDS = os.environ.get('ADMIN_IDS', '').split(',')

# Database
def init_db():
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Users table for tracking
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_date TEXT
    )''')
    
    defaults = [
        ('button1_text', 'Agent Link 1'),
        ('button1_url', 'https://t.me/your_channel1'),
        ('button2_text', 'Agent Link 2'),
        ('button2_url', 'https://t.me/your_channel2'),
        ('continue_text', 'Continue'),
        ('bot_photo', ''),
        ('bot_message', 'Google Maps 5 Star Rating + Review\n\n- Must Join All Channels To GET ₹180 + ₹200 AGENT\n- Process ~ After Joining Click Joined Button ✅\n- You Will Get Automatically NSE (₹180 + ₹200) Agent 😊!!')
    ]
    
    for key, value in defaults:
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

# User tracking functions
def add_user(user_id, username, first_name):
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    joined_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)",
                  (str(user_id), username or "", first_name or "", joined_date))
        conn.commit()
    except:
        pass
    conn.close()

def get_total_users():
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect('bot_settings.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

init_db()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Track user
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    button1_text = get_setting('button1_text')
    button1_url = get_setting('button1_url')
    button2_text = get_setting('button2_text')
    button2_url = get_setting('button2_url')
    continue_text = get_setting('continue_text')
    bot_message = get_setting('bot_message')
    
    keyboard = [
        [InlineKeyboardButton(button1_text, url=button1_url)],
        [InlineKeyboardButton(button2_text, url=button2_url)],
        [InlineKeyboardButton(continue_text, callback_data='continue')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(bot_message, reply_markup=reply_markup)

# Continue button
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'continue':
        button1_text = get_setting('button1_text')
        button1_url = get_setting('button1_url')
        button2_text = get_setting('button2_text')
        button2_url = get_setting('button2_url')
        continue_text = get_setting('continue_text')
        bot_message = get_setting('bot_message')
        
        keyboard = [
            [InlineKeyboardButton(button1_text, url=button1_url)],
            [InlineKeyboardButton(button2_text, url=button2_url)],
            [InlineKeyboardButton(continue_text, callback_data='continue')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(bot_message, reply_markup=reply_markup)

# Admin panel
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Not authorized")
        return
    
    total_users = get_total_users()
    
    keyboard = [
        [InlineKeyboardButton("📝 Change Button 1", callback_data='admin_btn1')],
        [InlineKeyboardButton("📝 Change Button 2", callback_data='admin_btn2')],
        [InlineKeyboardButton("🔄 Change Continue", callback_data='admin_continue')],
        [InlineKeyboardButton("✏️ Change Message", callback_data='admin_text')],
        [InlineKeyboardButton("📊 Total Users", callback_data='admin_users')],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
        [InlineKeyboardButton("👁️ View Settings", callback_data='admin_view')],
        [InlineKeyboardButton("❌ Close", callback_data='admin_close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"⚙️ *Admin Panel*\n\nTotal Users: {total_users}", 
                                   reply_markup=reply_markup, 
                                   parse_mode='Markdown')

# Admin callbacks
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS:
        await query.answer("⛔ Not authorized")
        return
    
    await query.answer()
    
    if query.data == 'admin_btn1':
        context.user_data['action'] = 'btn1_text'
        await query.edit_message_text("📝 Send new text for Button 1:")
    
    elif query.data == 'admin_btn2':
        context.user_data['action'] = 'btn2_text'
        await query.edit_message_text("📝 Send new text for Button 2:")
    
    elif query.data == 'admin_continue':
        context.user_data['action'] = 'continue_text'
        await query.edit_message_text("🔄 Send new text for Continue button:")
    
    elif query.data == 'admin_text':
        context.user_data['action'] = 'message'
        await query.edit_message_text("✏️ Send new message text:")
    
    elif query.data == 'admin_users':
        total = get_total_users()
        await query.edit_message_text(f"📊 *Total Users: {total}*", parse_mode='Markdown')
    
    elif query.data == 'admin_broadcast':
        context.user_data['action'] = 'broadcast'
        await query.edit_message_text("📢 Send the message you want to broadcast to all users:")
    
    elif query.data == 'admin_view':
        text = f"*Current Settings:*\n\n"
        text += f"*Button 1:* {get_setting('button1_text')}\n"
        text += f"*URL 1:* {get_setting('button1_url')}\n\n"
        text += f"*Button 2:* {get_setting('button2_text')}\n"
        text += f"*URL 2:* {get_setting('button2_url')}\n\n"
        text += f"*Continue:* {get_setting('continue_text')}\n\n"
        text += f"*Message:*\n{get_setting('bot_message')[:100]}..."
        await query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == 'admin_close':
        await query.edit_message_text("✅ Admin panel closed.")

# Handle admin input
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in ADMIN_IDS or 'action' not in context.user_data:
        return
    
    action = context.user_data['action']
    text = update.message.text
    
    if action == 'btn1_text':
        context.user_data['action'] = 'btn1_url'
        context.user_data['temp_text'] = text
        await update.message.reply_text(f"✅ Button 1 text set to: *{text}*\n\nNow send URL:", parse_mode='Markdown')
    
    elif action == 'btn1_url':
        update_setting('button1_text', context.user_data.get('temp_text', ''))
        update_setting('button1_url', text)
        context.user_data.clear()
        await update.message.reply_text("✅ Button 1 updated successfully!")
        await admin(update, context)
    
    elif action == 'btn2_text':
        context.user_data['action'] = 'btn2_url'
        context.user_data['temp_text'] = text
        await update.message.reply_text(f"✅ Button 2 text set to: *{text}*\n\nNow send URL:", parse_mode='Markdown')
    
    elif action == 'btn2_url':
        update_setting('button2_text', context.user_data.get('temp_text', ''))
        update_setting('button2_url', text)
        context.user_data.clear()
        await update.message.reply_text("✅ Button 2 updated successfully!")
        await admin(update, context)
    
    elif action == 'continue_text':
        update_setting('continue_text', text)
        context.user_data.clear()
        await update.message.reply_text("✅ Continue button updated successfully!")
        await admin(update, context)
    
    elif action == 'message':
        update_setting('bot_message', text)
        context.user_data.clear()
        await update.message.reply_text("✅ Message updated successfully!")
        await admin(update, context)
    
    elif action == 'broadcast':
        context.user_data.clear()
        await update.message.reply_text("📢 Broadcasting message to all users...")
        
        # Get all users
        users = get_all_users()
        success = 0
        failed = 0
        
        for user_id in users:
            try:
                await context.bot.send_message(chat_id=int(user_id), text=text)
                success += 1
            except:
                failed += 1
        
        await update.message.reply_text(f"✅ Broadcast completed!\n\nSuccess: {success}\nFailed: {failed}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_callback, pattern='^continue$'))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern='^admin_'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    
    print("✅ Bot is running with Broadcast & User Tracking...")
    app.run_polling()

if __name__ == '__main__':
    main()
