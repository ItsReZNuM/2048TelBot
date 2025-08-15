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
    markup.row(types.InlineKeyboardButton("دیگه نمیخوام بازی کنم ! ", callback_data=f"end_{user_id}"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command to welcome the user and initiate the game"""
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
    """Handle /rules command to display game rules"""
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
    """Handle /leaderboard command to show top players"""
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    lb = get_leaderboard()
    if not lb:
        bot.send_message(message.chat.id, "هنوز هیچ‌کس امتیازی ثبت نکرده!")
        return
    sorted_lb = sorted(lb.items(), key=lambda x: (-x[1]["score"], x[1]["time"]))
    message_text = "🏆 **لیدربورد بهترین بازیکنان (۵ نفر اول)** 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_lb[:5], 1):
        message_text += f"{i}. {data['name']} - امتیاز: {data['score']} | زمان: {data['time']} ثانیه\n"
    bot.send_message(message.chat.id, message_text, parse_mode='Markdown')

@bot.message_handler(commands=['alive'])
def send_alive_status(message):
    """Handle /alive command to check bot status"""
    bot.send_message(message.chat.id, "I'm alive and kicking! 🤖 2048Bot is here!")

@bot.callback_query_handler(func=lambda call: call.data == "show_levels")
def handle_show_levels(call):
    """Show difficulty level selection menu"""
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
    """Handle difficulty level selection and start the game"""
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
    """Handle clicks on game board tiles or dummy buttons"""
    bot.answer_callback_query(call.id, text="این دکمه‌ها نمایشین!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("end_"))
def handle_end_game_prompt(call):
    """Prompt user to confirm ending the game"""
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
    """Handle confirmed game end and save score"""
    user_id = str(call.from_user.id)
    if user_id in game_state:
        score = get_score(game_state[user_id]["board"])
        elapsed_time = int(time() - game_state[user_id]["start_time"])
        user_name = call.from_user.first_name
        
        save_leaderboard_entry(int(user_id), user_name, score, elapsed_time)
        
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
    """Handle general text messages with rate limiting"""
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return

@bot.callback_query_handler(func=lambda call: call.data == "noop")
def handle_noop(call):
    """Handle cancellation of game end prompt"""
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
    """Handle starting a new game"""
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
    """Handle game movement actions (up, down, left, right)"""
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
            save_leaderboard_entry(int(user_id), user_name, score, elapsed_time)
            
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
            save_leaderboard_entry(int(user_id), user_name, score, elapsed_time)
            
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
    """Handle broadcast command for admins"""
    if not is_message_valid(message):
        return
    user_id = message.chat.id
    if user_id not in ADMIN_USER_IDS:
        bot.send_message(user_id, "این قابلیت فقط برای ادمین‌ها در دسترسه!")
        return
    logger.info(f"Broadcast initiated by admin {user_id}")
    bot.send_message(user_id, "هر پیامی که می‌خوای بنویس تا برای همه کاربران ارسال بشه 📢")
    bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    """Send broadcast message to all users"""
    if not is_message_valid(message):
        return
    user_id = message.chat.id
    if user_id not in ADMIN_USER_IDS:
        return
    users = get_all_users()
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