import os
from dotenv import load_dotenv
from logging import getLogger

# Load environment variables
load_dotenv()

# Bot token and admin IDs
TOKEN = os.getenv("TOKEN")
ADMIN_USER_IDS = list(map(int, os.getenv("ADMIN_USER_IDS", "").split(","))) if os.getenv("ADMIN_USER_IDS") else []

# Logger instance
logger = getLogger(__name__)
