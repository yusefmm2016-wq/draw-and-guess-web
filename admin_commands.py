# admin_commands.py
import os
import re
import logging
import html
import asyncio
from types import SimpleNamespace
# استيراد env_loader بدلاً من dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env_file

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    ChatMemberHandler,
    filters,
)
from games.guess_who_game import guess_who_game
from games.draw_and_guess_game import draw_and_guess_game
from database import Database

# load env
load_env_file()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database
db = Database()

# تحميل الإعدادات من config.py
try:
    from config import OWNER_ID, BOT_CHANNEL, WELCOME_IMAGE
except ImportError:
    # إذا لم يوجد config.py، نستخدم القيم الافتراضية
    OWNER_ID = 8171730786
    BOT_CHANNEL = 'https://t.me/T6_wq'
    WELCOME_IMAGE = 'https://via.placeholder.com/800x400.png?text=Welcome'

# Conversation states (keep original numbering)
WAITING_SUGGESTION = 1
WAITING_BROADCAST = 2
WAITING_ADMIN_ID = 3
WAITING_BAN_ID = 4
WAITING_UNBAN_ID = 5
WAITING_REMOVE_ADMIN_ID = 6
WAITING_ADMIN_TITLE = 7
WAITING_CHANNEL = 8
WAITING_ACTIVATION_MESSAGE = 9
WAITING_TWAYQ_MESSAGE = 10

# ------------------------------
# Helpers
# ------------------------------
def chunk_buttons(buttons, chunk_size=2):
    result = []
    for i in range(0, len(buttons), chunk_size):
        result.append(buttons[i:i + chunk_size])
    return result

