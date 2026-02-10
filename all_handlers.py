# all_handlers.py

import re
from telegram.ext import MessageHandler, filters
from games.guess_the_numbers_game import guess_the_numbers_game
from games.connect_four_game import connect_four_game
from games.draw_and_guess_game import draw_and_guess_game
from games.xo_game import xo_game
from games.would_you_rather_game import would_you_rather_game
from games.quiz_game import quiz_game
from games.guess_who_game import guess_who_game

# الألعاب القديمة من z_old_games
from games.z_old_games.match_numbers_game.match_numbers_game import (
    start_game as match_numbers_start,
    button_click as match_numbers_click,
    leave_game as match_numbers_leave,
    games as match_numbers_games,
    player_sessions as match_numbers_sessions
)
from games.z_old_games import rps
from games.z_old_games import tictactoe

from telegram import Update
from telegram.ext import ContextTypes


# ------------------------------
# 🛠️ معالج الانسحاب الموحد
# ------------------------------
async def combined_leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # 2. فحص لعبة "تخمين الأرقام"
    if user_id in guess_the_numbers_game.player_sessions and guess_the_numbers_game.player_sessions[user_id]:
        await guess_the_numbers_game.leave_game(update, context)
        return

    # 💡 4. فحص لعبة "أربعة تربح"
    if user_id in connect_four_game.player_sessions:
        await connect_four_game.leave_game(update, context)
        return

    # 5. فحص لعبة "اكس او"
    game_to_leave = None
    for game_id, game in xo_game.games.items():
        if game["player1"]["id"] == user_id or (game.get("player2") and game["player2"]["id"] == user_id): # Safely access player2
            game_to_leave = game
            break

    if game_to_leave:
        await xo_game.leave_game(update, context)
        return

    # 6. فحص لعبة "ارسم وخمن"
    if user_id in draw_and_guess_game.player_sessions:
        await draw_and_guess_game.leave_game(update, context)
        return

    # 7. فحص لعبة "لو خيروك"
    if user_id in would_you_rather_game.player_sessions:
        await would_you_rather_game.leave_game(update, context)
        return

    # 8. فحص لعبة "طابق الأرقام"
    if (chat_id, user_id) in match_numbers_games:
        await match_numbers_leave(update, context)
        return

    # If no game is found to leave
    await update.message.reply_text("أنت لست في أي لعبة حاليًا.")


# ------------------------------
# 🧩 تجميع المعالجات
# ------------------------------
def get_all_handlers():
    handlers_list = []
    handlers_list.extend(guess_the_numbers_game.get_handlers())
    handlers_list.extend(connect_four_game.get_handlers())
    handlers_list.extend(xo_game.get_handlers())
    handlers_list.extend(would_you_rather_game.get_handlers())
    handlers_list.extend(guess_who_game.get_guess_who_handlers())
    handlers_list.extend(quiz_game.get_quiz_handlers())
    handlers_list.extend(draw_and_guess_game.get_handlers())
    
    # الألعاب القديمة من z_old_games
    from games.z_old_games.match_numbers_game.match_numbers_game import get_handlers as match_numbers_handlers
    handlers_list.extend(match_numbers_handlers())
    # ملاحظة: rps و tictactoe يتم تسجيلهما بشكل منفصل في main.py لتجنب التكرار
    # if hasattr(rps, 'get_handlers'):
    #     handlers_list.extend(rps.get_handlers())
    # if hasattr(tictactoe, 'get_handlers'):
    #     handlers_list.extend(tictactoe.get_handlers())
    
    # معالج الانسحاب الموحد
    handlers_list.append(
        MessageHandler(
            filters.Regex(re.compile("^(انسحاب|إلغاء|الغاء)$")) & filters.ChatType.GROUPS,
            combined_leave_game
        )
    )
    return handlers_list