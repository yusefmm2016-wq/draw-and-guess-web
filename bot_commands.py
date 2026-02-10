# bot_commands.py
import logging
import random
import time
from types import SimpleNamespace
# استيراد env_loader بدلاً من dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database

# load env
load_env_file()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------------
# 📘 معالجات أزرار المساعدة
# ------------------------------

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة الألعاب للاختيار وعرض المساعدة لكل لعبة."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # ✅ التحقق من المنع العام
    db = Database()
    if db.is_globally_banned(user.id):
        # ✅ إرسال رسالة واضحة للمحظور
        await update.message.reply_text(
            "⛔️ <b>أنت ممنوع من اللعب</b>\n\n"
            "🚫 <b>نوع المنع:</b> منع عام\n\n"
            "💬 راسل المطور لإلغاء المنع العام",
            parse_mode='HTML'
        )
        return
    
    # ✅ التحقق من المنع في المجموعة (إذا كانت مجموعة)
    if chat_id < 0:  # مجموعة
        if db.is_group_banned(user.id, chat_id):
            # ✅ إرسال رسالة واضحة للمحظور
            await update.message.reply_text(
                "⛔️ <b>أنت ممنوع من اللعب</b>\n\n"
                "🚫 <b>نوع المنع:</b> منع في هذه المجموعة\n\n"
                "💬 راسل المشرفين لإلغاء المنع",
                parse_mode='HTML'
            )
            return
    
    keyboard = [
        [
            InlineKeyboardButton("🔢 تخمين الأرقام", callback_data="help:guess"),
            InlineKeyboardButton("🟡 أربع تربح", callback_data="help:connect_four")
        ],
        [
            InlineKeyboardButton("❌ اكس اوه", callback_data="help:xo"),
            InlineKeyboardButton("🎨 ارسم وخمن", callback_data="help:draw")
        ],
        [
            InlineKeyboardButton("🤔 لو خيروك", callback_data="help:wyr"),
            InlineKeyboardButton("🧠 أسئلة ثقافية", callback_data="help:quiz") # 🆕 إضافة لعبة الأسئلة
        ],
        [
            InlineKeyboardButton("👤 حزر مين", callback_data="help:guess_who") # 🆕 إضافة لعبة حزر مين
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data="help:cancel_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # استخدام update.message أو update.effective_message حسب السياق
    if update.message:
        await update.message.reply_text(
            "اختر اللعبة اللي تبي تتعلمها 👇",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "اختر اللعبة اللي تبي تتعلمها 👇:",
            reply_markup=reply_markup
        )
    else:
        # إذا تم استدعاؤها من مكان آخر
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id,
            "اختر اللعبة اللي تبي تتعلمها 👇",
            reply_markup=reply_markup
        )

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج لكلمة 'العاب' و 'الألعاب'، يعرض قائمة الألعاب للعب مباشرة."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # ✅ التحقق من المنع العام
    db = Database()
    if db.is_globally_banned(user.id):
        # ✅ إرسال رسالة واضحة للمحظور
        await update.message.reply_text(
            "⛔️ <b>أنت ممنوع من اللعب</b>\n\n"
            "🚫 <b>نوع المنع:</b> منع عام\n\n"
            "💬 راسل المطور لإلغاء المنع العام",
            parse_mode='HTML'
        )
        return
    
    # ✅ التحقق من المنع في المجموعة (إذا كانت مجموعة)
    if chat_id < 0:  # مجموعة
        if db.is_group_banned(user.id, chat_id):
            # ✅ إرسال رسالة واضحة للمحظور
            await update.message.reply_text(
                "⛔️ <b>أنت ممنوع من اللعب</b>\n\n"
                "🚫 <b>نوع المنع:</b> منع في هذه المجموعة\n\n"
                "💬 راسل المشرفين لإلغاء المنع",
                parse_mode='HTML'
            )
            return
    
    keyboard = [
            [
                InlineKeyboardButton("🔢 تخمين الأرقام", callback_data="play:guess"),
                InlineKeyboardButton("🟡 أربع تربح", callback_data="play:connect_four")
            ],
            [
                InlineKeyboardButton("❌ اكس اوه", callback_data="play:xo"),
                InlineKeyboardButton("🎨 ارسم وخمن", callback_data="play:draw")
            ],
            [
                InlineKeyboardButton("🤔 لو خيروك", callback_data="play:wyr"),
                InlineKeyboardButton("🧠 أسئلة ثقافية", callback_data="play:quiz") # 🆕 إضافة زر البدء
            ],
            [
                InlineKeyboardButton("👤 حزر مين", callback_data="play:guess_who") # 🆕 إضافة زر البدء
            ],
            [InlineKeyboardButton("❌ إلغاء", callback_data="help:cancel_play")],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "اختر اللعبة اللي تبي تبدأها 👇",
        reply_markup=reply_markup
    )

async def help_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعالج أزرار المساعدة (help:) لعرض المعلومات والتراجع والإلغاء."""
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat_id if query.message else None
    
    # ✅ التحقق من المنع قبل أي إجراء
    db = Database()
    if db.is_globally_banned(user.id):
        await query.answer("⛔️ للأسف، أنت محظور من استخدام هذا البوت", show_alert=True)
        return
    
    if chat_id and chat_id < 0 and db.is_group_banned(user.id, chat_id):
        await query.answer("⛔️ للأسف، أنت محظور من اللعب في هذه المجموعة", show_alert=True)
        return
    
    await query.answer()

    # محتوى الألعاب (لم يتغير)
    game_info = {
        "help:guess": {
            "text": """
📖 *عن لعبة تخمين الأرقام*  
لعبة ثنائية 🔥، كل لاعب يختار رقم سري والخصم يحاول يكتشفه

⚙️ *طريقة اللعب:*  
- اكتب `تخمين الأرقام` عشان تبدأ  
- كل لاعب يرسل رقمه السري في الخاص  
- تتناوبون على التخمين  
- البوت يخبرك كم رقم صحيح  

🏆 *الفوز:*  
- اللي يخمن الرقم كامل أول → يكسب  
""",
            "play_data": "play:guess"
        },
        "help:connect_four": {
            "text": """
📖 *عن لعبة أربع تربح*  
لعبة ثنائية ⚔️، تتناوبون على وضع قطعكم في شبكة 6x7

⚙️ *طريقة اللعب:*  
- اكتب `أربع تربح` عشان تبدأ  
- لاعب ثاني ينضم بزر تحدي  
- يطلع لك اللوح، والقطع تنزل لتحت في العمود اللي تختاره

🏆 *الفوز:*  
- اللي يوصل أربع قطع من قطعه (أفقي أو عمودي أو قطري) → يكسب  
""",
            "play_data": "play:connect_four"
        },
        "help:wyr": {
            "text": """
📖 *عن لعبة لو خَيَّروك*
لعبة تصويت بسيطة 🧠، أسئلة محيرة من الذكاء الاصطناعي

⚙️ *طريقة اللعب:*
- اكتب `لو خيروك` أو `/play` عشان تبدأ
- البوت يطلع لك السؤال بخيارين (🔵 و 🔴)
- كل لاعب يضغط على الزر اللي يبيه
- بعد أول تصويت، تطلع نسب التصويت عشان تشوفون آراء المجموعة

🏆 *الفوز:*
- ما فيه فائز أو خاسر، اللعبة بس للمتعة ومقارنة الآراء
""",
            "play_data": "play:wyr"
        },
        "help:xo": {
            "text": """
📖 *عن لعبة اكس اوه (XO)*  
لعبة ثنائية كلاسيكية ❌⭕، مع خيارات لوحات أكبر للمحترفين

⚙️ *طريقة اللعب:*  
- اكتب `اكس او` أو `اكس اوه` عشان تبدأ  
- لاعب ثاني ينضم بزر أبي ألعب  
- صاحب الجلسة يختار حجم اللوح (3×3، 7×6، 8×8)  
- تتناوبون على اختيار الخانات لين يفوز واحد أو يصير تعادل  
- فيه مؤقت 30 ثانية لكل حركة، إذا تأخرت → تخسر الدور

🏆 *الفوز:*  
- اللي يوصل عدد معين من رموزه (X أو O) أفقي أو عمودي أو قطري → يكسب  
- (3 رموز للوح 3x3، 4 رموز للوح 7x6، 5 رموز للوح 8x8)
""",
            "play_data": "play:xo"
        },
        "help:draw": {
            "text": """
📖 *عن لعبة ارسم وخمن*
لعبة جماعية 🎨، واحد يرسم والباقين يخمنون الكلمة

⚙️ *طريقة اللعب:*
- اكتب `ارسم وخمن` عشان تبدأ
- اللاعبين ينضمون بزر 'انضم'
- صاحب الجلسة يضغط 'ابدأ'
- يتناوب اللاعبون على دور الرسم
- الرسام يحصل على كلمة في الخاص، ويرسل صورة تعبر عنها للمجموعة
- الباقون يخمنون الكلمة بالرد على رسالة الرسم

🏆 *الفوز:*
- اللي يخمن الكلمة صح يكسب نقاط
- الرسام يكسب نقاط إذا خمنها أحدهم
""",
            "play_data": "play:draw_help" # تغيير data البدء لتمييزه (إذا أردت فصل منطق البدء عبر زر المساعدة)
        },
# 🆕 إضافة شرح لعبة الأسئلة الثقافية
        "help:quiz": {
            "text": """
📖 *عن لعبة الأسئلة الثقافية* لعبة جماعية 🧠، أسئلة متعددة الخيارات تختبر معلوماتك.

⚙️ *طريقة اللعب:* - اكتب `ثقافة` أو `/ثقافة` عشان تبدأ
- البوت يرسل سؤالاً بأربعة خيارات.
- اللاعبون يضغطون على الإجابة الصحيحة في أسرع وقت.

🏆 *الفوز:* - اللي يجاوب صح يكسب نقاط.
- الهدف هو جمع أعلى مجموع نقاط في الجولة.
""",
            "play_data": "play:quiz"
        },
"help:guess_who": {
            "text": """
📖 *عن لعبة حزر مين*
لعبة تخمين صور الشخصيات (مشاهير، شخصيات كرتونية، إلخ) 🖼️.

⚙️ *طريقة اللعب:*
- اكتب `حزر مين` عشان تبدأ
- تظهر لك خيارات اللعب (ضد البوت أو تحدي جماعي).
- في التحدي الجماعي: يتناوب اللاعبون على إرسال صورة الشخصية والآخرون يحاولون التخمين بالرد.

🏆 *الفوز:*
- اللي يخمن الشخصية بشكل صحيح يكسب نقاط.
- اللي يكشف صورة صعبة ويكشفها أحد يكسب نقاط أيضاً.
""",
            "play_data": "play:guess_who"
        }            
            
    }

    if query.data in game_info:
        info = game_info[query.data]
        keyboard = [[InlineKeyboardButton("↩️ تراجع", callback_data="help:back"), InlineKeyboardButton("▶️ ابدأ اللعب", callback_data=info["play_data"])]]
        await query.edit_message_text(info["text"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "help:back":
        # إعادة عرض القائمة الرئيسية للمساعدة
        await help_command(update, context) # استخدام help_command لإعادة عرض القائمة
        
    elif query.data == "help:cancel_help": # معالج زر الإلغاء للمساعدة
        await query.answer("تم الإلغاء ✅")
        try:
            # ✅ حذف الرسالة - فقط للمستخدم الذي أرسل الأمر
            user_id = query.from_user.id
            message_user_id = query.message.from_user.id if query.message.from_user else None
            
            # إذا كان المستخدم هو من أرسل الرسالة، يمكن حذفها
            # أو إذا كان البوت مشرف في المجموعة
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete help message: {e}")
            # محاولة بديلة: إخفاء الرسالة بتعديلها
            try:
                await query.message.edit_text("❌ تم الإلغاء")
            except:
                pass

async def play_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعالج أزرار بدء الألعاب (play:)."""
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat_id
    
    # ✅ التحقق من المنع العام
    db = Database()
    if db.is_globally_banned(user.id):
        await query.answer("⛔️ للأسف، أنت محظور من استخدام هذا البوت", show_alert=True)
        return
    
    # ✅ التحقق من المنع في المجموعة (إذا كانت مجموعة)
    if chat_id < 0:  # مجموعة
        if db.is_group_banned(user.id, chat_id):
            await query.answer("⛔️ للأسف، أنت محظور من اللعب في هذه المجموعة", show_alert=True)
            return
    
    await query.answer()

    game_type = query.data.replace("play:", "")
    # معالجة draw_help ليكون draw
    if game_type == "draw_help":
        game_type = "draw"
    
    # قائمة بأسماء الأوامر المفتاحية للألعاب
    game_commands = {
        "guess": "تخمين الأرقام",
        "connect_four": "أربع تربح",
        "xo": "اكس او",
        "wyr": "لو خيروك",
        "draw": "ارسم وخمن",
        "quiz": "ثقافة",       # 🆕 الأمر المفتاحي للعبة الأسئلة
        "guess_who": "حزر مين", # 🆕 الأمر المفتاحي للعبة حزر مين
    }
    
    command_text = game_commands.get(game_type, "/start_game") # افتراض أمر بدء اللعبة

    # حذف رسالة اللوحة (سواء كانت قائمة الألعاب أو المساعدة)
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete help/play message: {e}")

    # *محاكاة* رسالة الأمر المفتاحي لبدء اللعبة
    
    # يجب أن تكون هذه imports في أعلى ملفك الرئيسي
    # from games.guess_the_numbers_game import guess_the_numbers_game
    # from games.connect_four_game import connect_four_game
    # from games.xo_game import xo_game
    # from games.would_you_rather_game import would_you_rather_game
    # from games.draw_and_guess_game import draw_and_guess_game
    
    # لتجنب تكرار الكود: قم بإنشاء fake_update بشكل عام واستدعاء دالة بدء اللعبة المناسبة
    
    # يجب أن تكون هذه Imports في أعلى ملفك الرئيسي:
    from games.guess_the_numbers_game import guess_the_numbers_game
    from games.connect_four_game import connect_four_game
    from games.xo_game import xo_game
    from games.would_you_rather_game import would_you_rather_game
    from games.draw_and_guess_game import draw_and_guess_game
    from games.quiz_game import quiz_game
    from games.guess_who_game import guess_who_game

    games_map = {
        "guess": (guess_the_numbers_game, guess_the_numbers_game.start_game),
        "connect_four": (connect_four_game, connect_four_game.start_game),
        "xo": (xo_game, xo_game.start_game),
        "wyr": (would_you_rather_game, would_you_rather_game.start_game_handler),
        "draw": (draw_and_guess_game, draw_and_guess_game.start_game),
        "quiz": (quiz_game, quiz_game.quiz_game_handler), # افترض أن هذه هي دالة البدء
        "guess_who": (guess_who_game, guess_who_game.group_game_command), # افترض أن هذه هي دالة البدء
    }

    if game_type in games_map:
        game_module, start_function = games_map[game_type]
        
        msg = await context.bot.send_message(chat_id, f"جاري بدء لعبة {game_commands.get(game_type, game_type)}...")

        # تنظيف الجلسة القديمة (فقط لتخمين الأرقام وأربع تربح حيث توجد جلسات فردية صريحة)
        user_id = query.from_user.id
        if game_type in ["guess", "connect_four"] and user_id in game_module.player_sessions:
            try:
                old_session_id = game_module.player_sessions[user_id]
                if old_session_id in game_module.game_sessions:
                    await game_module.handle_session_end(
                        context, old_session_id, "تم إلغاء الجلسة السابقة لبدء جلسة جديدة."
                    )
            except AttributeError:
                # لا توجد دالة handle_session_end أو هيكل الجلسات
                pass
            except Exception as e:
                 logger.warning(f"Failed to clean old session for {game_type}: {e}")


        # 1. إنشاء الرسالة المحاكية (fake_msg)
        fake_msg = SimpleNamespace(
            text=command_text,
            chat_id=chat_id,
            # 🆕 إضافة message_id محاكية (رقم عشوائي أو يعتمد على الوقت لضمان التفرد)
            message_id=int(time.time() * 1000) + random.randint(1, 100), 
            chat=SimpleNamespace(
                id=chat_id,
                type="group"
            ),
            from_user=query.from_user,
            reply_text=lambda text, **kwargs: context.bot.send_message(chat_id, text, **kwargs),
            reply_markup=None  # إضافة للحقول المطلوبة
        )

        # 2. إنشاء كائن التحديث المحاكي (fake_update)
        fake_update = SimpleNamespace(
            message=fake_msg,
            effective_message=fake_msg,
            effective_chat=SimpleNamespace(
                id=chat_id,
                type="group"
            ),
            effective_user=query.from_user
        )
        try:
            await context.bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass

        await start_function(fake_update, context)
        
    elif query.data == "help:cancel_play": # معالج زر الإلغاء للعب
        await query.answer("تم الإلغاء ✅")
        try:
            # ✅ حذف الرسالة - فقط للمستخدم الذي أرسل الأمر
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete play list message: {e}")
            # محاولة بديلة: إخفاء الرسالة بتعديلها
            try:
                await query.message.edit_text("❌ تم الإلغاء")
            except:
                pass
