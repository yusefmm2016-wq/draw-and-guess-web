# main.py
import asyncio
import logging
import os
import re

# تحميل متغيرات البيئة أولاً
from env_loader import load_env_file
load_env_file()

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import admin_commands
from bot_commands import (
    help_command,
    help_buttons,
    games_command,
    play_buttons,
)
from admin_commands import (
    start,
    get_admin_handlers,
)

from all_handlers import get_all_handlers
from games.would_you_rather_game import would_you_rather_game
from games.quiz_game import quiz_game
from games.guess_who_game import guess_who_game

# استيراد config.py للحصول على التوكن إذا لم يكن في .env
try:
    import config
except ImportError:
    config = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# أولوية قراءة التوكن: .env > config.py > قيمة افتراضية
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN and config and hasattr(config, 'BOT_TOKEN'):
    TOKEN = config.BOT_TOKEN
    logger.info("✅ تم تحميل التوكن من config.py")
elif not TOKEN:
    TOKEN = "8541472223:AAFpXmDXbkAenwJ0muITQQGBB8cnTCMB1V0"
    logger.warning("⚠️  استخدام التوكن الافتراضي - يرجى إضافة BOT_TOKEN في .env أو config.py")
else:
    logger.info("✅ تم تحميل التوكن من .env")

    # PORT من .env أو config.py
    # Replit requires port 5000 for webview to work correctly
    PORT = 5000
    os.environ["PORT"] = "5000"

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


async def initialize_data():
    """تهيئة البيانات الأولية"""
    from database import Database
    db = Database()
    db.initialize_wyr_questions()  # تهيئة 500 سؤال لـ لو خيروك
    db.initialize_quiz_questions()  # تهيئة 500 سؤال ثقافة
    await would_you_rather_game.initialize_wyr_cache()
    await quiz_game.quiz_initializer()
    # بدء Flask قبل Servo Tunnel
    logger.info("🌐 بدء خادم Flask للألعاب...")
    # دمج التطبيقين
    guess_who_game.start_webapp()
    # انتظار قليل لضمان بدء Flask
    import time
    time.sleep(5)  # انتظار أطول لضمان بدء Flask
    logger.info("✅ تم بدء خادم Flask (انتظر 5 ثوانٍ إضافية للتهيئة الكاملة)")

def main() -> None:
    # ✅ إيقاف جميع العمليات السابقة للبوت
    import subprocess
    import time
    print("🛑 إيقاف جميع عمليات البوت السابقة...")
    
    application = Application.builder().token(TOKEN).build()
    logger.info("🚀 بدء تشغيل البوت...")
    
    # إضافة معالج للأخطاء
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الأخطاء"""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    application.add_error_handler(error_handler)
    
    # ------------------ 1. تثبيت معالج /start أولاً ------------------
    application.add_handler(CommandHandler("start", start), group=0)

    # ✅ معالجات الألعاب - بعد معالجات الإدارة
    game_handlers = get_all_handlers()
    logger.info(f"✅ تم تسجيل {len(game_handlers)} معالج للألعاب")
    for handler in game_handlers:
        try:
            application.add_handler(handler, group=1)  # أولوية أقل من الإدارة
        except Exception as e:
            logger.error(f"❌ فشل تسجيل معالج: {e}")
            logger.error(f"   المعالج: {handler}")
    
    
    # معالجات المستخدم العادي (الألعاب والقوائم)
    application.add_handler(
        MessageHandler(
            filters.Regex(re.compile("^(المساعدة|مساعدة|المساعده|مساعده)$")) & filters.ChatType.GROUPS,
            help_command
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(re.compile("^(العاب|الالعاب|الألعاب|ألعاب)$"))
            & filters.ChatType.GROUPS,
            games_command
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            help_buttons, 
            pattern="^(help:)" 
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            play_buttons, 
            pattern="^(play:)" 
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            play_buttons, 
            pattern="^(help:cancel_play)$"
        )
    )
    
    # ✅ تسجيل معالجات ألعاب الخاص أولاً بأولوية عالية (group=0)
    from games.z_old_games import rps, tictactoe
    logger.info("✅ تسجيل معالجات ألعاب الخاص (rps, xo) بأولوية عالية...")
    for handler in rps.get_handlers():
        try:
            # جميع معالجات RPS بأولوية عالية
            application.add_handler(handler, group=0)
            logger.info(f"✅ تم تسجيل معالج RPS: {handler}")
        except Exception as e:
            logger.error(f"❌ فشل تسجيل معالج RPS: {e}")
    
    for handler in tictactoe.get_handlers():
        try:
            # جميع معالجات XO بأولوية عالية
            application.add_handler(handler, group=0)
            logger.info(f"✅ تم تسجيل معالج XO: {handler}")
        except Exception as e:
            logger.error(f"❌ فشل تسجيل معالج XO: {e}")
    
    # ✅ معالجات لوحة الإدارة - ConversationHandlers أولاً في group=0
    admin_handlers = admin_commands.get_admin_handlers()
    logger.info(f"✅ تم تسجيل {len(admin_handlers)} معالج للإدارة")
    for handler in admin_handlers:
        application.add_handler(handler, group=0)  # أولوية عالية
    
    # ✅ معالج أزرار لوحة الإدارة والأزرار العامة - بعد ConversationHandlers
    # ✅ إضافة معالج شامل لجميع الأزرار البسيطة (ليست entry_points)
    application.add_handler(
        CallbackQueryHandler(
            admin_commands.button_handler,
            pattern=r"^(admin_panel|back_to_start|stats|manage_admins|list_admins|manage_banned|list_banned|suggestions|edit_admin_\d+|bot_features|broadcast|manage_banning|ban_global_menu|unban_global_menu|message_settings|edit_activation_message|edit_twayq_message|change_channel|ban_user|unban_user|add_admin|remove_admin|send_suggestion|broadcast_groups|broadcast_users|broadcast_all)$"
        ),
        group=0  # نفس الأولوية - لكن بعد ConversationHandlers
    )
    
    # ✅ إضافة logging لتتبع الرسائل الواردة
    async def message_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log all incoming messages for debugging"""
        if update.message and update.message.text:
            logger.info(f"📨 رسالة: '{update.message.text[:50]}' | Chat: {update.effective_chat.type} | User: {update.effective_user.id}")
    
    application.add_handler(MessageHandler(filters.ALL, message_logger, block=False), group=-1)  # Last handler, lowest priority
    
    # معالج أزرار الصلاحيات
    application.add_handler(
        CallbackQueryHandler(
            admin_commands.handle_permissions,
            pattern=r"^perm_"
        )
    )

    # ✅ تم إضافة admin handlers في الأعلى قبل button_handler


    # -------------- تشغيل البوت --------------
    # تهيئة البيانات أولاً (بدون bot operations)
    asyncio.run(initialize_data())
    
    # نستخدم Polling دائماً في Replit لسهولة التعامل مع خادم Flask للألعاب على المنفذ 5000
    logger.info("🚀 تشغيل البوت على polling mode (المنفذ 5000 مخصص لخادم الألعاب)")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
