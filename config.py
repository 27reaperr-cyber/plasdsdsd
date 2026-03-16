import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'PUT_TELEGRAM_TOKEN')
MAX_SERVERS = int(os.getenv('MAX_SERVERS', 5))
SERVER_RAM_MIN = os.getenv('SERVER_RAM_MIN', '1G')
SERVER_RAM_MAX = os.getenv('SERVER_RAM_MAX', '2G')

# Project paths
BASE_DIR = Path(__file__).parent
SERVERS_DIR = BASE_DIR / 'servers'
DATABASE_FILE = BASE_DIR / 'users.db'
SERVERS_CONFIG_FILE = BASE_DIR / 'servers.json'

# Create necessary directories
SERVERS_DIR.mkdir(exist_ok=True)

# Minecraft server types
SERVER_TYPES = {
    'paper': 'PaperMC',
    'vanilla': 'Vanilla',
    'spigot': 'Spigot'
}
