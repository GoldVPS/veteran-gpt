import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8314580591:AAFNJOlJyvInFO8iCwRXvndV3NZDH4QOhrY')
ADMIN_IDS = [6051704334]  # Your Telegram ID

# Email Configuration (for receiving tokens)
EMAIL_CONFIG = {
    'imap_server': 'imap.gmail.com',
    'imap_port': 993,
    'email': os.getenv('VERIFICATION_EMAIL'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'use_ssl': True
}

# SheerID Configuration
PROGRAM_ID = "690415d58971e73ca187d8c9"
SHEERID_BASE_URL = "https://services.sheerid.com"

# Proxy Configuration
PROXY_FILE = 'proxies.txt'

# Database
DATABASE_PATH = 'bot_data.db'
