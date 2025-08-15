from time import time
from datetime import datetime
from pytz import timezone
from config import logger

# Store rate limit info
message_tracker = {}

# Store bot start time to ignore old messages
bot_start_time = datetime.now(timezone('Asia/Tehran')).timestamp()

def is_message_valid(message):
    """Check if message is newer than bot start time"""
    message_time = message.date
    if message_time < bot_start_time:
        logger.warning(f"Ignoring old message from {message.chat.id}")
        return False
    return True

def check_rate_limit(user_id):
    """
    Limit messages per second per user
    Allows max 2 messages per second,
    blocks for 30 seconds if exceeded
    """
    current_time = time()

    if user_id not in message_tracker:
        message_tracker[user_id] = {'count': 0, 'last_time': current_time, 'temp_block_until': 0}

    if current_time < message_tracker[user_id]['temp_block_until']:
        remaining = int(message_tracker[user_id]['temp_block_until'] - current_time)
        return False, f"You are temporarily blocked for {remaining} seconds due to spam."

    if current_time - message_tracker[user_id]['last_time'] > 1:
        message_tracker[user_id]['count'] = 0
        message_tracker[user_id]['last_time'] = current_time

    message_tracker[user_id]['count'] += 1

    if message_tracker[user_id]['count'] > 2:
        message_tracker[user_id]['temp_block_until'] = current_time + 30
        return False, "You have been blocked for 30 seconds due to spam."

    return True, ""
