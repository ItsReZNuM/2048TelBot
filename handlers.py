import telebot
from telebot import types
from time import time, sleep
from config import TOKEN, ADMIN_USER_IDS, logger
from database import save_user, get_all_users, get_leaderboard, save_leaderboard_entry
from game import init_board, get_score, add_random_tile, move_up, move_left, move_right, move_down, is_game_over
from utils import is_message_valid, check_rate_limit

bot = telebot.TeleBot(TOKEN)

# Store active games in memory
game_state = {}

def build_game_keyboard(board, user_id):
    """Create inline keyboard for game board"""
    size = len(board)
    markup = types.InlineKeyboardMarkup()
    for i in range(size):
        row_buttons = [types.InlineKeyboardButton(str(board[i][j]) if board[i][j] != 0 else "⚫", callback_data=f"tile_{i}_{j}_{user_id}") for j in range(size)]
        markup.row(*row_buttons)
    markup.row(
        types.InlineKeyboardButton("..........", callback_data="dummy"),
        types.InlineKeyboardButton("↑", callback_data=f"up_{user_id}"),
        types.InlineKeyboardButton("..........", callback_data="dummy")
    )
    markup.row(
        types.InlineKeyboardButton("←", callback_data=f"left_{user_id}"),
        types.InlineKeyboardButton("↓", callback_data=f"down_{user_id}"),
        types.InlineKeyboardButton("→", callback_data=f"right_{user_id}")
    )
    markup.row(types.InlineKeyboardButton("End Game", callback_data=f"end_{user_id}"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_message_valid(message):
        return
    user_id = message.from_user.id
    allowed, error = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error)
        return
    save_user(user_id, message.from_user.first_name)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Start Game 🚀", callback_data="show_levels"))
    bot.send_message(message.chat.id, "Welcome to 2048! Press Start to begin.", reply_markup=markup)

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    if not is_message_valid(message):
        return
    allowed, error = check_rate_limit(message.from_user.id)
    if not allowed:
        bot.send_message(message.from_user.id, error)
        return
    lb = get_leaderboard()
    if not lb:
        bot.send_message(message.chat.id, "No scores yet!")
        return
    sorted_lb = sorted(lb.items(), key=lambda x: (-x[1]['score'], x[1]['time']))
    msg = "🏆 Top Players 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_lb[:5], start=1):
        msg += f"{i}. {data['name']} - Score: {data['score']} | Time: {data['time']}s\n"
    bot.send_message(message.chat.id, msg)

@bot.callback_query_handler(func=lambda call: call.data == "show_levels")
def choose_level(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Easy (5x5)", callback_data="easy"))
    markup.add(types.InlineKeyboardButton("Medium (7x7)", callback_data="medium"))
    markup.add(types.InlineKeyboardButton("Hard (9x9)", callback_data="hard"))
    bot.edit_message_text("Choose your difficulty:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["easy", "medium", "hard"])
def start_game(call):
    size = {"easy": 5, "medium": 7, "hard": 9}[call.data]
    uid = str(call.from_user.id)
    game_state[uid] = {"board": init_board(size), "size": size, "start_time": time()}
    score = get_score(game_state[uid]["board"])
    bot.edit_message_text(f"Game started!\nScore: {score} | Time: 0s",
                          call.message.chat.id, call.message.message_id,
                          reply_markup=build_game_keyboard(game_state[uid]["board"], uid))

@bot.callback_query_handler(func=lambda call: call.data.startswith(("up_", "down_", "left_", "right_")))
def handle_move(call):
    uid = str(call.from_user.id)
    if uid not in game_state:
        bot.answer_callback_query(call.id, text="Start a new game first.", show_alert=True)
        return
    board = game_state[uid]["board"]
    moved = False
    if call.data.startswith("up_"):
        moved = move_up(board)
    elif call.data.startswith("down_"):
        moved = move_down(board)
    elif call.data.startswith("left_"):
        moved = move_left(board)
    elif call.data.startswith("right_"):
        moved = move_right(board)
    if moved:
        add_random_tile(board)
        score = get_score(board)
        elapsed = int(time() - game_state[uid]["start_time"])
        if is_game_over(board):
            save_leaderboard_entry(int(uid), call.from_user.first_name, score, elapsed)
            bot.edit_message_text(f"Game Over! Score: {score} | Time: {elapsed}s",
                                  call.message.chat.id, call.message.message_id)
            del game_state[uid]
        else:
            bot.edit_message_text(f"Score: {score} | Time: {elapsed}s",
                                  call.message.chat.id, call.message.message_id,
                                  reply_markup=build_game_keyboard(board, uid))
    else:
        bot.answer_callback_query(call.id, text="No move possible!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("end_"))
def end_game(call):
    uid = str(call.from_user.id)
    if uid in game_state:
        score = get_score(game_state[uid]["board"])
        elapsed = int(time() - game_state[uid]["start_time"])
        save_leaderboard_entry(int(uid), call.from_user.first_name, score, elapsed)
        bot.edit_message_text(f"Game ended. Score: {score} | Time: {elapsed}s",
                              call.message.chat.id, call.message.message_id)
        del game_state[uid]

@bot.message_handler(func=lambda m: m.text == "Broadcast 📢")
def broadcast(message):
    if message.chat.id not in ADMIN_USER_IDS:
        bot.send_message(message.chat.id, "Admins only!")
        return
    bot.send_message(message.chat.id, "Send the message to broadcast:")
    bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    users = get_all_users()
    count = 0
    for user in users:
        try:
            bot.send_message(user['id'], message.text)
            count += 1
            sleep(0.5)
        except:
            continue
    bot.send_message(message.chat.id, f"Sent to {count} users.")
