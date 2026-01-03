import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from verifier import VeteranVerifier
from database import Database
from config import BOT_TOKEN, ADMIN_IDS

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize
db = Database()
verifier = VeteranVerifier()

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome *{user.first_name}*!\n\n"
        "🚀 *Veteran Verification Bot*\n"
        "I can help verify your ChatGPT Plus veteran discount.\n\n"
        "📋 *Available Commands:*\n"
        "/verify - Start verification\n"
        "/status - Check verification status\n"
        "/help - Get help\n"
        "/admin - Admin commands (admin only)",
        parse_mode='Markdown'
    )
    db.add_user(user.id, user.username, user.first_name)

# Command: /verify
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Start Verification", callback_data='start_verify')],
        [InlineKeyboardButton("📋 How to get token?", callback_data='how_to_token')],
        [InlineKeyboardButton("⚠️ Requirements", callback_data='requirements')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Veteran Verification Process*\n\n"
        "1. Get your ChatGPT access token\n"
        "2. Provide veteran information\n"
        "3. We handle the verification\n"
        "4. Get your discount!\n\n"
        "Click below to start:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Callback: Start verification
async def start_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 *Step 1: Get ChatGPT Token*\n\n"
        "1. Login to https://chatgpt.com\n"
        "2. Open Developer Tools (F12)\n"
        "3. Go to Console tab\n"
        "4. Type: `fetch('https://chatgpt.com/api/auth/session').then(r => r.json()).then(console.log)`\n"
        "5. Copy the entire JSON output\n\n"
        "⚠️ *IMPORTANT:* Use a disposable account for safety!",
        parse_mode='Markdown'
    )
    
    # Save state
    context.user_data['step'] = 'awaiting_token'
    
    # Ask for token
    await asyncio.sleep(2)
    await query.message.reply_text(
        "📤 *Now paste your ChatGPT session JSON:*\n"
        "(Send the complete JSON starting with `{\"user\":...`)",
        parse_mode='Markdown'
    )