# ------------------------------
# Start / welcome
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    logger.info(f"🔄 /start command received from user {user.id} ({user.username}) in {chat_type} chat")
    logger.info(f"OWNER_ID: {OWNER_ID}, is_admin: {db.is_admin(user.id) if user.id else False}")

    # ---------------------------------------------
    # 🌟 فحص الروابط العميقة (Deep Links) أولاً 🌟
    # ---------------------------------------------
    if context.args and chat_type == "private":
        payload = context.args[0]
        
        # 1. رابط حزر مين (البادئة: gw_)
        if payload.startswith("gw_"):
            # نقوم بتمرير الوسيط إلى دالة اللعبة (مع إزالة البادئة)
            # يجب تعيين context.args مجدداً
            context.args = [payload.replace("gw_", "")] 
            await guess_who_game.start_command(update, context)
            return
            
        # 2. رابط ارسم وخمن (البادئة: dag_)
        elif payload.startswith("dag_"):
            # نقوم بتمرير الوسيط إلى دالة اللعبة (مع إزالة البادئة)
            # يجب تعيين context.args مجدداً
            context.args = [payload.replace("dag_", "")]
            await draw_and_guess_game.start_private(update, context)
            return
        
    # فحص الحظر العام
    if db.is_globally_banned(user.id):
        await update.message.reply_text("⛔️ للأسف، أنت محظور من استخدام هذا البوت")
        return

    # رسالة خاصة للخاص (Private)
    if chat_type == "private":
        # تسجيل المستخدم
        db.add_user(user.id, user.username, user.first_name, getattr(user, 'last_name', None))

        keyboard = []
        keyboard.append([InlineKeyboardButton("🎮 إضافة للمجموعة", url=f"https://t.me/{context.bot.username}?startgroup=true")])

        # قناة المتابعة
        if BOT_CHANNEL and BOT_CHANNEL != '@YourChannel':
            if BOT_CHANNEL.startswith('@'):
                channel_url = f"https://t.me/{BOT_CHANNEL[1:]}"
            elif BOT_CHANNEL.startswith('http'):
                channel_url = BOT_CHANNEL
            else:
                channel_url = f"https://t.me/{BOT_CHANNEL}"
            keyboard.append([InlineKeyboardButton("📢 تابعنا", url=channel_url)])

        # إضافة زر "شاركنا رأيك" للجميع
        keyboard.append([InlineKeyboardButton("💭 شاركنا رأيك", callback_data="send_suggestion")])
        
        # إضافة زر "مميزات البوت" للجميع
        keyboard.append([InlineKeyboardButton("⭐ مميزات البوت", callback_data="bot_features")])

        # إضافة زر لوحة التحكم للمالك والمشرفين
        is_owner = user.id == OWNER_ID
        is_admin_user = db.is_admin(user.id)
        logger.info(f"User {user.id} - is_owner: {is_owner} (OWNER_ID: {OWNER_ID}), is_admin: {is_admin_user}")
        
        if is_owner or is_admin_user:
            keyboard.append([InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin_panel")])
            logger.info(f"✅ Added admin panel button for user {user.id} (owner: {is_owner}, admin: {is_admin_user})")

        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
مرحباً {html.escape(user.first_name)}! 👋

أنا بوت الألعاب، جايب لك مجموعة روعة من الألعاب المسلية عشان تلعب مع أصدقائك! 🎯

ضيفني لمجموعتك وابدأوا اللعب، أو شاركنا رأيك وأفكارك واحنا بنسمعك 😊

استخدم الأزرار اللي تحت عشان تبدأ معانا 👇
        """

        try:
            # try to send photo with caption
            logger.info(f"Attempting to send welcome photo to user {user.id}")
            await update.message.reply_photo(
                photo=WELCOME_IMAGE,
                caption=welcome_text,
                reply_markup=reply_markup
            )
            logger.info(f"✅ Successfully sent welcome photo to user {user.id}")
        except Exception as e:
            logger.warning(f"Failed to send photo, trying text: {e}")
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )
            logger.info(f"✅ Successfully sent welcome text to user {user.id}")
    
    # معالجة المجموعات (Groups/Supergroups)
    elif chat_type in ["group", "supergroup"]:
        # تسجيل المستخدم فقط (المجموعة تُسجل فقط عند رفع البوت مشرف)
        db.add_user(user.id, user.username, user.first_name, getattr(user, 'last_name', None))
        
        keyboard = []
        
        # إضافة زر لوحة التحكم للمالك والمشرفين في المجموعة
        if user.id == OWNER_ID or db.is_admin(user.id):
            keyboard.append([InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        group_welcome_text = f"""
مرحباً {html.escape(user.first_name)}! 👋

أنا بوت الألعاب المسلية! 🎯

يمكنك اللعب مع أصدقائك في هذه المجموعة باستخدام الألعاب المختلفة.

📝 *الأوامر المتاحة:*
• اكتب `العاب` أو `الألعاب` لعرض قائمة الألعاب
• اكتب `مساعدة` أو `المساعدة` للحصول على المساعدة

🎮 *بعض الألعاب المتاحة:*
• تخمين الأرقام
• اكس او (XO)
• لو خيروك
• وألعاب أخرى...

استمتعوا باللعب! 🎉
        """
        
        try:
            await update.message.reply_text(
                group_welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending start message to group: {e}")
            # محاولة بديلة بدون أزرار
            await update.message.reply_text(
                "🎮 مرحباً! أنا بوت الألعاب. اكتب 'العاب' لرؤية قائمة الألعاب أو 'مساعدة' للمساعدة."
            )

# ------------------------------
# Callback handler (buttons)
# This replaces old admin_panel_handler and expands functionality.
# ------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user = query.from_user
    logger.info(f"🔘 Button handler called with data: '{data}' from user {user.id}")

    # global checks
    if db.is_globally_banned(user.id):
        await query.answer("⛔️ للأسف، أنت محظور من استخدام هذا البوت", show_alert=True)
        return

    if db.is_user_blocked(user.id):
        await query.answer("⛔️ للأسف، ما تقدر تستخدم البوت حالياً", show_alert=True)
        return

    await query.answer()

    # Suggestion - يتم التعامل معه من خلال ConversationHandler مباشرة
    if data == "send_suggestion":
        logger.info(f"Button handler: send_suggestion clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Bot features
    elif data == "bot_features":
        logger.info(f"Button handler: bot_features clicked by user {user.id}")
        features_text = """
⭐ <b>مميزات البوت:</b>

🎮 <b>ألعاب المجموعات:</b>
• 🔢 تخمين الأرقام - لعبة ثنائية تحدي
• 🟡 أربع تربح - لعبة استراتيجية
• ❌ اكس او (XO) - لعبة كلاسيكية
• 🎨 ارسم وخمن - لعبة جماعية
• 🤔 لو خيروك - أسئلة محيرة
• 🧠 أسئلة ثقافية - اختبار معلوماتك
• 👤 حزر مين - لعبة تخمين الشخصيات
• 🔢 طابق الأرقام - لعبة ذاكرة

🎯 <b>ألعاب الخاص:</b>
• /rps أو "حجر ورقة مقص" - حجر ورقة مقص ضد البوت
• /xo أو "اكس او" - اكس او ضد البوت
• /start (مع رابط) - ارسم وخمن (WebApp)

💡 <b>كيفية اللعب:</b>
• في المجموعات: اكتب اسم اللعبة (مثل: "اكس او" أو "تخمين الأرقام")
• في الخاص: استخدم الأوامر (مثل: /rps أو /xo)
• اكتب "العاب" في المجموعة لعرض قائمة الألعاب
• اكتب "مساعدة" للحصول على شرح الألعاب

🎉 استمتعوا باللعب!
        """
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.edit_text(features_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception:
            await query.message.reply_text(features_text, reply_markup=reply_markup, parse_mode='HTML')
        return

    # Back to start (welcome)
    elif data == "back_to_start":
        keyboard = []
        keyboard.append([InlineKeyboardButton("🎮 إضافة للمجموعة", url=f"https://t.me/{context.bot.username}?startgroup=true")])

        if BOT_CHANNEL and BOT_CHANNEL != '@YourChannel':
            if BOT_CHANNEL.startswith('@'):
                channel_url = f"https://t.me/{BOT_CHANNEL[1:]}"
            elif BOT_CHANNEL.startswith('http'):
                channel_url = BOT_CHANNEL
            else:
                channel_url = f"https://t.me/{BOT_CHANNEL}"
            keyboard.append([InlineKeyboardButton("📢 تابعنا", url=channel_url)])

        # إضافة زر "شاركنا رأيك" للجميع
        keyboard.append([InlineKeyboardButton("💭 شاركنا رأيك", callback_data="send_suggestion")])
        
        # إضافة زر "مميزات البوت" للجميع
        keyboard.append([InlineKeyboardButton("⭐ مميزات البوت", callback_data="bot_features")])

        # إضافة زر لوحة التحكم للمالك والمشرفين
        is_owner = user.id == OWNER_ID
        is_admin_user = db.is_admin(user.id)
        logger.info(f"back_to_start: User {user.id} - is_owner: {is_owner} (OWNER_ID: {OWNER_ID}), is_admin: {is_admin_user}")
        
        if is_owner or is_admin_user:
            keyboard.append([InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin_panel")])
            logger.info(f"✅ Added admin panel button for user {user.id} (owner: {is_owner}, admin: {is_admin_user})")

        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
مرحباً {html.escape(user.first_name)}! 👋

أنا بوت الألعاب، جايب لك مجموعة روعة من الألعاب المسلية عشان تلعب مع أصدقائك! 🎯

ضيفني لمجموعتك وابدأوا اللعب، أو شاركنا رأيك وأفكارك واحنا بنسمعك 😊

استخدام الأزرار اللي تحت عشان تبدأ معانا 👇
        """

        try:
            await query.message.edit_text(
                welcome_text,
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )

    # Admin panel
    elif data == "admin_panel":
        logger.info(f"Button handler: admin_panel clicked by user {user.id} (owner: {user.id == OWNER_ID}, admin: {db.is_admin(user.id)})")
        if user.id != OWNER_ID and not db.is_admin(user.id):
            logger.warning(f"User {user.id} tried to access admin panel without permission")
            await query.answer("⛔️ ما عندك صلاحية للدخول هنا", show_alert=True)
            return

        try:
            # استخدام query.edit_message_text مباشرة
            await show_admin_panel(query, user.id)
            logger.info(f"Admin panel shown successfully for user {user.id}")
        except Exception as e:
            logger.error(f"Error showing admin panel for user {user.id}: {e}", exc_info=True)
            await query.answer("❌ حدث خطأ في فتح لوحة الإدارة", show_alert=True)
        return

    # Stats
    elif data == "stats":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'view_stats'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لمشاهدة الإحصائيات")
            return

        stats = db.get_stats()
        text = f"""
📊 <b>إحصائيات البوت:</b>

👥 المستخدمين: {stats.get('users', 0)} مستخدم
👨‍👩‍👧‍👦 المجموعات: {stats.get('groups', 0)} مجموعة
🚫 المحظورين: {stats.get('blocked', 0)} شخص
        """
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # Broadcast menu
    elif data == "broadcast":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'broadcast'):
            await query.message.reply_text("⛔️ ما عندك صلاحية للإذاعة")
            return

        buttons = [
            InlineKeyboardButton("👨‍👩‍👧‍👦 للمجموعات", callback_data="broadcast_groups"),
            InlineKeyboardButton("👥 للمستخدمين", callback_data="broadcast_users"),
            InlineKeyboardButton("📣 للكل", callback_data="broadcast_all")
        ]
        keyboard = chunk_buttons(buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "📢 <b>اختر وين تبي ترسل:</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    elif data.startswith("broadcast_"):
        # ConversationHandler سيتعامل معه مباشرة
        logger.info(f"Button handler: broadcast_ clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Manage admins menu
    elif data == "manage_admins":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'manage_admins'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لإدارة المشرفين")
            return

        buttons = [
            InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin"),
            InlineKeyboardButton("➖ حذف مشرف", callback_data="remove_admin"),
            InlineKeyboardButton("📋 قائمة المشرفين", callback_data="list_admins")
        ]
        keyboard = chunk_buttons(buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "👥 <b>إدارة المشرفين:</b>\n\nاختر اللي تبي تسويه:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # Add admin (start conversation) - ConversationHandler سيتعامل معه مباشرة
    elif data == "add_admin":
        logger.info(f"Button handler: add_admin clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Remove admin (start conversation) - ConversationHandler سيتعامل معه مباشرة
    elif data == "remove_admin":
        logger.info(f"Button handler: remove_admin clicked by user {user.id} - ConversationHandler will handle it")
        return

    # List admins
    elif data == "list_admins":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'view_admins'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لمشاهدة المشرفين")
            return

        admins = db.get_all_admins()

        if not admins:
            text = "📋 ما في مشرفين حالياً"
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="manage_admins")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return

        text = "📋 <b>قائمة المشرفين:</b>\n\n"

        buttons = []
        for admin in admins:
            button_text = f"👤 {admin.get('first_name','')}"
            if admin.get('username'):
                button_text += f" (@{admin['username']})"
            if admin.get('title'):
                button_text += f"\n🏷️ {admin['title']}"
            
            text += f"👤 {html.escape(admin.get('first_name',''))}"
            if admin.get('username'):
                text += f" (@{html.escape(admin['username'])})"
            if admin.get('title'):
                text += f"\n🏷️ <b>اللقب:</b> {html.escape(admin['title'])}"
            if admin.get('added_by'):
                text += f"\n📌 <b>رفعه:</b> المستخدم #{admin['added_by']}"
            text += "\n\n"
            
            buttons.append(InlineKeyboardButton(f"⚙️ {admin.get('first_name','')}", callback_data=f"edit_admin_{admin['user_id']}"))

        keyboard = chunk_buttons(buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="manage_admins")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # Edit admin (open permissions)
    elif data.startswith("edit_admin_"):
        admin_id = int(data.replace("edit_admin_", ""))

        if user.id != OWNER_ID and not db.has_permission(user.id, 'manage_admins'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لتعديل المشرفين")
            return

        admin_info = None
        for admin in db.get_all_admins():
            if admin['user_id'] == admin_id:
                admin_info = admin
                break

        if not admin_info:
            await query.message.edit_text("❌ المشرف غير موجود")
            return

        context.user_data['editing_admin_id'] = admin_id
        context.user_data['admin_permissions'] = admin_info.get('permissions', {}).copy()
        context.user_data['admin_title'] = admin_info.get('title')

        admin_detail_text = f"👤 <b>{html.escape(admin_info.get('first_name',''))}</b>"
        if admin_info.get('username'):
            admin_detail_text += f"\n🔖 @{html.escape(admin_info['username'])}"
        if admin_info.get('title'):
            admin_detail_text += f"\n🏷️ <b>اللقب:</b> {html.escape(admin_info['title'])}"
        if admin_info.get('added_by'):
            admin_detail_text += f"\n📌 <b>رفعه:</b> المستخدم #{admin_info['added_by']}"
        
        admin_detail_text += "\n\n<b>الصلاحيات الحالية:</b>"
        for perm, value in admin_info.get('permissions', {}).items():
            admin_detail_text += f"\n• {perm}: {'✓' if value else '✗'}"
        
        await query.message.edit_text(admin_detail_text, parse_mode='HTML')
        await asyncio.sleep(0.5)
        await show_permissions_menu(query.message, context, is_editing=True)

    # Manage banned menu
    elif data == "manage_banned":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'view_banned'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لمشاهدة المحظورين")
            return

        buttons = [
            InlineKeyboardButton("📋 قائمة المحظورين", callback_data="list_banned"),
            InlineKeyboardButton("منع مستخدم ", callback_data="ban_user"),
            InlineKeyboardButton("الغاء منع مستخدم", callback_data="unban_user")
        ]
        keyboard = chunk_buttons(buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "🚫 <b>إدارة المحظورين:</b>\n\nاختر اللي تبي تسويه:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # List banned users
    elif data == "list_banned":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'view_banned'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لمشاهدة المحظورين")
            return

        blocked = db.get_blocked_users()

        if not blocked:
            text = "📋 ما في مستخدمين محظورين حالياً"
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="manage_banned")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return

        text = "🚫 <b>قائمة المحظورين:</b>\n\n"
        for banned_user in blocked:
            text += f"👤 {html.escape(banned_user.get('first_name',''))}"
            if banned_user.get('username'):
                text += f" (@{html.escape(banned_user['username'])})"
            text += f"\n🆔 الآيدي: <code>{banned_user['user_id']}</code>\n\n"

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="manage_banned")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # Ban user (start conversation) - ConversationHandler سيتعامل معه مباشرة
    elif data == "ban_user":
        logger.info(f"Button handler: ban_user clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Unban user (start conversation) - ConversationHandler سيتعامل معه مباشرة
    elif data == "unban_user":
        logger.info(f"Button handler: unban_user clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Suggestions (view)
    elif data == "suggestions":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'view_suggestions'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لمشاهدة الاقتراحات")
            return

        suggestions = db.get_all_suggestions()

        if not suggestions:
            text = "💭 ما في اقتراحات حالياً"
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return

        text = "💭 <b>الاقتراحات الواردة:</b>\n\n"
        for sug in suggestions[:10]:
            text += f"👤 من: {html.escape(sug['first_name'])}"
            if sug.get('username'):
                text += f" (@{html.escape(sug['username'])})"
            text += f"\n📝 الاقتراح: {html.escape(sug['suggestion_text'])}\n"
            text += f"📅 التاريخ: {sug['created_at']}\n\n"

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # Change channel (owner only) - ConversationHandler سيتعامل معه مباشرة
    elif data == "change_channel":
        logger.info(f"Button handler: change_channel clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Message settings (owner only)
    elif data == "message_settings":
        if user.id != OWNER_ID:
            await query.answer("⛔️ هذه الميزة متاحة للمطور فقط", show_alert=True)
            return
        
        buttons = [
            InlineKeyboardButton("🎉 رسالة التفعيل", callback_data="edit_activation_message"),
            InlineKeyboardButton("📋 رسالة طويق", callback_data="edit_twayq_message"),
        ]
        keyboard = chunk_buttons(buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "📝 <b>إعدادات الرسائل:</b>\n\nاختر الرسالة التي تريد تعديلها:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # Edit activation message (owner only) - ConversationHandler سيتعامل معه مباشرة
    elif data == "edit_activation_message":
        logger.info(f"Button handler: edit_activation_message clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Edit twayq message (owner only) - ConversationHandler سيتعامل معه مباشرة
    elif data == "edit_twayq_message":
        logger.info(f"Button handler: edit_twayq_message clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Manage banning menu
    elif data == "manage_banning":
        if user.id != OWNER_ID and not db.has_permission(user.id, 'view_banned'):
            await query.message.reply_text("⛔️ ما عندك صلاحية لإدارة المنع")
            return

        # ✅ الحصول على عدد الممنوعين عاماً
        global_banned_count = db.get_global_banned_count()
        
        buttons = []
        if user.id == OWNER_ID:
            buttons.append(InlineKeyboardButton("🚫 منع عام", callback_data="ban_global_menu"))
            buttons.append(InlineKeyboardButton("✅ الغاء المنع العام", callback_data="unban_global_menu"))
        buttons.append(InlineKeyboardButton("📋 قائمة المحظورين", callback_data="list_banned"))
        keyboard = chunk_buttons(buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ✅ إضافة الإحصائيات للرسالة
        menu_text = "🚫 <b>إدارة المنع:</b>\n\n"
        if user.id == OWNER_ID:
            menu_text += f"📊 عدد الممنوعين عاماً: <b>{global_banned_count}</b>\n\n"
        menu_text += "اختر اللي تبي تسويه:"
        
        await query.message.edit_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # Ban global menu (owner only) - ConversationHandler سيتعامل معه مباشرة
    elif data == "ban_global_menu":
        logger.info(f"Button handler: ban_global_menu clicked by user {user.id} - ConversationHandler will handle it")
        return

    # Unban global menu (owner only) - ConversationHandler سيتعامل معه مباشرة
    elif data == "unban_global_menu":
        logger.info(f"Button handler: unban_global_menu clicked by user {user.id} - ConversationHandler will handle it")
        return

# ------------------------------
# Admin panel UI
# ------------------------------
async def show_admin_panel(query_or_message, user_id: int):
    is_owner = user_id == OWNER_ID
    logger.info(f"show_admin_panel called for user {user_id}, is_owner: {is_owner}, OWNER_ID: {OWNER_ID}")

    buttons = []

    if is_owner or db.has_permission(user_id, 'view_stats'):
        buttons.append(InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"))

    if is_owner or db.has_permission(user_id, 'broadcast'):
        buttons.append(InlineKeyboardButton("📢 الإذاعة", callback_data="broadcast"))

    if is_owner or db.has_permission(user_id, 'manage_admins'):
        buttons.append(InlineKeyboardButton("👥 إدارة المشرفين", callback_data="manage_admins"))

    if is_owner or db.has_permission(user_id, 'view_banned'):
        buttons.append(InlineKeyboardButton("🚫 إدارة المحظورين", callback_data="manage_banned"))
        buttons.append(InlineKeyboardButton("🚫 المنع", callback_data="manage_banning"))

    if is_owner or db.has_permission(user_id, 'view_suggestions'):
        buttons.append(InlineKeyboardButton("💭 الاقتراحات", callback_data="suggestions"))

    if is_owner:
        buttons.append(InlineKeyboardButton("⚙️ تغيير قناة البداية", callback_data="change_channel"))
        buttons.append(InlineKeyboardButton("📝 إعدادات الرسائل", callback_data="message_settings"))

    keyboard = chunk_buttons(buttons)
    keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_start")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "⚙️ <b>لوحة الإدارة:</b>\n\nاختر القسم اللي تبي تديره:"

    try:
        # إذا كان query (من callback_query)
        if hasattr(query_or_message, 'edit_message_text'):
            await query_or_message.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        # إذا كان message
        elif hasattr(query_or_message, 'edit_text'):
            await query_or_message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            # إذا كانت رسالة عادية، نستخدم reply_text
            await query_or_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}", exc_info=True)
        try:
            # محاولة بديلة
            if hasattr(query_or_message, 'message') and hasattr(query_or_message.message, 'reply_text'):
                await query_or_message.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            elif hasattr(query_or_message, 'reply_text'):
                await query_or_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e2:
            logger.error(f"Error replying admin panel: {e2}", exc_info=True)

# ------------------------------
# Suggestions handling
# ------------------------------
async def receive_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    suggestion_text = update.message.text
    logger.info(f"📝 receive_suggestion: User {user.id} sent suggestion: {suggestion_text[:50]}...")

    suggestion_id = db.add_suggestion(user.id, user.username or 'بدون معرف', user.first_name, suggestion_text)
    logger.info(f"✅ Suggestion saved with ID: {suggestion_id}")

    await update.message.reply_text(
        "✅ <b>تم إرسال اقتراحك بنجاح!</b>\n\nشكراً لك، رأيك يهمنا وبنراجعه قريب 😊",
        parse_mode='HTML'
    )

    # إرسال إشعار للمالك
    if OWNER_ID:
        try:
            notification_text = f"""
🔔 <b>اقتراح جديد وصلك!</b>

👤 من: {html.escape(user.first_name)}"""
            if user.username:
                notification_text += f" (@{html.escape(user.username)})"
            notification_text += f"""
🆔 الآيدي: <code>{user.id}</code>

💭 الاقتراح:
{html.escape(suggestion_text)}

💡 <b>للرد:</b> اسحب الرسالة واكتب ردك عليها
            """
            sent_message = await context.bot.send_message(
                chat_id=OWNER_ID,
                text=notification_text,
                parse_mode='HTML'
            )

            db.update_suggestion_message_id(suggestion_id, sent_message.message_id)

        except Exception as e:
            logger.error(f"Error sending suggestion notification: {e}")

    return ConversationHandler.END

async def handle_suggestion_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != OWNER_ID and not db.is_admin(user.id):
        return

    if not update.message.reply_to_message:
        return

    replied_message_id = update.message.reply_to_message.message_id

    suggestion = db.get_suggestion_by_message_id(replied_message_id)

    if not suggestion:
        return

    reply_text = update.message.text

    try:
        reply_message = f"""
📬 <b>رد على اقتراحك:</b>

💭 اقتراحك كان:
{html.escape(suggestion['suggestion_text'])}

📝 الرد:
{html.escape(reply_text)}
        """

        await context.bot.send_message(
            chat_id=suggestion['user_id'],
            text=reply_message,
            parse_mode='HTML'
        )

        await update.message.reply_text(
            f"✅ تم إرسال ردك إلى {html.escape(suggestion['first_name'])}",
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error sending reply to user: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء إرسال الرد"
        )

# ------------------------------
# Broadcast handling
# ------------------------------
async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_type = context.user_data.get('broadcast_type', 'all')
    message = update.message

    user_success_count = 0
    user_fail_count = 0
    group_success_count = 0
    group_fail_count = 0

    total_users = 0
    total_groups = 0

    if broadcast_type in ['users', 'all']:
        users = db.get_all_users()
        total_users = len(users)
    if broadcast_type in ['groups', 'all']:
        groups = db.get_all_groups()
        total_groups = len(groups)

    total_recipients = total_users + total_groups

    progress_msg = await update.message.reply_text(
        f"⏳ <b>جاري الإرسال...</b>\n\n📊 الإجمالي: {total_recipients}",
        parse_mode='HTML'
    )

    if broadcast_type in ['users', 'all']:
        users_to_send = db.get_all_users()
        for user_id in users_to_send:
            try:
                if message.text:
                    await context.bot.send_message(chat_id=user_id, text=message.text)
                elif message.photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=message.photo[-1].file_id,
                        caption=message.caption if message.caption else None
                    )
                user_success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                user_fail_count += 1
                logger.error(f"Failed to send to user {user_id}: {e}")

    if broadcast_type in ['groups', 'all']:
        groups_to_send = db.get_all_groups()
        for chat_id in groups_to_send:
            try:
                if message.text:
                    await context.bot.send_message(chat_id=chat_id, text=message.text)
                elif message.photo:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=message.photo[-1].file_id,
                        caption=message.caption if message.caption else None
                    )
                group_success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                group_fail_count += 1
                logger.error(f"Failed to send to group {chat_id}: {e}")

    final_message_text = "✅ <b>تمت الإذاعة!</b>\n\n"
    if total_users > 0:
        final_message_text += f"👥 للمستخدمين: نجح {user_success_count} / فشل {user_fail_count}\n"
    if total_groups > 0:
        final_message_text += f"🏘️ للمجموعات: نجح {group_success_count} / فشل {group_fail_count}\n"
    
    total_overall_success = user_success_count + group_success_count
    total_overall_fail = user_fail_count + group_fail_count
    final_message_text += f"\n📊 الإجمالي: نجح {total_overall_success} / فشل {total_overall_fail}"

    await progress_msg.edit_text(
        final_message_text,
        parse_mode='HTML'
    )

    return ConversationHandler.END

# ------------------------------
# Channel change handling
# ------------------------------
async def receive_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_CHANNEL
    new_channel = update.message.text.strip()

    os.environ['BOT_CHANNEL'] = new_channel
    BOT_CHANNEL = new_channel

    await update.message.reply_text(
        f"✅ <b>تم تحديث قناة البداية بنجاح!</b>\n\n🔗 القناة الجديدة: {html.escape(new_channel)}",
        parse_mode='HTML'
    )

    return ConversationHandler.END

async def receive_activation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_message = update.message.text.strip()
    
    db.set_setting('activation_message', new_message)
    
    await update.message.reply_text(
        f"✅ <b>تم تحديث رسالة التفعيل بنجاح!</b>\n\n📝 الرسالة الجديدة:\n{html.escape(new_message)}",
        parse_mode='HTML'
    )
    
    return ConversationHandler.END

async def receive_twayq_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_message = update.message.text.strip()
    
    db.set_setting('twayq_message', new_message)
    
    await update.message.reply_text(
        f"✅ <b>تم تحديث رسالة طويق بنجاح!</b>\n\n📝 الرسالة الجديدة:\n{html.escape(new_message)}",
        parse_mode='HTML'
    )
    
    return ConversationHandler.END

# ------------------------------
# Admin add/remove and permissions UI
# ------------------------------
async def receive_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        admin_id = int(update.message.text.strip())

        context.user_data['pending_admin_id'] = admin_id
        context.user_data['admin_permissions'] = {
            'broadcast': False,
            'view_stats': False,
            'ban': False,
            'unban': False,
            'view_banned': False,
            'view_admins': False,
            'manage_admins': False,
            'view_suggestions': False
        }

        await update.message.reply_text(
            "📝 <b>أدخل اللقب المخصص للمشرف</b>\n\n(أو اكتب 'لا' للتخطي)",
            parse_mode='HTML'
        )
        return WAITING_ADMIN_TITLE

    except ValueError:
        await update.message.reply_text("❌ الرقم مو صحيح! أرسل رقم الآيدي فقط")
        return WAITING_ADMIN_ID

async def receive_admin_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title_text = update.message.text.strip()

    if title_text.lower() in ['لا', 'no', 'skip']:
        context.user_data['admin_title'] = None
    else:
        context.user_data['admin_title'] = title_text

    await show_permissions_menu(update.message, context)

    return ConversationHandler.END

async def show_permissions_menu(message, context, is_editing=False):
    perms = context.user_data.get('admin_permissions', {})

    if is_editing:
        admin_id = context.user_data.get('editing_admin_id')
        text = f"⚙️ <b>تعديل صلاحيات المشرف</b>\n\n🆔 الآيدي: <code>{admin_id}</code>\n\n"
        text += "اختر الصلاحيات اللي تبي تعدلها:\n\n"
    else:
        admin_id = context.user_data.get('pending_admin_id')
        text = f"⚙️ <b>تحديد صلاحيات المشرف</b>\n\n🆔 الآيدي: <code>{admin_id}</code>\n\n"
        text += "اختر الصلاحيات اللي تبي تعطيها للمشرف:\n\n"

    permissions_labels = {
        'broadcast': '📢 الإذاعة',
        'view_stats': '📊 الإحصائيات',
        'ban': '🚫 الحظر',
        'unban': '✅ إلغاء الحظر',
        'view_banned': '👁️ مشاهدة المحظورين',
        'view_admins': '👥 مشاهدة المشرفين',
        'manage_admins': '⚙️ إدارة المشرفين',
        'view_suggestions': '💭 الاقتراحات'
    }

    keyboard = []
    for perm_key, perm_label in permissions_labels.items():
        is_enabled = perms.get(perm_key, False)
        status_icon = "✓" if is_enabled else "✗"
        keyboard.append([
            InlineKeyboardButton(
                f"{perm_label} {status_icon}",
                callback_data=f"perm_toggle_{perm_key}"
            )
        ])
        text += f"{perm_label}: {'✓' if is_enabled else '✗'}\n"

    keyboard.append([InlineKeyboardButton("✅ تأكيد وحفظ", callback_data="perm_confirm")])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="perm_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    except Exception:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def handle_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    is_editing = 'editing_admin_id' in context.user_data

    if not is_editing and 'pending_admin_id' not in context.user_data:
        await query.message.reply_text("❌ في مشكلة، حاول مرة ثانية")
        return

    data = query.data

    if data.startswith("perm_toggle_"):
        perm_key = data.replace("perm_toggle_", "")

        if 'admin_permissions' not in context.user_data:
            context.user_data['admin_permissions'] = {}

        current_value = context.user_data['admin_permissions'].get(perm_key, False)
        context.user_data['admin_permissions'][perm_key] = not current_value

        await show_permissions_menu(query.message, context, is_editing=is_editing)

    elif data == "perm_confirm":
        permissions = context.user_data.get('admin_permissions', {})
        admin_title = context.user_data.get('admin_title')
        added_by = query.from_user.id

        if is_editing:
            admin_id = context.user_data['editing_admin_id']

            try:
                user_info = await context.bot.get_chat(admin_id)
                username = user_info.username if user_info.username else None
                first_name = user_info.first_name if user_info.first_name else f"مستخدم {admin_id}"
                db.add_admin(admin_id, username, first_name, permissions, admin_title, added_by)

                await query.message.edit_text(
                    f"✅ <b>تم تحديث صلاحيات المشرف!</b>\n\n👤 {html.escape(first_name)}\n🆔 الآيدي: <code>{admin_id}</code>",
                    parse_mode='HTML'
                )

                context.user_data.pop('editing_admin_id', None)
                context.user_data.pop('admin_permissions', None)
                context.user_data.pop('admin_title', None)

                await asyncio.sleep(1.5)
                await show_admin_panel(query.message, query.from_user.id)

            except Exception as e:
                # إذا فشل الحصول على معلومات المستخدم، نحاول الحصول على المعلومات من قاعدة البيانات
                logger.warning(f"Could not get chat info for admin {admin_id}: {e}")
                existing_admin = db.get_admin(admin_id)
                if existing_admin:
                    username = existing_admin.get('username')
                    first_name = existing_admin.get('first_name', f"مستخدم {admin_id}")
                else:
                    username = None
                    first_name = f"مستخدم {admin_id}"
                
                db.add_admin(admin_id, username, first_name, permissions, admin_title, added_by)

                await query.message.edit_text(
                    f"✅ <b>تم تحديث صلاحيات المشرف!</b>\n\n👤 {html.escape(first_name)}\n🆔 الآيدي: <code>{admin_id}</code>",
                    parse_mode='HTML'
                )

                context.user_data.pop('editing_admin_id', None)
                context.user_data.pop('admin_permissions', None)
                context.user_data.pop('admin_title', None)

                await asyncio.sleep(1.5)
                await show_admin_panel(query.message, query.from_user.id)
        else:
            admin_id = context.user_data['pending_admin_id']

            try:
                user_info = await context.bot.get_chat(admin_id)
                username = user_info.username if user_info.username else None
                first_name = user_info.first_name if user_info.first_name else f"مستخدم {admin_id}"
                db.add_admin(admin_id, username, first_name, permissions, admin_title, added_by)

                await query.message.edit_text(
                    f"✅ <b>تم رفع المشرف بنجاح!</b>\n\n👤 {html.escape(first_name)}\n🆔 الآيدي: <code>{admin_id}</code>",
                    parse_mode='HTML'
                )

                context.user_data.pop('pending_admin_id', None)
                context.user_data.pop('admin_permissions', None)
                context.user_data.pop('admin_title', None)

                await asyncio.sleep(1.5)
                await show_admin_panel(query.message, query.from_user.id)

            except Exception as e:
                # إذا فشل الحصول على معلومات المستخدم، نضيفه بالقيم الافتراضية
                logger.warning(f"Could not get chat info for admin {admin_id}: {e}")
                username = None
                first_name = f"مستخدم {admin_id}"
                db.add_admin(admin_id, username, first_name, permissions, admin_title, added_by)

                await query.message.edit_text(
                    f"✅ <b>تم رفع المشرف بنجاح!</b>\n\n👤 {html.escape(first_name)}\n🆔 الآيدي: <code>{admin_id}</code>\n\n⚠️ <i>ملاحظة: لم يتم الحصول على معلومات المستخدم، تم إضافته بالآيدي فقط</i>",
                    parse_mode='HTML'
                )

                context.user_data.pop('pending_admin_id', None)
                context.user_data.pop('admin_permissions', None)
                context.user_data.pop('admin_title', None)

                await asyncio.sleep(1.5)
                await show_admin_panel(query.message, query.from_user.id)

    elif data == "perm_cancel":
        if is_editing:
            context.user_data.pop('editing_admin_id', None)
            context.user_data.pop('admin_permissions', None)

            await query.message.edit_text(
                "❌ تم إلغاء تعديل الصلاحيات",
                parse_mode='HTML'
            )
        else:
            context.user_data.pop('pending_admin_id', None)
            context.user_data.pop('admin_permissions', None)

            await query.message.edit_text(
                "❌ تم إلغاء إضافة المشرف",
                parse_mode='HTML'
            )

        await asyncio.sleep(1.5)
        await show_admin_panel(query.message, query.from_user.id)

# ------------------------------
# Ban / Unban (conversations & commands)
# ------------------------------
async def receive_ban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج المنع - يدعم الرد على الرسائل"""
    try:
        user = update.effective_user
        chat_id = update.message.chat.id if update.message.chat else None
        
        ban_id = None
        target_username = None
        target_first_name = None
        
        # دعم الرد على الرسائل
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            ban_id = target.id
            target_username = target.username
            target_first_name = target.first_name
        else:
            ban_id = int(update.message.text.strip())
            try:
                user_info = await context.bot.get_chat(ban_id)
                target_username = user_info.username
                target_first_name = user_info.first_name
            except Exception:
                target_username = None
                target_first_name = "مستخدم"

        # ✅ منطق المنع: إذا كان في مجموعة والمستخدم ليس المطور -> منع في المجموعة
        # إذا كان المطور أو في الخاص -> منع عام
        if chat_id and chat_id < 0 and user.id != OWNER_ID:
            # منع في المجموعة (للمشرفين والمطور)
            if db.is_admin(user.id) or user.id == OWNER_ID:
                db.group_ban_user(ban_id, chat_id)
                user_mention = f'<a href="tg://user?id={ban_id}">{html.escape(target_first_name)}</a>'
                await update.message.reply_text(
                    f"✅ تم منع {user_mention} في هذه المجموعة.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("⛔️ ما عندك صلاحية للمنع في هذه المجموعة")
                return ConversationHandler.END
        else:
            # منع عام (للمطور فقط)
            if user.id == OWNER_ID:
                db.global_ban_user(ban_id, target_username, target_first_name)
                user_mention = f'<a href="tg://user?id={ban_id}">{html.escape(target_first_name)}</a>'
                await update.message.reply_text(
                    f"✅ تم منع عام {user_mention}.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("⛔️ المنع العام متاح للمطور فقط")
                return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ الرقم مو صحيح! أرسل رقم الآيدي فقط أو رد على رسالة")
        return WAITING_BAN_ID

    return ConversationHandler.END

async def receive_unban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج إلغاء المنع - يدعم الرد على الرسائل"""
    try:
        user = update.effective_user
        chat_id = update.message.chat.id if update.message.chat else None
        
        unban_id = None
        target_username = None
        target_first_name = None
        
        # دعم الرد على الرسائل
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            unban_id = target.id
            target_username = target.username
            target_first_name = target.first_name
        else:
            unban_id = int(update.message.text.strip())
            try:
                target_info = await context.bot.get_chat(unban_id)
                target_username = target_info.username
                target_first_name = target_info.first_name
            except Exception:
                target_first_name = "مستخدم"

        # ✅ منطق إلغاء المنع: إذا كان في مجموعة والمستخدم ليس المطور -> إلغاء منع في المجموعة
        # إذا كان المطور أو في الخاص -> إلغاء منع عام
        if chat_id and chat_id < 0 and user.id != OWNER_ID:
            # إلغاء المنع في المجموعة (للمشرفين والمطور)
            if db.is_admin(user.id) or user.id == OWNER_ID:
                if db.is_group_banned(unban_id, chat_id):
                    db.group_unban_user(unban_id, chat_id)
                    user_mention = f'<a href="tg://user?id={unban_id}">{html.escape(target_first_name)}</a>'
                    await update.message.reply_text(
                        f"✅ تم الغاء منع {user_mention} في هذه المجموعة.",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ هذا المستخدم غير ممنوع في هذه المجموعة!",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text("⛔️ ما عندك صلاحية لإلغاء المنع في هذه المجموعة")
                return ConversationHandler.END
        else:
            # إلغاء المنع العام (للمطور فقط)
            if user.id == OWNER_ID:
                if db.is_globally_banned(unban_id):
                    db.global_unban_user(unban_id)
                    user_mention = f'<a href="tg://user?id={unban_id}">{html.escape(target_first_name)}</a>'
                    await update.message.reply_text(
                        f"✅ تم الغاء منع عام {user_mention}.",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ هذا المستخدم غير ممنوع عام!",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text("⛔️ إلغاء المنع العام متاح للمطور فقط")
                return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ الرقم مو صحيح! أرسل رقم الآيدي فقط أو رد على رسالة")
        return WAITING_UNBAN_ID

    return ConversationHandler.END

async def receive_remove_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        admin_id = int(update.message.text.strip())

        if not db.is_admin(admin_id):
            await update.message.reply_text("❌ هذا الشخص مو مشرف أصلاً!")
            return ConversationHandler.END

        db.remove_admin(admin_id)

        await update.message.reply_text(
            f"✅ <b>تم حذف المشرف!</b>\n\n🆔 الآيدي: {admin_id}",
            parse_mode='HTML'
        )

    except ValueError:
        await update.message.reply_text("❌ الرقم مو صحيح! أرسل رقم الآيدي فقط")
        return WAITING_REMOVE_ADMIN_ID

    return ConversationHandler.END

# ------------------------------
# Global ban/unban commands (owner)
# ------------------------------
async def global_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منع عام - للمطور فقط (يعمل في المجموعات والخاص)"""
    user = update.effective_user

    if user.id != OWNER_ID:
        await update.message.reply_text("❌ هذا الأمر متاح للمطور فقط")
        return

    target_user_id = None
    target_username = None
    target_first_name = None

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_user_id = target.id
        target_username = target.username
        target_first_name = target.first_name
    elif context.args:
        arg = context.args[0]

        if arg.startswith('@'):
            username_to_search = arg[1:]
            try:
                target_chat = await context.bot.get_chat(f"@{username_to_search}")
                target_user_id = target_chat.id
                target_username = target_chat.username
                target_first_name = target_chat.first_name
            except Exception:
                await update.message.reply_text(
                    f"❌ لم أتمكن من العثور على المستخدم @{username_to_search}\n"
                    "تأكد من أن اليوزرنيم صحيح أو استخدم ID بدلاً منه"
                )
                return

        else:
            try:
                target_user_id = int(arg)
                try:
                    target_info = await context.bot.get_chat(target_user_id)
                    target_username = target_info.username
                    target_first_name = target_info.first_name
                except Exception:
                    target_first_name = "مستخدم"
            except ValueError:
                await update.message.reply_text(
                    "❌ المعرّف غير صحيح!\n"
                    "استخدم معرف رقمي (ID) أو يوزرنيم مثل @username"
                )
                return

    else:
        await update.message.reply_text(
            "❌ طريقة الاستخدام:\n\n"
            "1️⃣ الرد على رسالة الشخص\n"
            "2️⃣ كتابة ID: <code>حظر عام 123456789</code>\n"
            "3️⃣ كتابة اليوزر: <code>حظر عام @username</code>",
            parse_mode='HTML'
        )
        return

    if target_user_id == OWNER_ID:
        await update.message.reply_text("❌ لا يمكنك حظر نفسك!")
        return

    db.global_ban_user(target_user_id, target_username, target_first_name)
    user_mention = f'<a href="tg://user?id={target_user_id}">{html.escape(target_first_name)}</a>'
    ban_text = f"✅ تم منع عام {user_mention}."

    await update.message.reply_text(ban_text, parse_mode='HTML')

async def global_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء منع عام - للمطور فقط (يعمل في المجموعات والخاص)"""
    user = update.effective_user

    if user.id != OWNER_ID:
        await update.message.reply_text("❌ هذا الأمر متاح للمطور فقط")
        return

    target_user_id = None
    target_username = None
    target_first_name = None

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_user_id = target.id
        target_username = target.username
        target_first_name = target.first_name
    elif context.args:
        arg = context.args[0]
        if arg.startswith('@'):
            username_to_search = arg[1:]
            try:
                target_chat = await context.bot.get_chat(f"@{username_to_search}")
                target_user_id = target_chat.id
                target_username = target_chat.username
                target_first_name = target_chat.first_name
            except Exception:
                await update.message.reply_text(
                    f"❌ لم أتمكن من العثور على المستخدم @{username_to_search}\n"
                    "تأكد من أن اليوزرنيم صحيح أو استخدم ID بدلاً منه"
                )
                return
        else:
            try:
                target_user_id = int(arg)
                try:
                    target_info = await context.bot.get_chat(target_user_id)
                    target_username = target_info.username
                    target_first_name = target_info.first_name
                except Exception:
                    target_first_name = "مستخدم"
            except ValueError:
                await update.message.reply_text(
                    "❌ المعرّف غير صحيح!\n"
                    "استخدم معرف رقمي (ID) أو يوزرنيم مثل @username"
                )
                return
    else:
        await update.message.reply_text("❌ استخدم: الغاء منع عام [رد على رسالة أو ID]")
        return

    if not db.is_globally_banned(target_user_id):
        await update.message.reply_text("❌ هذا المستخدم غير محظور عام!")
        return

    db.global_unban_user(target_user_id)
    user_mention = f'<a href="tg://user?id={target_user_id}">{html.escape(target_first_name)}</a>'
    unban_text = f"✅ تم الغاء منع عام {user_mention}."

    await update.message.reply_text(unban_text, parse_mode='HTML')

# ------------------------------
# Short ban/unban (admin/owner)
# ------------------------------
async def ban_user_short(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منع مستخدم في المجموعة الحالية (للمشرفين والمطور)"""
    if not update.message:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    chat_id = chat.id if chat else None
    
    logger.info(f"🔍 ban_user_short called: user={user.id}, chat_id={chat_id}, has_reply={update.message.reply_to_message is not None}")

    # التحقق من الصلاحيات: المشرفين المعينين أو المطور
    if user.id != OWNER_ID and not db.is_admin(user.id):
        logger.warning(f"❌ User {user.id} is not authorized")
        await update.message.reply_text("❌ هذا الأمر متاح للمشرفين والمطور فقط")
        return

    # ✅ إصلاح: المجموعات لها chat_id سالب (أقل من 0)
    # يجب أن يكون في مجموعة (للمشرفين) - المطور يمكنه استخدامه في أي مكان
    if user.id != OWNER_ID:
        if not chat_id or chat_id >= 0:
            logger.warning(f"❌ Command used outside group: chat_id={chat_id}")
            await update.message.reply_text("❌ هذا الأمر يعمل فقط في المجموعات")
            return

    target_user_id = None
    target_username = None
    target_first_name = "مستخدم"

    # ✅ إصلاح: التحقق من الرد على رسالة أولاً
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
        target_user_id = target.id
        target_username = target.username
        target_first_name = target.first_name or "مستخدم"
        logger.info(f"✅ Target from reply: user_id={target_user_id}, name={target_first_name}")
    elif context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith('@'):
            username_to_search = arg[1:]
            try:
                target_chat = await context.bot.get_chat(f"@{username_to_search}")
                target_user_id = target_chat.id
                target_username = target_chat.username
                target_first_name = target_chat.first_name or "مستخدم"
                logger.info(f"✅ Target from username: user_id={target_user_id}, name={target_first_name}")
            except Exception as e:
                logger.error(f"❌ Error getting user by username: {e}")
                await update.message.reply_text("❌ لم أتمكن من العثور على هذا المستخدم")
                return
        else:
            try:
                target_user_id = int(arg)
                try:
                    target_info = await context.bot.get_chat(target_user_id)
                    target_username = target_info.username
                    target_first_name = target_info.first_name or "مستخدم"
                    logger.info(f"✅ Target from ID: user_id={target_user_id}, name={target_first_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not get user info for ID {target_user_id}: {e}")
                    target_first_name = "مستخدم"
            except ValueError:
                logger.error(f"❌ Invalid user ID format: {arg}")
                await update.message.reply_text("❌ استخدم: منع [رد على رسالة أو ID]")
                return
    else:
        logger.warning(f"❌ No target specified: has_reply={update.message.reply_to_message is not None}, args={context.args}")
        await update.message.reply_text("❌ استخدم: منع [رد على رسالة أو ID]")
        return

    if not target_user_id:
        logger.error("❌ target_user_id is None")
        await update.message.reply_text("❌ لم يتم تحديد المستخدم")
        return

    if target_user_id == OWNER_ID:
        await update.message.reply_text("❌ لا يمكن منع المطور")
        return

    # منع في المجموعة فقط (إذا كان في مجموعة) أو منع عام (إذا كان المطور في الخاص)
    if chat_id and chat_id < 0:
        # في مجموعة - منع في المجموعة فقط
        logger.info(f"✅ Group ban: user_id={target_user_id}, chat_id={chat_id}")
        db.group_ban_user(target_user_id, chat_id)
        user_mention = f'<a href="tg://user?id={target_user_id}">{html.escape(target_first_name)}</a>'
        ban_text = f"✅ تم منع {user_mention} في هذه المجموعة."
    elif user.id == OWNER_ID:
        # المطور في الخاص - منع عام
        logger.info(f"✅ Global ban: user_id={target_user_id}")
        db.global_ban_user(target_user_id, target_username, target_first_name)
        user_mention = f'<a href="tg://user?id={target_user_id}">{html.escape(target_first_name)}</a>'
        ban_text = f"✅ تم منع عام {user_mention}."
    else:
        logger.warning(f"❌ Invalid context: chat_id={chat_id}, user_id={user.id}")
        await update.message.reply_text("❌ هذا الأمر يعمل فقط في المجموعات")
        return

    logger.info(f"✅ Ban successful: {ban_text}")
    await update.message.reply_text(ban_text, parse_mode='HTML')

async def unban_user_short(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء منع مستخدم من المجموعة الحالية (للمشرفين والمطور)"""
    user = update.effective_user
    chat_id = update.message.chat.id

    # التحقق من الصلاحيات: المشرفين المعينين أو المطور
    if user.id != OWNER_ID and not db.is_admin(user.id):
        await update.message.reply_text("❌ هذا الأمر متاح للمشرفين والمطور فقط")
        return

    # ✅ إصلاح: المجموعات لها chat_id سالب (أقل من 0)
    # يجب أن يكون في مجموعة (للمشرفين) - المطور يمكنه استخدامه في أي مكان
    if user.id != OWNER_ID:
        if not chat_id or chat_id >= 0:
            await update.message.reply_text("❌ هذا الأمر يعمل فقط في المجموعات")
            return

    target_user_id = None
    target_username = None
    target_first_name = None

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_user_id = target.id
        target_username = target.username
        target_first_name = target.first_name
    elif context.args:
        arg = context.args[0]
        if arg.startswith('@'):
            username_to_search = arg[1:]
            try:
                target_chat = await context.bot.get_chat(f"@{username_to_search}")
                target_user_id = target_chat.id
                target_username = target_chat.username
                target_first_name = target_chat.first_name
            except Exception:
                await update.message.reply_text("❌ لم أتمكن من العثور على هذا المستخدم")
                return
        else:
            try:
                target_user_id = int(arg)
                try:
                    target_info = await context.bot.get_chat(target_user_id)
                    target_username = target_info.username
                    target_first_name = target_info.first_name
                except Exception:
                    target_first_name = "مستخدم"
            except ValueError:
                await update.message.reply_text("❌ المعرف غير صحيح!")
                return
    else:
        await update.message.reply_text(
            "❌ <b>طريقة استخدام أمر إلغاء المنع:</b>\n\n"
            "1️⃣ رد على رسالة الشخص واكتب: <code>الغاء المنع</code>\n"
            "2️⃣ أو اكتب: <code>الغاء المنع @username</code>\n"
            "3️⃣ أو اكتب: <code>الغاء المنع 123456789</code>",
            parse_mode='HTML'
        )
        return

    # إلغاء المنع في المجموعة (إذا كان في مجموعة) أو إلغاء المنع العام (إذا كان المطور في الخاص)
    if chat_id and chat_id < 0:
        # في مجموعة - إلغاء منع في المجموعة
        if db.is_group_banned(target_user_id, chat_id):
            db.group_unban_user(target_user_id, chat_id)
            user_mention = f'<a href="tg://user?id={target_user_id}">{html.escape(target_first_name)}</a>'
            unban_text = f"✅ تم الغاء منع {user_mention} في هذه المجموعة."
        else:
            await update.message.reply_text("❌ هذا المستخدم غير ممنوع في هذه المجموعة!")
            return
    elif user.id == OWNER_ID:
        # المطور في الخاص - إلغاء منع عام
        if db.is_globally_banned(target_user_id):
            db.global_unban_user(target_user_id)
            user_mention = f'<a href="tg://user?id={target_user_id}">{html.escape(target_first_name)}</a>'
            unban_text = f"✅ تم الغاء منع عام {user_mention}."
        else:
            await update.message.reply_text("❌ هذا المستخدم غير ممنوع عام!")
            return
    else:
        await update.message.reply_text("❌ هذا الأمر يعمل فقط في المجموعات")
        return

    await update.message.reply_text(unban_text, parse_mode='HTML')

# ------------------------------
# Arabic text commands handler (shortcut commands using arabic words)
# ------------------------------
from telegram.ext import ApplicationHandlerStop

async def twayq_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر طويق"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip().lower()
    if text not in ["طويق", "طويق"]:
        return
    
    # الحصول على رسالة طويق من قاعدة البيانات
    twayq_message = db.get_setting('twayq_message', 
        '📋 <b>أوامر البوت:</b>\n\n🎮 <b>الألعاب المتاحة:</b>\n• اكتب "العاب" لعرض قائمة الألعاب\n• اكتب "مساعدة" للحصول على المساعدة\n\n🎯 <b>بعض الألعاب:</b>\n• تخمين الأرقام\n• اكس او (XO)\n• لو خيروك\n• ارسم وخمن\n• وألعاب أخرى...\n\nاستمتعوا باللعب! 🎉')
    
    # الحصول على رابط القناة
    channel_link = BOT_CHANNEL
    if channel_link and channel_link != '@YourChannel':
        if channel_link.startswith('@'):
            channel_url = f"https://t.me/{channel_link[1:]}"
        elif channel_link.startswith('http'):
            channel_url = channel_link
        else:
            channel_url = f"https://t.me/{channel_link}"
    else:
        channel_url = None
    
    # إنشاء الأزرار
    keyboard = []
    if channel_url:
        keyboard.append([InlineKeyboardButton("طويق", url=channel_url)])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        twayq_message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def rank_title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أوامر رتبتي/لقبي"""
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    text = update.message.text.strip().lower()
    
    # التحقق من أن النص يحتوي على "رتبتي" أو "لقبي"
    if "رتبتي" not in text and "لقبي" not in text:
        return
    
    # التحقق من إذا كان المستخدم مطور أساسي
    if user.id == OWNER_ID:
        if "رتبتي" in text:
            await update.message.reply_text("🏆 <b>رتبتك:</b> مطور أساسي", parse_mode='HTML')
        elif "لقبي" in text:
            await update.message.reply_text("🏷️ <b>لقبك:</b> مالك البوت", parse_mode='HTML')
        return
    
    # التحقق من إذا كان المستخدم مشرف
    admin_info = db.get_admin(user.id)
    if admin_info:
        if "رتبتي" in text:
            await update.message.reply_text("🏆 <b>رتبتك:</b> مشرف", parse_mode='HTML')
        elif "لقبي" in text:
            title = admin_info.get('title', 'لا يوجد لقب')
            await update.message.reply_text(f"🏷️ <b>لقبك:</b> {html.escape(title)}", parse_mode='HTML')
        return
    
    # إذا لم يكن مطور أو مشرف، لا نرد

async def ban_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أوامر المنع - يعمل مثل رتبتي في المجموعات والخاص"""
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    text = update.message.text.strip()
    chat = update.effective_chat
    chat_id = chat.id if chat else None
    
    logger.info(f"🔍 ban_commands_handler: text='{text}', user={user.id}, chat_id={chat_id}, has_reply={update.message.reply_to_message is not None}")
    
    # التحقق من الصلاحيات
    is_owner = user.id == OWNER_ID
    is_admin = db.is_admin(user.id)
    
    # منع
    if text in ["منع", "منع_"]:
        if is_owner or is_admin:
            logger.info(f"✅ Ban command detected: '{text}' from user {user.id} (owner: {is_owner}, admin: {is_admin}), chat_id={chat_id}")
            try:
                await ban_user_short(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in ban_user_short: {e}", exc_info=True)
                raise ApplicationHandlerStop
        else:
            logger.warning(f"❌ Unauthorized ban attempt: user {user.id}")
        return
    
    # الغاء منع
    elif text in ["الغاء المنع", "الغاء_المنع", "إلغاء المنع", "إلغاء_المنع"]:
        if is_owner or is_admin:
            logger.info(f"✅ Unban command detected: '{text}' from user {user.id} (owner: {is_owner}, admin: {is_admin}), chat_id={chat_id}")
            try:
                await unban_user_short(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in unban_user_short: {e}", exc_info=True)
                raise ApplicationHandlerStop
        else:
            logger.warning(f"❌ Unauthorized unban attempt: user {user.id}")
        return
    
    # منع عام - للمطور فقط
    if is_owner:
        if text in ["حظر عام", "حظر_عام", "منع عام", "منع_عام"]:
            logger.info(f"✅ Global ban command detected: '{text}' from owner {user.id}, chat_id={chat_id}")
            try:
                await global_ban_command(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in global_ban_command: {e}", exc_info=True)
                raise ApplicationHandlerStop
        
        # الغاء منع عام - للمطور فقط
        elif text in ["الغاء حظر عام", "الغاء_حظر_عام", "إلغاء حظر عام", "إلغاء_حظر_عام", "الغاء منع عام", "الغاء_منع_عام"]:
            logger.info(f"✅ Global unban command detected: '{text}' from owner {user.id}, chat_id={chat_id}")
            try:
                await global_unban_command(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in global_unban_command: {e}", exc_info=True)
                raise ApplicationHandlerStop

async def arabic_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text.strip()
    
    # ✅ تجاهل أوامر الألعاب - دع handlers الألعاب تتعامل معها
    game_commands = [
        "اكس اوه", "اكس او", "اكسو",
        "تخمين الأرقام", "تخمين الارقام", "تخمين ارقام", "خمن الارقام", "خمن الأرقام", "خمن ارقام", "تخمين رقم", "خمن رقم", "لعبة تخمين", "لعبة الأرقام",
        "أربع تربح", "اربع تربح",
        "ارسم وخمن", "خمن وارسم",
        "لو خيروك", "لو خيرك", "لخيروك",
        "ثقافة", "ثقافه",
        "حزر مين",
        "طابق الأرقام", "طابق الارقام",
        "العاب", "الالعاب", "الألعاب", "ألعاب",
        "مساعدة", "المساعدة", "المساعده", "مساعده",
    ]
    
    # تحقق من أن النص يبدأ بأحد أوامر الألعاب أو المستخدم العادي
    if any(text.startswith(cmd) or text == cmd for cmd in game_commands):
        return  # دع handlers الألعاب تتعامل معها
    
    # ✅ التحقق من الصلاحيات أولاً
    is_owner = user.id == OWNER_ID
    is_admin = db.is_admin(user.id)
    
    # ✅ معالجة أوامر المنع (مع دعم الرد على الرسائل)
    logger.info(f"🔍 Checking ban commands for text: '{text}' | User: {user.id} | Owner: {is_owner} | Admin: {is_admin}")
    
    # منع (في المجموعة فقط) - للمشرفين والمطور
    if text in ["منع", "منع_"]:
        logger.info(f"✅ Matched 'منع' command")
        if is_owner or is_admin:
            logger.info(f"✅ Ban command authorized: '{text}' from user {user.id} (owner: {is_owner}, admin: {is_admin}), has reply: {update.message.reply_to_message is not None}")
            try:
                await ban_user_short(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in ban_user_short: {e}", exc_info=True)
                raise ApplicationHandlerStop
        else:
            logger.warning(f"❌ Ban command rejected: user {user.id} is not admin/owner (owner: {is_owner}, admin: {is_admin})")
            return

    # الغاء منع (من المجموعة فقط) - للمشرفين والمطور
    elif text in ["الغاء المنع", "الغاء_المنع", "إلغاء المنع", "إلغاء_المنع"]:
        logger.info(f"✅ Matched 'الغاء المنع' command")
        if is_owner or is_admin:
            logger.info(f"✅ Unban command authorized: '{text}' from user {user.id} (owner: {is_owner}, admin: {is_admin}), has reply: {update.message.reply_to_message is not None}")
            try:
                await unban_user_short(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in unban_user_short: {e}", exc_info=True)
                raise ApplicationHandlerStop
        else:
            logger.warning(f"❌ Unban command rejected: user {user.id} is not admin/owner (owner: {is_owner}, admin: {is_admin})")
            return

    # منع عام - للمطور فقط
    if is_owner:
        if text in ["حظر عام", "حظر_عام", "منع عام", "منع_عام"]:
            logger.info(f"✅ Matched 'منع عام' command")
            logger.info(f"✅ Global ban command authorized: '{text}' from owner {user.id}, has reply: {update.message.reply_to_message is not None}")
            try:
                await global_ban_command(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in global_ban_command: {e}", exc_info=True)
                raise ApplicationHandlerStop

        # الغاء منع عام - للمطور فقط
        elif text in ["الغاء حظر عام", "الغاء_حظر_عام", "إلغاء حظر عام", "إلغاء_حظر_عام", "الغاء منع عام", "الغاء_منع_عام"]:
            logger.info(f"✅ Matched 'الغاء منع عام' command")
            logger.info(f"✅ Global unban command authorized: '{text}' from owner {user.id}, has reply: {update.message.reply_to_message is not None}")
            try:
                await global_unban_command(update, context)
                raise ApplicationHandlerStop
            except Exception as e:
                logger.error(f"❌ Error in global_unban_command: {e}", exc_info=True)
                raise ApplicationHandlerStop
    
    # ✅ إذا لم يكن أي من الأوامر أعلاه، نترك handlers الأخرى تتعامل معه
    logger.info(f"Arabic command received: '{text}' from user {user.id} (not a ban command)")

# ------------------------------
# Check messages from globally banned users (filter) + Register users on first use
# ------------------------------
async def check_global_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص الحظر العام والخاص وتسجيل المستخدمين عند أول استخدام - block=False حتى لا يعترض handlers الألعاب"""
    if update.message and update.message.from_user:
        # note: update.message.from_user.id used (not .user_id)
        user_id = update.message.from_user.id
        user = update.message.from_user
        chat_id = update.message.chat.id if update.message.chat else None

        # فحص الحظر العام
        if db.is_globally_banned(user_id):
            logger.info(f"Blocked message from globally banned user {user_id}")
            # ✅ لا نعترض - فقط نسجل
            return
        
        # فحص الحظر الخاص (في المجموعة)
        if chat_id and chat_id < 0 and db.is_group_banned(user_id, chat_id):
            logger.info(f"Blocked message from group-banned user {user_id} in chat {chat_id}")
            # ✅ لا نعترض - فقط نسجل
            return
        
        # تسجيل المستخدم عند أول استخدام (في أي تفاعل) - بدون تكرار
        try:
            db.add_user(user_id, user.username, user.first_name, getattr(user, 'last_name', None))
        except Exception as e:
            logger.error(f"Error registering user {user_id}: {e}")

# ------------------------------
# Cancel helper
# ------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء ✅")
    return ConversationHandler.END

# ------------------------------
# Chat member updates (bot added/removed / private block)
# ------------------------------
async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.my_chat_member:
        status_change = update.my_chat_member
        chat = status_change.chat
        new_status = status_change.new_chat_member.status
        old_status = status_change.old_chat_member.status
        user = status_change.from_user

        if chat.type == 'private':
            if new_status == 'kicked' and old_status == 'member':
                db.block_user(user.id, user.username, user.first_name)
                logger.info(f"User blocked the bot: {user.first_name} ({user.id})")

            elif new_status == 'member' and old_status == 'kicked':
                db.unblock_user(user.id)
                logger.info(f"User unblocked the bot: {user.first_name} ({user.id})")

        elif chat.type in ['group', 'supergroup']:
            # فقط عند رفع البوت مشرف (وليس عند إضافته فقط)
            if new_status == 'administrator' and old_status in ['member', 'left', 'kicked']:
                # إضافة المجموعة للإحصائيات فقط عند رفع البوت مشرف
                db.add_group(chat.id, chat.title, getattr(chat, 'username', None))
                logger.info(f"Bot promoted to admin in group: {chat.title} ({chat.id})")

                # إرسال رسالة التفعيل في المجموعة
                try:
                    activation_message = db.get_setting('activation_message', 
                        '🎉 تم تفعيل البوت بنجاح!\n\nمرحباً بكم في مجموعة الألعاب المسلية! 🎮\n\nيمكنكم الآن الاستمتاع بجميع الألعاب المتاحة.')
                    
                    # الحصول على رابط القناة
                    channel_link = BOT_CHANNEL
                    if channel_link and channel_link != '@YourChannel':
                        if channel_link.startswith('@'):
                            channel_url = f"https://t.me/{channel_link[1:]}"
                        elif channel_link.startswith('http'):
                            channel_url = channel_link
                        else:
                            channel_url = f"https://t.me/{channel_link}"
                    else:
                        channel_url = None
                    
                    # إنشاء الأزرار
                    keyboard = []
                    if channel_url:
                        keyboard.append([InlineKeyboardButton("طويق", url=channel_url)])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                    
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=activation_message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error sending activation message: {e}")

                # إرسال إشعار واحد فقط عند الرفع
                try:
                    await context.bot.send_message(
                        chat_id=OWNER_ID,
                        text=f"🎉 تم رفع البوت مشرف في مجموعة جديدة!\n\n👥 المجموعة: {html.escape(chat.title)}\n🆔 الآيدي: <code>{chat.id}</code>",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error notifying owner: {e}")

            elif new_status in ['left', 'kicked']:
                db.remove_group(chat.id)
                logger.info(f"Bot removed from group: {chat.title} ({chat.id})")

# ------------------------------
# Handler registration helper
# Returns a list of handlers (ConversationHandlers, CallbackQueryHandler, MessageHandler, etc.)
# so the main application can register them easily.
# ------------------------------
def get_admin_handlers():
    # Conversation for suggestions
    async def start_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query:
            await query.answer()
            await query.message.reply_text(
                "💭 <b>شاركنا رأيك:</b>\n\nاكتب لنا اقتراحك أو ملاحظتك، وأكيد بنهتم فيها! 😊",
                parse_mode='HTML'
            )
        return WAITING_SUGGESTION
    
    suggestion_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_suggestion, pattern="^send_suggestion$")],
        states={
            WAITING_SUGGESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_suggestion)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Broadcast conv
    async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        data = query.data
        user = query.from_user
        
        if user.id != OWNER_ID and not db.has_permission(user.id, 'broadcast'):
            await query.answer("⛔️ ما عندك صلاحية للإذاعة", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        broadcast_type = data.split("_")[1]
        context.user_data['broadcast_type'] = broadcast_type
        await query.message.reply_text(
            "📝 <b>اكتب الرسالة اللي تبي ترسلها:</b>\n\nممكن ترسل نص عادي أو صورة مع كلام",
            parse_mode='HTML'
        )
        return WAITING_BROADCAST
    
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^broadcast_")],
        states={
            WAITING_BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, receive_broadcast)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Admin add conv
    async def start_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID and not db.has_permission(user.id, 'manage_admins'):
            await query.answer("⛔️ ما عندك صلاحية لإضافة مشرفين", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🆔 <b>أرسل رقم المعرف (ID) للشخص اللي تبي ترفعه مشرف:</b>",
            parse_mode='HTML'
        )
        return WAITING_ADMIN_ID
    
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_admin, pattern="^add_admin$")],
        states={
            WAITING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id)],
            WAITING_ADMIN_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_title)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Ban conv
    async def start_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID and not db.has_permission(user.id, 'ban'):
            await query.answer("⛔️ ما عندك صلاحية لحظر المستخدمين", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🆔 <b>أرسل رقم المعرف (ID) للشخص اللي تبي تحظره:</b>",
            parse_mode='HTML'
        )
        return WAITING_BAN_ID
    
    ban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ban_user, pattern="^ban_user$")],
        states={
            WAITING_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ban_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Unban conv
    async def start_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID and not db.has_permission(user.id, 'unban'):
            await query.answer("⛔️ ما عندك صلاحية لإلغاء الحظر", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🆔 <b>أرسل رقم المعرف (ID) للشخص اللي تبي تلغي حظره:</b>",
            parse_mode='HTML'
        )
        return WAITING_UNBAN_ID
    
    unban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_unban_user, pattern="^unban_user$")],
        states={
            WAITING_UNBAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_unban_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Remove admin conv
    async def start_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID and not db.has_permission(user.id, 'manage_admins'):
            await query.answer("⛔️ ما عندك صلاحية لحذف مشرفين", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🆔 <b>أرسل رقم المعرف (ID) للمشرف اللي تبي تحذفه:</b>",
            parse_mode='HTML'
        )
        return WAITING_REMOVE_ADMIN_ID
    
    remove_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_admin, pattern="^remove_admin$")],
        states={
            WAITING_REMOVE_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_admin_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Channel change conv (owner only)
    async def start_change_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID:
            await query.answer("⛔️ هذه الميزة متاحة للمطور فقط", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🔗 <b>تغيير قناة البداية:</b>\n\nأرسل رابط القناة الجديد (مثال: https://t.me/T6_wq أو @T6_wq)",
            parse_mode='HTML'
        )
        return WAITING_CHANNEL
    
    channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_change_channel, pattern="^change_channel$")],
        states={
            WAITING_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Activation message conv (owner only)
    async def start_edit_activation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID:
            await query.answer("⛔️ هذه الميزة متاحة للمطور فقط", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        current_message = db.get_setting('activation_message', 
            '🎉 تم تفعيل البوت بنجاح!\n\nمرحباً بكم في مجموعة الألعاب المسلية! 🎮\n\nيمكنكم الآن الاستمتاع بجميع الألعاب المتاحة.')
        await query.message.reply_text(
            f"📝 <b>تعديل رسالة التفعيل:</b>\n\n📄 الرسالة الحالية:\n{html.escape(current_message)}\n\n✏️ أرسل الرسالة الجديدة:",
            parse_mode='HTML'
        )
        return WAITING_ACTIVATION_MESSAGE
    
    activation_message_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_activation_message, pattern="^edit_activation_message$")],
        states={
            WAITING_ACTIVATION_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_activation_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Twayq message conv (owner only)
    async def start_edit_twayq_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID:
            await query.answer("⛔️ هذه الميزة متاحة للمطور فقط", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        current_message = db.get_setting('twayq_message', 
            '📋 <b>أوامر البوت:</b>\n\n🎮 <b>الألعاب المتاحة:</b>\n• اكتب "العاب" لعرض قائمة الألعاب\n• اكتب "مساعدة" للحصول على المساعدة\n\n🎯 <b>بعض الألعاب:</b>\n• تخمين الأرقام\n• اكس او (XO)\n• لو خيروك\n• ارسم وخمن\n• وألعاب أخرى...\n\nاستمتعوا باللعب! 🎉')
        await query.message.reply_text(
            f"📝 <b>تعديل رسالة طويق:</b>\n\n📄 الرسالة الحالية:\n{html.escape(current_message)}\n\n✏️ أرسل الرسالة الجديدة:",
            parse_mode='HTML'
        )
        return WAITING_TWAYQ_MESSAGE
    
    twayq_message_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_twayq_message, pattern="^edit_twayq_message$")],
        states={
            WAITING_TWAYQ_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_twayq_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Ban global conv (owner only)
    async def start_ban_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID:
            await query.answer("⛔️ هذه الميزة متاحة للمطور فقط", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🆔 <b>منع عام:</b>\n\nأرسل رقم المعرف (ID) للشخص اللي تبي تمنعه عام:",
            parse_mode='HTML'
        )
        return WAITING_BAN_ID
    
    ban_global_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ban_global, pattern="^ban_global_menu$")],
        states={
            WAITING_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ban_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    # Unban global conv (owner only)
    async def start_unban_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        user = query.from_user
        
        if user.id != OWNER_ID:
            await query.answer("⛔️ هذه الميزة متاحة للمطور فقط", show_alert=True)
            return ConversationHandler.END
        
        await query.answer()
        await query.message.reply_text(
            "🆔 <b>إلغاء المنع العام:</b>\n\nأرسل رقم المعرف (ID) للشخص اللي تبي تلغي منعه العام:",
            parse_mode='HTML'
        )
        return WAITING_UNBAN_ID
    
    unban_global_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_unban_global, pattern="^unban_global_menu$")],
        states={
            WAITING_UNBAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_unban_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )

    handlers = [
        # CommandHandler("start", start),
        CommandHandler("gban", global_ban_command),
        CommandHandler("ungban", global_unban_command),
        suggestion_conv,
        broadcast_conv,
        admin_conv,
        ban_conv,
        unban_conv,
        remove_admin_conv,
        channel_conv,
        activation_message_conv,
        twayq_message_conv,
        ban_global_conv,
        unban_global_conv,
        CallbackQueryHandler(handle_permissions, pattern="^perm_"),
        # تم نقل معالج button_handler إلى main.py لتجنب التكرار
        # CallbackQueryHandler(button_handler, pattern="^admin_panel$"),
        # CallbackQueryHandler(button_handler, pattern=r"^(back_to_start|stats|...)"),
        # ✅ معالجات النصوص - block=False حتى لا تعترض handlers الألعاب
        MessageHandler(filters.TEXT & filters.REPLY & ~filters.COMMAND, handle_suggestion_reply, block=False),
        MessageHandler(filters.Regex(re.compile("^(طويق)$", re.IGNORECASE)) & filters.ChatType.GROUPS, twayq_command_handler, block=False),
        MessageHandler(filters.Regex(re.compile(".*(رتبتي|لقبي).*", re.IGNORECASE)) & filters.ChatType.GROUPS, rank_title_handler, block=False),
        # ✅ معالج أوامر المنع - يعمل في المجموعات والخاص مثل رتبتي
        MessageHandler(filters.Regex(re.compile("^(منع|منع_|الغاء المنع|الغاء_المنع|إلغاء المنع|إلغاء_المنع|منع عام|منع_عام|حظر عام|حظر_عام|الغاء منع عام|الغاء_منع_عام|الغاء حظر عام|الغاء_حظر_عام|إلغاء حظر عام|إلغاء_حظر_عام)$", re.IGNORECASE)), ban_commands_handler, block=False),
        MessageHandler(filters.TEXT & ~filters.COMMAND, arabic_commands_handler, block=False),
        MessageHandler(filters.ALL, check_global_ban, block=False),
        ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER),
    ]

    return handlers
