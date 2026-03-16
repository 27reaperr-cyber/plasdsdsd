import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import SERVERS_CONFIG_FILE, DATABASE_FILE
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize SQLite database for users."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                registration_date TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


def register_user(user_id: int, username: str) -> bool:
    """Register a new user if not exists."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            logger.info(f"User {user_id} already exists")
            conn.close()
            return False
        
        registration_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO users (user_id, username, registration_date, role)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, registration_date, 'user'))
        
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} registered")
        return True
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return False


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user information."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'registration_date': row[2],
                'role': row[3]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


def load_servers_config() -> Dict[str, Any]:
    """Load servers configuration from JSON file."""
    try:
        if SERVERS_CONFIG_FILE.exists():
            with open(SERVERS_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading servers config: {e}")
    return {}


def save_servers_config(config: Dict[str, Any]):
    """Save servers configuration to JSON file."""
    try:
        with open(SERVERS_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving servers config: {e}")


def is_process_running(pid: int) -> bool:
    """Check if a process is running."""
    try:
        result = subprocess.run(
            ['ps', '-p', str(pid)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def get_server_status(server: Dict[str, Any]) -> str:
    """Get current server status."""
    if server.get('status') == 'running':
        if is_process_running(server.get('pid', -1)):
            return 'running'
        else:
            return 'stopped'
    return 'stopped'


def format_timestamp(iso_string: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        return iso_string


def get_process_memory_usage(pid: int) -> Optional[str]:
    """Get memory usage of a process."""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            parts = line.split()
            if len(parts) > 1 and parts[1] == str(pid):
                # Memory is in columns 5 (RSS in KB)
                return parts[5] if len(parts) > 5 else 'N/A'
    except Exception:
        pass
    return None


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f} TB"
