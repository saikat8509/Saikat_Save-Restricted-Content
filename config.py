import os
from urllib.parse import quote_plus

# Bot token from @BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# API ID and Hash from my.telegram.org
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")

# Admin ID for broadcast
ADMINS = int(os.environ.get("ADMINS", "0"))

# MongoDB credentials
MONGO_USERNAME = os.environ.get("MONGO_USERNAME", "")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "")
MONGO_CLUSTER = os.environ.get("MONGO_CLUSTER", "")

# Encode MongoDB credentials
encoded_username = quote_plus(MONGO_USERNAME)
encoded_password = quote_plus(MONGO_PASSWORD)

# Standard MongoDB URI to avoid SRV DNS issues
DB_URI = os.environ.get("DB_URI", f"mongodb://{encoded_username}:{encoded_password}@{MONGO_CLUSTER}:27017/?retryWrites=true&w=majority")
DB_NAME = os.environ.get("DB_NAME", "save_restricted_bot")

# Target channel for forwarding content
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "")

# Enable error messages in user chats
ERROR_MESSAGE = bool(os.environ.get("ERROR_MESSAGE", True))
