import telebot
from telebot import types
import random
import json
import os
from time import time , sleep
from datetime import datetime
from pytz import timezone
from logging import getLogger

TOKEN = "YOUR_BOT_TOKEN"

bot = telebot.TeleBot(TOKEN)
logger = getLogger(__name__)
message_tracker = {}
game_state = {}
leaderboard = {}
user_data = {}
ADMIN_USER_IDS = [12345667898] 
USERS_FILE = "users.json"
LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {str(k): v for k, v in data.items()}
    return {}

def save_leaderboard(leaderboard_data):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(leaderboard_data, f, ensure_ascii=False)

leaderboard = load_leaderboard()

bot_start_time = datetime.now(timezone('Asia/Tehran')).timestamp()

def save_user(user_id, username):
    if user_id in ADMIN_USER_IDS:
        return
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except json.JSONDecodeError:
            logger.error("Failed to read users.json, starting with empty list")
    
    if not any(user['id'] == user_id for user in users):
        users.append({"id": user_id, "username": username if username else "ندارد"})
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved user {user_id} to users.json")
        except Exception as e:
            logger.error(f"Error saving user {user_id} to users.json: {e}")

def is_message_valid(message):
    message_time = message.date
    logger.info(f"Checking message timestamp: {message_time} vs bot_start_time: {bot_start_time}")
    if message_time < bot_start_time:
        logger.warning(f"Ignoring old message from user {message.chat.id} sent at {message_time}")
        return False
    return True

def check_rate_limit(user_id):
    current_time = time()
    
    if user_id not in message_tracker:
        message_tracker[user_id] = {'count': 0, 'last_time': current_time, 'temp_block_until': 0}
    
    if current_time < message_tracker[user_id]['temp_block_until']:
        remaining = int(message_tracker[user_id]['temp_block_until'] - current_time)
        return False, f"شما به دلیل ارسال پیام زیاد تا {remaining} ثانیه نمی‌تونید پیام بفرستید 😕"
    
    if current_time - message_tracker[user_id]['last_time'] > 1:
        message_tracker[user_id]['count'] = 0
        message_tracker[user_id]['last_time'] = current_time
    
    message_tracker[user_id]['count'] += 1
    
    if message_tracker[user_id]['count'] > 2:
        message_tracker[user_id]['temp_block_until'] = current_time + 30
        return False, "شما بیش از حد پیام فرستادید! تا ۳۰ ثانیه نمی‌تونید پیام بفرستید 😕"
    
    return True, ""

def send_broadcast(message):
    if not is_message_valid(message):
        return
    user_id = message.chat.id
    if user_id not in ADMIN_USER_IDS:
        return
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except json.JSONDecodeError:
            logger.error("Failed to read users.json")
            bot.send_message(user_id, "❌ خطا در خواندن لیست کاربران!")
            return
    success_count = 0
    for user in users:
        try:
            bot.send_message(user["id"], message.text)
            success_count += 1
            sleep(0.5)
        except Exception as e:
            logger.warning(f"Failed to send broadcast to user {user['id']}: {e}")
            continue
    bot.send_message(user_id, f"پیام به {success_count} کاربر ارسال شد 📢")
    logger.info(f"Broadcast sent to {success_count} users by admin {user_id}")

def init_board(size):
    board = [[0] * size for _ in range(size)]
    add_random_tile(board)
    add_random_tile(board)
    return board

def add_random_tile(board):
    size = len(board)
    empty = [(i, j) for i in range(size) for j in range(size) if board[i][j] == 0]
    if empty:
        i, j = random.choice(empty)
        board[i][j] = random.choice([2, 4])

def get_score(board):
    return max([max(row) for row in board])

def build_game_keyboard(board, user_id):
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
    markup.row(types.InlineKeyboardButton("دیگه نمیخوام بازی کنم ! ", callback_data=f"end_{user_id}"))
    return markup

def move_left(board):
    size = len(board)
    moved = False
    for i in range(size):
        row = [x for x in board[i] if x != 0]
        for j in range(len(row) - 1):
            if row[j] == row[j + 1]:
                row[j] *= 2
                row[j + 1] = 0
                moved = True
        row = [x for x in row if x != 0]
        row += [0] * (size - len(row))
        if board[i] != row:
            moved = True
        board[i] = row
    return moved

def move_right(board):
    size = len(board)
    moved = False
    for i in range(size):
        row = [x for x in board[i] if x != 0]
        for j in range(len(row) - 1, 0, -1):
            if row[j] == row[j - 1]:
                row[j] *= 2
                row[j - 1] = 0
                moved = True
        row = [x for x in row if x != 0]
        row = [0] * (size - len(row)) + row
        if board[i] != row:
            moved = True
        board[i] = row
    return moved

def move_up(board):
    size = len(board)
    board_t = [[board[j][i] for j in range(size)] for i in range(size)]
    moved = move_left(board_t)
    board[:] = [[board_t[j][i] for j in range(size)] for i in range(size)]
    return moved

