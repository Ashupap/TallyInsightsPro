import streamlit as st
import hashlib
import os
from typing import Dict, Optional
from src.tally_api import TallyAPIClient

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

def initialize_session():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'permissions' not in st.session_state:
        st.session_state.permissions = []
    if 'tally_server' not in st.session_state:
        st.session_state.tally_server = "http://localhost:9000"
    if 'company_name' not in st.session_state:
        st.session_state.company_name = None
    if 'dashboard_layout' not in st.session_state:
        st.session_state.dashboard_layout = get_default_dashboard_layout()
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = "light"
    if 'alerts_enabled' not in st.session_state:
        st.session_state.alerts_enabled = True

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
        st.error("Unable to connect to Tally server. Please check server URL and ensure Tally Prime is running.")
        return False
    
    # Get company information
    companies = tally_client.get_company_list()
    company_name = companies[0]['name'] if companies else "Default Company"
    
    # Set session variables
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.user_role = user_data["role"]
    st.session_state.permissions = user_data["permissions"]
    st.session_state.tally_server = tally_server
    st.session_state.company_name = company_name
    
    return True

def check_permission(permission: str) -> bool:
    """Check if current user has specific permission"""
    if not st.session_state.get('authenticated', False):
        return False
    
    user_permissions = st.session_state.get('permissions', [])
    return "all" in user_permissions or permission in user_permissions

def require_auth(func):
    """Decorator to require authentication for page functions"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated', False):
            st.error("Please login to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_permission(permission):
                st.error(f"You don't have permission to access this feature. Required: {permission}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_default_dashboard_layout() -> Dict:
    """Get default dashboard tile layout"""
    return {
        "tiles": [
            {"id": "sales_summary", "position": {"x": 0, "y": 0, "w": 2, "h": 1}, "enabled": True},
            {"id": "purchase_summary", "position": {"x": 2, "y": 0, "w": 2, "h": 1}, "enabled": True},
            {"id": "inventory_status", "position": {"x": 0, "y": 1, "w": 2, "h": 1}, "enabled": True},
            {"id": "outstanding_receivables", "position": {"x": 2, "y": 1, "w": 2, "h": 1}, "enabled": True},
            {"id": "cash_flow", "position": {"x": 0, "y": 2, "w": 4, "h": 1}, "enabled": True},
            {"id": "profit_loss", "position": {"x": 0, "y": 3, "w": 2, "h": 1}, "enabled": True},
            {"id": "alerts", "position": {"x": 2, "y": 3, "w": 2, "h": 1}, "enabled": True}
        ],
        "layout_mode": "horizontal",
        "auto_refresh": True,
        "refresh_interval": 300
    }

def logout_user():
    """Clear session and logout user"""
    keys_to_clear = ['authenticated', 'username', 'user_role', 'permissions', 
                     'tally_server', 'company_name', 'dashboard_layout']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def get_user_preferences() -> Dict:
    """Get user preferences"""
    return {
        "theme_mode": st.session_state.get('theme_mode', 'light'),
        "alerts_enabled": st.session_state.get('alerts_enabled', True),
        "dashboard_layout": st.session_state.get('dashboard_layout', get_default_dashboard_layout()),
        "auto_refresh": st.session_state.get('auto_refresh', True)
    }

def save_user_preferences(preferences: Dict):
    """Save user preferences"""
    for key, value in preferences.items():
        st.session_state[key] = value

# Session state management for dashboard customization
def save_dashboard_layout(layout: Dict):
    """Save dashboard layout to session"""
    st.session_state.dashboard_layout = layout

def get_dashboard_layout() -> Dict:
    """Get current dashboard layout"""
    return st.session_state.get('dashboard_layout', get_default_dashboard_layout())

def reset_dashboard_layout():
    """Reset dashboard to default layout"""
    st.session_state.dashboard_layout = get_default_dashboard_layout()