# Handle JSON token
async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('step') != 'awaiting_token':
        return
    
    token_data = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        # Parse token
        import json
        data = json.loads(token_data)
        access_token = data.get('accessToken', '')
        
        if not access_token:
            await update.message.reply_text("❌ Invalid token format!")
            return
        
        # Save token
        db.save_token(user_id, access_token)
        context.user_data['access_token'] = access_token
        context.user_data['step'] = 'awaiting_veteran_info'
        
        # Ask for veteran info
        keyboard = [
            [InlineKeyboardButton("📝 Enter Manually", callback_data='enter_manual')],
            [InlineKeyboardButton("📁 Upload File", callback_data='upload_file')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ *Token received!*\n\n"
            "📋 *Step 2: Veteran Information*\n\n"
            "Format: `FirstName|LastName|Branch|BirthDate|DischargeDate`\n"
            "Example: `JOHN|SMITH|Army|1990-05-15|2025-01-15`\n\n"
            "Choose input method:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except json.JSONDecodeError:
        await update.message.reply_text("❌ Invalid JSON! Please send valid session data.")
    except Exception as e:
        logger.error(f"Token error: {e}")
        await update.message.reply_text("❌ Error processing token.")

# Handle veteran data
async def handle_veteran_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('step') != 'awaiting_veteran_info':
        return
    
    data_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Parse veteran data
    try:
        parts = data_text.split('|')
        if len(parts) != 5:
            raise ValueError("Invalid format")
        
        first_name, last_name, branch, birth_date, discharge_date = parts
        
        # Validate dates
        from datetime import datetime
        datetime.strptime(birth_date, '%Y-%m-%d')
        datetime.strptime(discharge_date, '%Y-%m-%d')
        
        # Save to database
        veteran_id = db.save_veteran(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            branch=branch,
            birth_date=birth_date,
            discharge_date=discharge_date
        )
        
        context.user_data['veteran_id'] = veteran_id
        context.user_data['step'] = 'ready_to_verify'
        
        # Confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Start Verification", callback_data='begin_verification')],
            [InlineKeyboardButton("✏️ Edit Data", callback_data='edit_data')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Veteran Data Saved!*\n\n"
            f"👤 Name: {first_name} {last_name}\n"
            f"🎖️ Branch: {branch}\n"
            f"🎂 Birth: {birth_date}\n"
            f"📅 Discharge: {discharge_date}\n\n"
            f"*Start verification?*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except ValueError as e:
        await update.message.reply_text(
            "❌ *Invalid format!*\n\n"
            "Use: `FirstName|LastName|Branch|BirthDate|DischargeDate`\n"
            "Example: `JOHN|SMITH|Army|1990-05-15|2025-01-15`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Start verification process
async def begin_verification_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    veteran_id = context.user_data.get('veteran_id')
    access_token = context.user_data.get('access_token')
    
    if not all([veteran_id, access_token]):
        await query.edit_message_text("❌ Missing data! Please restart.")
        return
    
    # Get veteran data
    veteran_data = db.get_veteran(veteran_id)
    
    # Update status
    db.update_status(veteran_id, 'processing')
    
    # Send processing message
    message = await query.edit_message_text(
        "🔄 *Starting Verification...*\n\n"
        "⏳ This may take 1-3 minutes\n"
        "📧 Checking email for token...",
        parse_mode='Markdown'
    )
    
    # Run verification in background
    asyncio.create_task(
        run_verification(
            user_id=user_id,
            veteran_id=veteran_id,
            access_token=access_token,
            veteran_data=veteran_data,
            message=message
        )
    )

# Async verification task
async def run_verification(user_id, veteran_id, access_token, veteran_data, message):
    try:
        # Update status
        await message.edit_text("🔄 Step 1: Getting verification ID...")
        
        # Step 1: Get verification ID
        verification_id = verifier.get_verification_id(access_token)
        
        if not verification_id:
            raise Exception("Failed to get verification ID")
        
        await message.edit_text("✅ Step 1: Got verification ID\n🔄 Step 2: Submitting to SheerID...")
        
        # Step 2: Submit to SheerID
        step1 = verifier.submit_military_status(verification_id)
        step2 = verifier.submit_personal_info(verification_id, veteran_data)
        
        await message.edit_text("✅ Step 2: Submitted to SheerID\n🔄 Step 3: Waiting for email token...")
        
        # Step 3: Get email token
        email_token = verifier.wait_for_email_token(timeout=120)
        
        if not email_token:
            raise Exception("Email token not received")
        
        await message.edit_text(f"✅ Step 3: Got token: {email_token}\n🔄 Step 4: Completing verification...")
        
        # Step 4: Complete verification
        result = verifier.submit_email_token(verification_id, email_token)
        
        if result.get('status') == 'approved':
            # Success
            db.update_status(veteran_id, 'approved')
            
            # Send success message
            await message.edit_text(
                "🎉 *VERIFICATION SUCCESSFUL!*\n\n"
                "✅ Your ChatGPT account has been verified as a veteran.\n\n"
                "📝 *Next Steps:*\n"
                "1. Go to: https://chatgpt.com/veterans-claim\n"
                "2. Claim your discount\n"
                "3. Add payment method\n"
                "4. Enjoy ChatGPT Plus!\n\n"
                "⚠️ *Security Tips:*\n"
                "• Change your ChatGPT password\n"
                "• Revoke old sessions\n"
                "• Enable 2FA",
                parse_mode='Markdown'
            )
            
            # Send admin notification
            await send_admin_notification(user_id, veteran_data, 'approved')
            
        else:
            # Failed
            db.update_status(veteran_id, 'failed')
            await message.edit_text(
                f"❌ *Verification Failed*\n\n"
                f"Reason: {result.get('error', 'Unknown')}\n\n"
                f"Possible issues:\n"
                f"• Veteran data not found in database\n"
                f"• Discharge date too old\n"
                f"• IP blocked\n\n"
                f"Try with different data or contact admin.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Verification error: {e}")
        db.update_status(veteran_id, 'error')
        await message.edit_text(f"❌ *Error:* {str(e)}\n\nContact admin for help.")

# Admin notification
async def send_admin_notification(user_id, veteran_data, status):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 *New Verification*\n\n"
                     f"User: {user_id}\n"
                     f"Name: {veteran_data['first_name']} {veteran_data['last_name']}\n"
                     f"Status: {status}\n"
                     f"Time: {datetime.now()}",
                parse_mode='Markdown'
            )
        except:
            pass

# Command: /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    verifications = db.get_user_verifications(user_id)
    
    if not verifications:
        await update.message.reply_text("📭 No verifications found.")
        return
    
    text = "📊 *Your Verifications*\n\n"
    for v in verifications:
        text += f"👤 {v['first_name']} {v['last_name']}\n"
        text += f"🎖️ {v['branch']}\n"
        text += f"📅 {v['discharge_date']}\n"
        text += f"🔄 Status: {v['status'].upper()}\n"
        text += f"⏰ {v['created_at']}\n"
        text += "─" * 20 + "\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# Command: /admin (Admin only)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only!")
        return
    
    stats = db.get_stats()
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data='admin_stats')],
        [InlineKeyboardButton("👥 Users", callback_data='admin_users')],
        [InlineKeyboardButton("✅ Success", callback_data='admin_success')],
        [InlineKeyboardButton("❌ Failed", callback_data='admin_failed')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👑 *Admin Panel*\n\n"
        f"📈 Total Users: {stats['total_users']}\n"
        f"✅ Successful: {stats['approved']}\n"
        f"❌ Failed: {stats['failed']}\n"
        f"🔄 Processing: {stats['processing']}",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Main function
def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(start_verification, pattern='start_verify'))
    application.add_handler(CallbackQueryHandler(begin_verification_process, pattern='begin_verification'))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    # Start bot
    print("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check current step
    step = context.user_data.get('step')
    
    if step == 'awaiting_token':
        await handle_token(update, context)
    elif step == 'awaiting_veteran_info':
        await handle_veteran_data(update, context)

if __name__ == '__main__':
    main()
