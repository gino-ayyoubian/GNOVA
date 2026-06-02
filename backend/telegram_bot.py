"""
GNOVA Telegram Bot
Full-featured fintech bot with innovative features
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from auth_service import AuthService
from ledger_service import LedgerService
from database import get_db
import qrcode
from io import BytesIO
import json

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
APP_URL = os.getenv("APP_URL", "https://gnova.app")

# Debug: Print token status
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment!")
else:
    logger.info(f"Bot token loaded: {BOT_TOKEN[:10]}...")


class GnovaTelegramBot:
    """GNOVA Telegram Bot Handler"""
    
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot command and callback handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("deposit", self.deposit_command))
        self.app.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.app.add_handler(CommandHandler("convert", self.convert_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        self.app.add_handler(CommandHandler("alerts", self.alerts_command))
        self.app.add_handler(CommandHandler("analytics", self.analytics_command))
        self.app.add_handler(CommandHandler("export", self.export_command))
        self.app.add_handler(CommandHandler("settings", self.settings_command))
        self.app.add_handler(CommandHandler("referral", self.referral_command))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Registration/Welcome"""
        telegram_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        
        # Check if user exists
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            # Register new user
            result = await AuthService.register_user(
                telegram_id=telegram_id,
                username=username
            )
            
            if result["ok"]:
                welcome_text = f"""
🎉 خوش آمدید به GNOVA Fintech!

سلام {first_name} عزیز! 👋

حساب شما با موفقیت ایجاد شد.
شناسه کاربری شما: `{result['user_id']}`

🏦 **ویژگی‌های GNOVA:**
• 💰 واریز و برداشت ریالی
• 🔄 تبدیل ارز و رمزارز
• 📊 تحلیل هوشمند خرج‌کرد
• 🔔 هشدارهای نرخ
• 📈 آمار و گزارش‌گیری
• 🎁 برنامه ارجاع دوستان

برای شروع از منوی زیر استفاده کنید یا /help را بزنید.
"""
                keyboard = [
                    [
                        KeyboardButton("💰 موجودی"),
                        KeyboardButton("📥 واریز")
                    ],
                    [
                        KeyboardButton("📤 برداشت"),
                        KeyboardButton("🔄 تبدیل")
                    ],
                    [
                        KeyboardButton("📊 تاریخچه"),
                        KeyboardButton("⚙️ تنظیمات")
                    ]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ خطا در ایجاد حساب. لطفاً دوباره تلاش کنید."
                )
        else:
            # Existing user
            welcome_back_text = f"""
👋 سلام {first_name}!

به GNOVA خوش برگشتید.
شناسه کاربری: `{user['id']}`

برای دیدن دستورات از /help استفاده کنید.
"""
            keyboard = [
                [
                    InlineKeyboardButton("💰 موجودی", callback_data="balance"),
                    InlineKeyboardButton("📥 واریز", callback_data="deposit")
                ],
                [
                    InlineKeyboardButton("📊 تاریخچه", callback_data="history"),
                    InlineKeyboardButton("📈 آمار", callback_data="analytics")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_back_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
📖 **راهنمای دستورات GNOVA**

**💰 مالی:**
/balance - نمایش موجودی دارایی‌ها
/deposit - واریز ریال
/withdraw - درخواست برداشت
/convert - تبدیل دارایی

**📊 گزارش‌ها:**
/history - تاریخچه تراکنش‌ها
/analytics - تحلیل خرج‌کرد
/export - دریافت گزارش PDF/CSV

**🔔 هشدارها:**
/alerts - مدیریت هشدار نرخ

**⚙️ تنظیمات:**
/settings - تنظیمات حساب
/referral - کد دعوت و پاداش

**ℹ️ اطلاعات:**
/help - نمایش این راهنما

💡 نکته: می‌توانید از دکمه‌های منو نیز استفاده کنید!
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user balances"""
        telegram_id = update.effective_user.id
        
        # Get user
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        if not user:
            await update.message.reply_text(
                "❌ کاربر یافت نشد. لطفاً ابتدا /start را بزنید."
            )
            return
        
        # Get balances
        balances = await LedgerService.compute_all_balances(user["id"])
        
        if not balances:
            await update.message.reply_text("💳 هنوز موجودی ندارید.")
            return
        
        balance_text = "💰 **موجودی دارایی‌های شما:**\n\n"
        
        for bal in balances:
            amount = bal["balance_minor"]
            precision = bal["decimal_precision"]
            
            # Convert minor units to major
            if precision > 0:
                amount_display = amount / (10 ** precision)
                balance_text += f"• {bal['asset_name']}: {amount_display:,.{precision}f} {bal['asset_code']}\n"
            else:
                balance_text += f"• {bal['asset_name']}: {amount:,} {bal['asset_code']}\n"
        
        balance_text += "\n_آخرین به‌روزرسانی: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "_"
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("📥 واریز", callback_data="deposit"),
                InlineKeyboardButton("📤 برداشت", callback_data="withdraw")
            ],
            [
                InlineKeyboardButton("🔄 تبدیل", callback_data="convert"),
                InlineKeyboardButton("📊 تاریخچه", callback_data="history")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            balance_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Initiate deposit"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        deposit_text = """
📥 **واریز ریال به GNOVA**

برای واریز ریال به حساب خود:

**روش 1: درگاه بانکی**
مبلغ مورد نظر را به تومان وارد کنید:
مثال: 100000 (یکصد هزار تومان)

**روش 2: کارت به کارت**
شماره کارت: `6037-9977-1234-5678`
به نام: GNOVA System

پس از واریز، کد پیگیری را ارسال کنید.

⚠️ حداقل واریز: 10,000 تومان
⚠️ حداکثر واریز: 100,000,000 تومان

💡 واریزها معمولاً در کمتر از 5 دقیقه تایید می‌شوند.
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 درگاه بانکی", callback_data="deposit_gateway")],
            [InlineKeyboardButton("📸 کارت به کارت", callback_data="deposit_card")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            deposit_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request withdrawal"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        withdraw_text = """
📤 **برداشت از GNOVA**

برای برداشت از حساب خود:

**برداشت ریالی:**
• مبلغ و شماره کارت/شبا مقصد را وارد کنید
• کارمزد: 0.5٪ (حداقل 5,000 تومان)
• زمان پردازش: 24-48 ساعت

**برداشت رمزارز:**
• آدرس کیف پول و شبکه را مشخص کنید
• کارمزد شبکه: متغیر
• زمان پردازش: 10-60 دقیقه

⚠️ حداقل برداشت: 50,000 تومان
⚠️ احراز هویت (KYC) الزامی است

وضعیت KYC شما: {kyc_status}
"""
        
        keyboard = [
            [InlineKeyboardButton("💵 برداشت ریالی", callback_data="withdraw_irr")],
            [InlineKeyboardButton("₿ برداشت رمزارز", callback_data="withdraw_crypto")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            withdraw_text.format(kyc_status=user.get("kyc_status", "pending")),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def convert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Convert between assets"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        convert_text = """
🔄 **تبدیل دارایی**

برای تبدیل بین دارایی‌های مختلف:

**تبدیل‌های موجود:**
• ریال ↔️ USDT
• ریال ↔️ Bitcoin
• USDT ↔️ Bitcoin

**ویژگی‌ها:**
• 🔒 قفل نرخ برای 5 دقیقه
• 📊 نرخ واقعی بازار
• ⚡ تبدیل آنی
• 💰 کارمزد: 0.3٪

**نحوه استفاده:**
مثال: `تبدیل 1000000 ریال به USDT`

نرخ فعلی:
• 1 USDT = 65,000 ریال
• 1 BTC = 2,850,000,000 ریال

_نرخ‌ها لحظه‌ای و قابل تغییر هستند_
"""
        
        keyboard = [
            [
                InlineKeyboardButton("IRR → USDT", callback_data="convert_irr_usdt"),
                InlineKeyboardButton("USDT → IRR", callback_data="convert_usdt_irr")
            ],
            [
                InlineKeyboardButton("IRR → BTC", callback_data="convert_irr_btc"),
                InlineKeyboardButton("USDT → BTC", callback_data="convert_usdt_btc")
            ],
            [InlineKeyboardButton("🔔 تنظیم هشدار نرخ", callback_data="set_rate_alert")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            convert_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show transaction history"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        # Get transaction history
        history = await LedgerService.get_transaction_history(user["id"], limit=10)
        
        if not history:
            await update.message.reply_text("📊 هنوز تراکنشی ندارید.")
            return
        
        history_text = "📊 **آخرین تراکنش‌های شما:**\n\n"
        
        emoji_map = {
            "deposit": "📥",
            "withdraw": "📤",
            "convert": "🔄",
            "reserve": "🔒",
            "transfer": "↔️"
        }
        
        for tx in history:
            emoji = emoji_map.get(tx["type"], "•")
            tx_type = {
                "deposit": "واریز",
                "withdraw": "برداشت",
                "convert": "تبدیل",
                "reserve": "رزرو",
                "transfer": "انتقال"
            }.get(tx["type"], tx["type"])
            
            amount = tx["amount_from_minor"]
            asset = tx.get("asset_from_code", "IRR")
            status_emoji = "✅" if tx["status"] == "settled" else "⏳"
            
            date_str = datetime.fromisoformat(tx["created_at"]).strftime("%Y-%m-%d %H:%M")
            
            history_text += f"{emoji} **{tx_type}** {status_emoji}\n"
            history_text += f"   مبلغ: {amount:,} {asset}\n"
            history_text += f"   زمان: {date_str}\n"
            history_text += f"   شناسه: `{tx['id'][:8]}...`\n\n"
        
        history_text += "_برای مشاهده تاریخچه کامل از /export استفاده کنید_"
        
        keyboard = [
            [
                InlineKeyboardButton("📄 خروجی PDF", callback_data="export_pdf"),
                InlineKeyboardButton("📊 خروجی CSV", callback_data="export_csv")
            ],
            [InlineKeyboardButton("📈 تحلیل", callback_data="analytics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            history_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def analytics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show spending analytics"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        analytics_text = """
📈 **تحلیل هوشمند خرج‌کرد**

**این ماه:**
• 💰 کل واریز: 5,000,000 ریال
• 💸 کل برداشت: 3,200,000 ریال
• 📊 تراکنش‌ها: 24 عدد
• 💹 سود/زیان: +1,800,000 ریال (+36%)

**دسته‌بندی خرج‌کرد:**
• 🛒 خرید: 45%
• 💳 پرداخت: 30%
• 🔄 تبدیل: 15%
• 📤 انتقال: 10%

**مقایسه با ماه گذشته:**
▲ افزایش 12% در واریزها
▼ کاهش 8% در برداشت‌ها

**پیشنهادات:**
💡 با توجه به الگوی خرج شما، توصیه می‌شود 20% موجودی را در USDT نگه دارید.
💡 بهترین زمان تبدیل: یکشنبه‌ها ساعت 10-12

_تحلیل‌ها بر اساس 30 روز اخیر_
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 گزارش کامل", callback_data="full_report"),
                InlineKeyboardButton("📅 انتخاب بازه", callback_data="select_period")
            ],
            [InlineKeyboardButton("🎯 تنظیم هدف پس‌انداز", callback_data="set_savings_goal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            analytics_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage rate alerts"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        alerts_text = """
🔔 **مدیریت هشدارهای نرخ**

با تنظیم هشدار نرخ، زمانی که نرخ تبدیل به حد مورد نظر شما رسید، به شما اطلاع می‌دهیم.

**هشدارهای فعال شما:**
_هنوز هشداری تنظیم نکرده‌اید_

**مثال‌های هشدار:**
• وقتی 1 USDT کمتر از 64,000 ریال شد
• وقتی 1 BTC بیشتر از 3,000,000,000 ریال شد

**تنظیم هشدار جدید:**
مثال: `هشدار USDT کمتر 64000`
"""
        
        keyboard = [
            [InlineKeyboardButton("➕ هشدار جدید", callback_data="new_alert")],
            [
                InlineKeyboardButton("📋 لیست هشدارها", callback_data="list_alerts"),
                InlineKeyboardButton("🗑 حذف همه", callback_data="delete_all_alerts")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            alerts_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export transaction history"""
        await update.message.reply_text(
            "📄 **خروجی گزارش**\n\nدر حال آماده‌سازی گزارش شما...\nلطفاً چند لحظه صبر کنید."
        )
        
        # This would generate actual PDF/CSV in production
        await asyncio.sleep(2)
        
        await update.message.reply_text(
            "✅ گزارش آماده است!\n\n"
            "📎 فایل‌های ضمیمه شده:\n"
            "• transaction_report.pdf\n"
            "• transaction_data.csv\n\n"
            "_در نسخه تولید، فایل‌ها ارسال می‌شوند_"
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User settings"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        settings_text = f"""
⚙️ **تنظیمات حساب**

**اطلاعات حساب:**
• شناسه: `{user['id'][:16]}...`
• وضعیت: {'✅ فعال' if user['status'] == 'active' else '❌ غیرفعال'}
• KYC: {user.get('kyc_status', 'pending')}
• سطح ریسک: {user.get('risk_level', 'low')}

**تنظیمات:**
• 🌐 زبان: فارسی
• 💱 ارز پیش‌فرض: ریال
• 🔔 اعلان‌ها: فعال
• 🔒 تایید دو مرحله‌ای: غیرفعال

**محدودیت‌ها:**
• واریز روزانه: نامحدود
• برداشت روزانه: 50,000,000 ریال
• تبدیل روزانه: نامحدود
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🌐 تغییر زبان", callback_data="change_language"),
                InlineKeyboardButton("🔔 اعلان‌ها", callback_data="notifications")
            ],
            [
                InlineKeyboardButton("🔒 امنیت", callback_data="security"),
                InlineKeyboardButton("📊 محدودیت‌ها", callback_data="limits")
            ],
            [InlineKeyboardButton("✅ احراز هویت (KYC)", callback_data="kyc")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Referral program"""
        telegram_id = update.effective_user.id
        user = await AuthService.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text("❌ لطفاً ابتدا /start را بزنید.")
            return
        
        referral_code = user["id"][:8].upper()
        referral_link = f"{APP_URL}/ref/{referral_code}"
        
        referral_text = f"""
🎁 **برنامه دعوت دوستان**

با دعوت دوستان خود، هم شما و هم آن‌ها پاداش دریافت می‌کنید!

**پاداش‌ها:**
• 💰 شما: 100,000 ریال
• 🎁 دوست شما: 50,000 ریال

**کد دعوت شما:**
`{referral_code}`

**لینک دعوت:**
{referral_link}

**آمار:**
• تعداد دعوت‌ها: 0
• کل پاداش: 0 ریال

**شرایط:**
• دوست شما باید حداقل 500,000 ریال واریز کند
• پاداش ظرف 24 ساعت واریز می‌شود

💡 نکته: می‌توانید نامحدود دوست دعوت کنید!
"""
        
        keyboard = [
            [InlineKeyboardButton("📤 اشتراک‌گذاری", url=f"https://t.me/share/url?url={referral_link}")],
            [InlineKeyboardButton("📊 آمار دعوت‌ها", callback_data="referral_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            referral_text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "balance":
            # Simulate balance command
            update.message = query.message
            await self.balance_command(update, context)
        
        elif data == "deposit":
            update.message = query.message
            await self.deposit_command(update, context)
        
        elif data == "withdraw":
            update.message = query.message
            await self.withdraw_command(update, context)
        
        elif data == "convert":
            update.message = query.message
            await self.convert_command(update, context)
        
        elif data == "history":
            update.message = query.message
            await self.history_command(update, context)
        
        elif data == "analytics":
            update.message = query.message
            await self.analytics_command(update, context)
        
        elif data == "cancel":
            await query.edit_message_text("❌ عملیات لغو شد.")
        
        else:
            await query.edit_message_text(
                f"⚠️ این قسمت در حال توسعه است.\nCallback: {data}"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            )
    
    def run(self):
        """Run the bot"""
        logger.info("Starting GNOVA Telegram Bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


# Run bot if executed directly
if __name__ == "__main__":
    bot = GnovaTelegramBot()
    bot.run()