def move_down(board):
    size = len(board)
    board_t = [[board[j][i] for j in range(size)] for i in range(size)]
    moved = move_right(board_t)
    board[:] = [[board_t[j][i] for j in range(size)] for i in range(size)]
    return moved

def is_game_over(board):
    size = len(board)
    for i in range(size):
        for j in range(size):
            if board[i][j] == 0:
                return False
    for i in range(size):
        for j in range(size - 1):
            if board[i][j] == board[i][j + 1]:
                return False
    for i in range(size - 1):
        for j in range(size):
            if board[i][j] == board[i + 1][j]:
                return False
    return True


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user.first_name
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    save_user(user_id, user)

    welcome_message = (
        f"سلام {user} عزیز! 😊\n"
        f"به ربات بازی 2048 خوش اومدی  ،  نمیدونم چقد با بازی آشنایی  ،  اما اگه از قوانین بازی خیلی نمیدونی روی /rules  کلیک کن تا قوانین بهت نشون داده بشن  \n\n"
        f"همچنین میتونی برای دیدن امتیاز نفرات برتر از دستور /leaderboard 🥇 استفاده کنی\n\n"
        "هر موقع آماده بودی ، روی دکمه شروع بازی بزن تا وارد بازی بشیم"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("شروع بازی 🚀", callback_data="show_levels"))
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(commands=['rules'])
def send_rules(message):
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    rules_message = (
        "🎲 **قوانین و روش بازی ۲۰۴۸** 🎲\n\n"
        "هدف بازی اینه که با جابه‌جا کردن کاشی‌ها، به عدد ۲۰۴۸ برسی!\n"
        "چجوری؟ اینجوری:\n"
        "1️⃣ با دکمه‌های جهت‌دار (↑ ↓ ← →) کاشی‌ها رو حرکت بده.\n"
        "2️⃣ کاشی‌های با عدد یکسان که کنار هم قرار بگیرن، با هم جمع می‌شن (مثلاً ۲+۲=۴).\n"
        "3️⃣ بعد از هر حرکت، یه کاشی جدید (۲ یا ۴) تو جدول ظاهر می‌شه.\n"
        "4️⃣ اگه به ۲۰۴۸ برسی، برنده می‌شی! ولی اگه جدول پر بشه و دیگه حرکتی نداشته باشی، می‌بازی.\n\n"
        "امتیازت هم بزرگ‌ترین عدد تو جدوله! آماده‌ای بهترین خودت رو نشون بدی؟ 😎"
    )
    bot.send_message(message.chat.id, rules_message, parse_mode='Markdown')

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    if not leaderboard:
        bot.send_message(message.chat.id, "هنوز هیچ‌کس امتیازی ثبت نکرده!")
        return
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: (-x[1]["score"], x[1]["time"]))
    message_text = "🏆 **لیدربورد بهترین بازیکنان (۵ نفر اول)** 🏆\n\n"
    for i, (user_id, data) in enumerate(sorted_leaderboard[:5], 1):
        message_text += f"{i}. {data['name']} - امتیاز: {data['score']} | زمان: {data['time']} ثانیه\n"
    bot.send_message(message.chat.id, message_text, parse_mode='Markdown')

@bot.message_handler(commands=['alive'])
def send_alive_status(message):
    bot.send_message(message.chat.id, "I'm alive and kicking! 🤖 2048Bot is here!")


