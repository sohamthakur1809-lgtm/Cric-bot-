import os

# Telegram Bot Token (Get from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8934574015:AAFBpCbnpaMl3gRUkinljDi8yfQxavJCBpw")

# Admin Configurations
OWNER_ID = 5533367541  # Replace with your actual Telegram ID
ADMIN_IDS = [OWNER_ID, 987654321]
MOD_IDS = []

# Rank Tiers (Rating Points Required)
RANKS = {
    "Bronze": 0,
    "Silver": 500,
    "Gold": 1200,
    "Platinum": 2500,
    "Diamond": 5000,
    "Master": 8000,
    "Inferno Legend": 12000
}

# Timeout Constants (in seconds)
AFK_WARNING = 60
AFK_FINAL_WARNING = 90
AFK_AUTO_OUT = 120
LOBBY_AUTO_START = 60

# Default Embed Images / Media Categories
DEFAULT_MEDIA = {
    "START_GROUP": "https://images.unsplash.com/photo-1531415074968-036ba1b575da",
    "START_DM": "https://images.unsplash.com/photo-1540747737956-37872a7e86e5",
    "WICKET": "https://images.unsplash.com/photo-1593341646782-e0b495cff86d"
}
