import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

# LTC
LTC_WALLET = os.getenv("LTC_WALLET")
LTC_API_URL = "https://api.blockcypher.com/v1/ltc/main"
CHECK_INTERVAL = 60  # Проверка заявок на пополнение (в секундах)