@bot.callback_query_handler(func=lambda call: call.data == "show_levels")
def handle_show_levels(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("آسون (۵×۵)", callback_data="easy"))
    markup.add(types.InlineKeyboardButton("متوسط (۷×۷)", callback_data="medium"))
    markup.add(types.InlineKeyboardButton("سخت (۹×۹)", callback_data="hard"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="میخوای بازی تو چه سطحی باشه ؟ در واقع این میزان بزرگ یا کوچیک بودن جدول بازی رو مشخص میکنه",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id) 

@bot.callback_query_handler(func=lambda call: call.data in ["easy", "medium", "hard"])
def handle_level_selection(call):
    user_id = str(call.from_user.id)
    size = {"easy": 5, "medium": 7, "hard": 9}[call.data]
    game_state[user_id] = {"board": init_board(size), "size": size, "start_time": time()}
    score = get_score(game_state[user_id]["board"])
    elapsed_time = int(time() - game_state[user_id]["start_time"])
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"بازی شروع شد!\nامتیاز: {score} | زمان: {elapsed_time} ثانیه",
        reply_markup=build_game_keyboard(game_state[user_id]["board"], user_id)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tile_") or call.data == "dummy")
def handle_dummy_tiles(call):
    bot.answer_callback_query(call.id, text="این دکمه‌ها نمایشین!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("end_"))
def handle_end_game_prompt(call):
    user_id = str(call.from_user.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("آره", callback_data=f"confirm_end_{user_id}"),
        types.InlineKeyboardButton("نه", callback_data="noop")
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="مطمئنی که میخوای بازی رو تموم بکنی ؟ ",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_end_"))
def handle_confirm_end_game(call):
    user_id = str(call.from_user.id)
    if user_id in game_state:
        score = get_score(game_state[user_id]["board"])
        elapsed_time = int(time() - game_state[user_id]["start_time"])
        user_name = call.from_user.first_name
        
        if user_id not in leaderboard or score > leaderboard[user_id]["score"]:
            leaderboard[user_id] = {"name": user_name, "score": score, "time": elapsed_time}
            save_leaderboard(leaderboard)
        
        del game_state[user_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("بازی جدید", callback_data="new_game"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"بازی تموم شد !\nامتیاز نهایی: {score} | زمان: {elapsed_time} ثانیه",
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, text="اطلاعات بازی شما پیدا نشد.", show_alert=True)
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text'])
def handle_message(message):
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return

@bot.callback_query_handler(func=lambda call: call.data == "noop")
def handle_noop(call):
    user_id = str(call.from_user.id)
    if user_id in game_state:
        board = game_state[user_id]["board"]
        score = get_score(board)
        elapsed_time = int(time() - game_state[user_id]["start_time"])
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"بازی ادامه داره!\nامتیاز: {score} | زمان: {elapsed_time} ثانیه",
            reply_markup=build_game_keyboard(board, user_id)
        )
    else:
        bot.send_message(call.message.chat.id, "برای شروع یک بازی جدید، /start را بزنید.")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "new_game")
def handle_new_game(call):
    user = call.from_user.first_name
    welcome_message = (
        f"سلام دوباره {user} جان! 😍\n"
        "مرسی که برگشتی، یه بازی جدید شروع کنیم؟"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("شروع بازی 🚀", callback_data="show_levels"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=welcome_message,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.endswith("_" + str(call.from_user.id)))
def handle_game_moves(call):
    user_id = str(call.from_user.id)
    
    if user_id not in game_state:
        bot.answer_callback_query(call.id, text="لطفاً یک بازی جدید را شروع کنید.", show_alert=True)
        return

    board = game_state[user_id]["board"]
    moved = False
    
    action = call.data.split('_')[0] 

    if action == "up":
        moved = move_up(board)
    elif action == "left":
        moved = move_left(board)
    elif action == "right":
        moved = move_right(board)
    elif action == "down":
        moved = move_down(board)

    if moved:
        add_random_tile(board)
        score = get_score(board)
        elapsed_time = int(time() - game_state[user_id]["start_time"])
        user_name = call.from_user.first_name

        if 2048 in [num for row in board for num in row]:
            if user_id not in leaderboard or score > leaderboard[user_id]["score"]:
                leaderboard[user_id] = {"name": user_name, "score": score, "time": elapsed_time}
                save_leaderboard(leaderboard)
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("بازی جدید", callback_data="new_game"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"شما برنده شدید! 💥\nامتیاز نهایی: {score} | زمان: {elapsed_time} ثانیه",
                reply_markup=markup
            )
            del game_state[user_id]
        elif is_game_over(board):
            if user_id not in leaderboard or score > leaderboard[user_id]["score"]:
                leaderboard[user_id] = {"name": user_name, "score": score, "time": elapsed_time}
                save_leaderboard(leaderboard)
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("بازی جدید", callback_data="new_game"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"بازی تموم شد، شما باختید! ❌\nامتیاز نهایی: {score} | زمان: {elapsed_time} ثانیه",
                reply_markup=markup
            )
            del game_state[user_id]
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"بازی ادامه داره!\nامتیاز: {score} | زمان: {elapsed_time} ثانیه",
                reply_markup=build_game_keyboard(board, user_id)
            )
    else:
        bot.answer_callback_query(call.id, text="حرکتی امکان‌پذیر نیست! ", show_alert=True)
    
    bot.answer_callback_query(call.id) 

@bot.message_handler(func=lambda message: message.text == "پیام همگانی 📢")
def handle_broadcast(message):
    if not is_message_valid(message):
        return
    user_id = message.chat.id
    if user_id not in ADMIN_USER_IDS:
        bot.send_message(user_id, "این قابلیت فقط برای ادمین‌ها در دسترسه!")
        return
    logger.info(f"Broadcast initiated by admin {user_id}")
    bot.send_message(user_id, "هر پیامی که می‌خوای بنویس تا برای همه کاربران ارسال بشه 📢")
    bot.register_next_step_handler(message, send_broadcast)

def set_bot_commands():
    commands = [
        types.BotCommand("start", "شروع بازی ۲۰۴۸"),
        types.BotCommand("rules", "نمایش قوانین بازی"),
        types.BotCommand("leaderboard", "نمایش لیدربورد بهترین بازیکنان"),
    ]
    bot.set_my_commands(commands)


if __name__ == "__main__":
    set_bot_commands() 
    print("Bot is Starting..")
    bot.polling(non_stop=True)