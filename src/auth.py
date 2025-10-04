import hashlib
from typing import Dict, Optional
from src.tally_api import TallyAPIClient
import logging

logger = logging.getLogger(__name__)

# Default users (in production, this would be from database)
DEFAULT_USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "Administrator",
        "permissions": ["all"]
    },
    "manager": {
        "password": hashlib.sha256("manager123".encode()).hexdigest(),
        "role": "Manager",
        "permissions": ["view_reports", "export_data", "analytics"]
    },
    "viewer": {
        "password": hashlib.sha256("viewer123".encode()).hexdigest(),
        "role": "Viewer",
        "permissions": ["view_reports"]
    }
}

def authenticate_user(username: str, password: str, tally_server: str) -> bool:
    """Authenticate user credentials and test Tally connection"""
    if not username or not password:
        return False
    
    # Hash the provided password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Check against default users (in production, check database)
    user_data = DEFAULT_USERS.get(username)
    if not user_data or user_data["password"] != password_hash:
        return False
    
    # Test Tally connection
    tally_client = TallyAPIClient(tally_server)
    if not tally_client.test_connection():
        logger.error("Unable to connect to Tally server")
        return False
    
    return True

def get_user_data(username: str) -> Optional[Dict]:
    """Get user data by username"""
    return DEFAULT_USERS.get(username)

def check_permission(user_permissions: list, permission: str) -> bool:
    """Check if user has specific permission"""
    return "all" in user_permissions or permission in user_permissions
