from handlers import bot
from database import init_db
from config import logger

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("Starting bot...")
    bot.polling(non_stop=True)
