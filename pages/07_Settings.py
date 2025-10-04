import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from src.auth import require_auth, check_permission, get_user_preferences, save_user_preferences, get_dashboard_layout, save_dashboard_layout, reset_dashboard_layout
from src.dashboard_components import customize_dashboard_layout, TILE_REGISTRY
from src.alerts import render_alert_settings, AlertManager
from src.tally_api import TallyAPIClient
from src.utils import load_custom_css

# Page configuration
st.set_page_config(
    page_title="Settings - Tally Prime Analytics",
    page_icon="⚙️",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main settings page"""
    
    st.title("⚙️ Settings & Configuration")
    st.markdown("### Customize your Tally Prime Analytics experience")
    
    # Settings navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎛️ Dashboard", 
        "🔔 Alerts", 
        "🔗 Connections", 
        "👤 User Preferences", 
        "🔐 Access Control",
        "📊 System Info"
    ])
    
    with tab1:
        render_dashboard_settings()
    
    with tab2:
        render_alerts_settings()
    
    with tab3:
        render_connection_settings()
    
    with tab4:
        render_user_preferences()
    
    with tab5:
        render_access_control_settings()
    
    with tab6:
        render_system_info()

def render_dashboard_settings():
    """Render dashboard customization settings"""
    st.markdown("## 🎛️ Dashboard Configuration")
    st.markdown("Customize your dashboard layout, tiles, and display preferences")
    
    # Current dashboard layout info
    current_layout = get_dashboard_layout()
    enabled_tiles = [t for t in current_layout.get('tiles', []) if t.get('enabled', True)]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Tiles", len(enabled_tiles))
    
    with col2:
        layout_mode = current_layout.get('layout_mode', 'horizontal')
        st.metric("Layout Mode", layout_mode.title())
    
    with col3:
        auto_refresh = current_layout.get('auto_refresh', True)
        st.metric("Auto Refresh", "Enabled" if auto_refresh else "Disabled")
    
    st.markdown("---")
    
    # Dashboard Layout Customization
    st.markdown("### 📐 Layout Customization")
    
    # Use the existing customization component
    customize_dashboard_layout()
    
    st.markdown("---")
    
    # Dashboard Display Settings
    st.markdown("### 🖥️ Display Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### General Display")
        
        # Theme settings
        theme_mode = st.selectbox(
            "Theme Mode",
            ["Light", "Dark", "Auto"],
            index=0 if st.session_state.get('theme_mode', 'light') == 'light' else 1
        )
        
        # Chart color scheme
        chart_color_scheme = st.selectbox(
            "Chart Color Scheme",
            ["Default", "Business", "Vibrant", "Pastel"],
            index=0
        )
        
        # Number format
        number_format = st.selectbox(
            "Number Format",
            ["Indian (₹1,00,000)", "International (₹100,000)", "Abbreviated (₹1L)"],
            index=2
        )
        
        # Date format
        date_format = st.selectbox(
            "Date Format",
            ["DD-MM-YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
            index=0
        )
    
    with col2:
        st.markdown("#### Dashboard Behavior")
        
        # Auto-refresh settings
        auto_refresh_enabled = st.checkbox(
            "Enable Auto Refresh",
            value=current_layout.get('auto_refresh', True)
        )
        
        if auto_refresh_enabled:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                60, 600, 
                current_layout.get('refresh_interval', 300),
                step=30
            )
        else:
            refresh_interval = 300
        
        # Animation settings
        enable_animations = st.checkbox("Enable Animations", value=True)
        
        # Compact mode
        compact_mode = st.checkbox("Compact Mode", value=False)
        
        # Show tooltips
        show_tooltips = st.checkbox("Show Tooltips", value=True)
    
    # Save display settings
    if st.button("💾 Save Display Settings"):
        display_settings = {
            'theme_mode': theme_mode.lower(),
            'chart_color_scheme': chart_color_scheme.lower(),
            'number_format': number_format,
            'date_format': date_format,
            'auto_refresh': auto_refresh_enabled,
            'refresh_interval': refresh_interval,
            'enable_animations': enable_animations,
            'compact_mode': compact_mode,
            'show_tooltips': show_tooltips
        }
        
        # Update session state
        for key, value in display_settings.items():
            st.session_state[key] = value
        
        # Update dashboard layout
        updated_layout = current_layout.copy()
        updated_layout['auto_refresh'] = auto_refresh_enabled
        updated_layout['refresh_interval'] = refresh_interval
        save_dashboard_layout(updated_layout)
        
        st.success("✅ Display settings saved successfully!")
        st.rerun()
    
    st.markdown("---")
    
    # Dashboard Export/Import
    st.markdown("### 📤📥 Dashboard Export/Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Dashboard Configuration")
        
        if st.button("📤 Export Configuration"):
            config_data = {
                'dashboard_layout': current_layout,
                'user_preferences': get_user_preferences(),
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            config_json = json.dumps(config_data, indent=2)
            
            st.download_button(
                label="💾 Download Configuration File",
                data=config_json,
                file_name=f"tally_dashboard_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("#### Import Dashboard Configuration")
        
        uploaded_file = st.file_uploader(
            "Choose configuration file",
            type=['json'],
            help="Upload a previously exported configuration file"
        )
        
        if uploaded_file is not None:
            try:
                config_data = json.loads(uploaded_file.read().decode())
                
                if 'dashboard_layout' in config_data:
                    st.info("Configuration file loaded successfully!")
                    
                    if st.button("📥 Import Configuration"):
                        # Import dashboard layout
                        if 'dashboard_layout' in config_data:
                            save_dashboard_layout(config_data['dashboard_layout'])
                        
                        # Import user preferences
                        if 'user_preferences' in config_data:
                            save_user_preferences(config_data['user_preferences'])
                        
                        st.success("✅ Configuration imported successfully!")
                        st.rerun()
                else:
                    st.error("❌ Invalid configuration file format")
                    
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file")
            except Exception as e:
                st.error(f"❌ Error importing configuration: {str(e)}")

def render_alerts_settings():
    """Render alert configuration settings"""
    st.markdown("## 🔔 Alert Configuration")
    st.markdown("Configure business alerts, notifications, and thresholds")
    
    # Use the existing alert settings component
    render_alert_settings()
    
    st.markdown("---")
    
    # Notification Channels
    st.markdown("### 📱 Notification Channels")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Email Notifications")
        
        email_enabled = st.checkbox("Enable Email Notifications", value=False)
        
        if email_enabled:
            smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
            smtp_username = st.text_input("Email Username")
            smtp_password = st.text_input("Email Password", type="password")
            
            # Test email configuration
            if st.button("📧 Test Email Configuration"):
                st.info("Email test functionality will be implemented with SMTP setup")
    
    with col2:
        st.markdown("#### Other Notifications")
        
        browser_notifications = st.checkbox("Browser Notifications", value=True)
        sound_notifications = st.checkbox("Sound Notifications", value=False)
        
        # WhatsApp notifications (future feature)
        whatsapp_enabled = st.checkbox("WhatsApp Notifications (Coming Soon)", value=False, disabled=True)
        
        # Slack integration (future feature)
        slack_enabled = st.checkbox("Slack Integration (Coming Soon)", value=False, disabled=True)
    
    # Alert Schedule
    st.markdown("### 📅 Alert Schedule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Business Hours")
        
        business_hours_only = st.checkbox("Send alerts only during business hours", value=True)
        
        if business_hours_only:
            start_time = st.time_input("Business Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            end_time = st.time_input("Business End Time", value=datetime.strptime("18:00", "%H:%M").time())
        
        # Weekend alerts
        weekend_alerts = st.checkbox("Send alerts on weekends", value=False)
    
    with col2:
        st.markdown("#### Alert Frequency")
        
        alert_frequency = st.selectbox(
            "Maximum Alert Frequency",
            ["Immediate", "Every 15 minutes", "Every 30 minutes", "Every hour", "Daily digest"]
        )
        
        # Duplicate suppression
        suppress_duplicates = st.checkbox("Suppress duplicate alerts", value=True)
        
        if suppress_duplicates:
            suppression_period = st.slider(
                "Suppression Period (hours)",
                1, 24, 4
            )
    
    # Save alert settings
    if st.button("💾 Save Alert Settings"):
        alert_settings = {
            'email_enabled': email_enabled,
            'browser_notifications': browser_notifications,
            'sound_notifications': sound_notifications,
            'business_hours_only': business_hours_only,
            'weekend_alerts': weekend_alerts,
            'alert_frequency': alert_frequency,
            'suppress_duplicates': suppress_duplicates
        }
        
        if email_enabled:
            alert_settings.update({
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'smtp_username': smtp_username
                # Note: Password should be encrypted in production
            })
        
        if business_hours_only:
            alert_settings.update({
                'start_time': start_time.strftime("%H:%M"),
                'end_time': end_time.strftime("%H:%M")
            })
        
        if suppress_duplicates:
            alert_settings['suppression_period'] = suppression_period
        
        # Save to session state (in production, save to database)
        st.session_state.alert_settings = alert_settings
        
        st.success("✅ Alert settings saved successfully!")

def render_connection_settings():
    """Render Tally connection and integration settings"""
    st.markdown("## 🔗 Connection Settings")
    st.markdown("Manage Tally Prime connections and external integrations")
    
    # Current connection status
    tally_server = st.session_state.get('tally_server', 'http://localhost:9000')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🖥️ Tally Prime Connection")
        
        # Connection details
        server_url = st.text_input(
            "Tally Server URL",
            value=tally_server,
            help="URL where Tally Prime is running with XML API enabled"
        )
        
        server_port = st.number_input(
            "Server Port",
            value=9000,
            min_value=1000,
            max_value=65535,
            help="Port number for Tally XML API"
        )
        
        # Connection timeout
        connection_timeout = st.slider(
            "Connection Timeout (seconds)",
            5, 60, 30
        )
        
        # Test connection
        if st.button("🔍 Test Connection"):
            full_server_url = f"{server_url.rstrip(':')}:{server_port}" if not server_url.endswith(f":{server_port}") else server_url
            
            try:
                client = TallyAPIClient(full_server_url)
                if client.test_connection():
                    st.success("✅ Successfully connected to Tally Prime!")
                    
                    # Get company information
                    companies = client.get_company_list()
                    if companies:
                        st.info(f"Found {len(companies)} companies: {', '.join([c['name'] for c in companies[:3]])}")
                else:
                    st.error("❌ Unable to connect to Tally Prime")
                    
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
        
        # Save connection settings
        if st.button("💾 Save Connection Settings"):
            full_server_url = f"{server_url.rstrip(':')}:{server_port}" if not server_url.endswith(f":{server_port}") else server_url
            st.session_state.tally_server = full_server_url
            st.session_state.connection_timeout = connection_timeout
            
            st.success("✅ Connection settings saved!")
    
    with col2:
        st.markdown("### 🏢 Company Selection")
        
        # Get available companies
        if tally_server:
            try:
                client = TallyAPIClient(tally_server)
                companies = client.get_company_list()
                
                if companies:
                    company_names = [comp['name'] for comp in companies]
                    current_company = st.session_state.get('company_name', company_names[0] if company_names else '')
                    
                    selected_company = st.selectbox(
                        "Active Company",
                        company_names,
                        index=company_names.index(current_company) if current_company in company_names else 0
                    )
                    
                    if st.button("🔄 Switch Company"):
                        st.session_state.company_name = selected_company
                        st.success(f"✅ Switched to company: {selected_company}")
                        st.rerun()
                        
                else:
                    st.warning("No companies found. Please check Tally connection.")
                    
            except Exception as e:
                st.error(f"Unable to fetch companies: {str(e)}")
        
        st.markdown("### 📊 Data Sync Settings")
        
        # Auto-sync settings
        auto_sync = st.checkbox("Enable Automatic Data Sync", value=True)
        
        if auto_sync:
            sync_interval = st.selectbox(
                "Sync Interval",
                ["Every 5 minutes", "Every 15 minutes", "Every 30 minutes", "Every hour"]
            )
        
        # Data caching
        enable_caching = st.checkbox("Enable Data Caching", value=True)
        
        if enable_caching:
            cache_duration = st.slider("Cache Duration (minutes)", 5, 60, 15)
        
        # Last sync info
        last_sync = st.session_state.get('last_sync_time', 'Never')
        st.info(f"Last sync: {last_sync}")
        
        if st.button("🔄 Force Sync Now"):
            st.cache_data.clear()
            st.session_state.last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("✅ Data synchronized!")
            st.rerun()
    
    st.markdown("---")
    
    # External Integrations
    st.markdown("### 🔌 External Integrations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Database Export")
        
        enable_db_export = st.checkbox("Enable Database Export", value=False)
        
        if enable_db_export:
            db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQL Server"])
            db_connection_string = st.text_input("Connection String", type="password")
            
            if st.button("🔍 Test Database Connection"):
                st.info("Database connection test will be implemented")
    
    with col2:
        st.markdown("#### API Integration")
        
        enable_api = st.checkbox("Enable REST API", value=False)
        
        if enable_api:
            api_key = st.text_input("API Key", value="", type="password")
            api_rate_limit = st.number_input("Rate Limit (requests/minute)", value=100)
            
            st.info("API endpoint: `/api/v1/`")
    
    with col3:
        st.markdown("#### Cloud Backup")
        
        enable_cloud_backup = st.checkbox("Enable Cloud Backup", value=False)
        
        if enable_cloud_backup:
            cloud_provider = st.selectbox("Cloud Provider", ["Google Drive", "OneDrive", "Dropbox"])
            backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
            
            if st.button("☁️ Setup Cloud Backup"):
                st.info("Cloud backup setup will be implemented")

def render_user_preferences():
    """Render user preference settings"""
    st.markdown("## 👤 User Preferences")
    st.markdown("Personalize your experience and account settings")
    
    # Get current preferences
    current_prefs = get_user_preferences()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎨 Interface Preferences")
        
        # Language settings
        language = st.selectbox(
            "Language",
            ["English", "Hindi", "Tamil", "Telugu", "Bengali"],
            index=0
        )
        
        # Currency settings
        currency_symbol = st.selectbox(
            "Currency Symbol",
            ["₹ (INR)", "$ (USD)", "€ (EUR)", "£ (GBP)"],
            index=0
        )
        
        # Decimal places
        decimal_places = st.slider("Decimal Places", 0, 4, 2)
        
        # Thousand separator
        thousand_separator = st.selectbox(
            "Thousand Separator",
            ["Indian (1,00,000)", "International (100,000)"],
            index=0
        )
        
        # Timezone
        timezone = st.selectbox(
            "Timezone",
            ["Asia/Kolkata", "UTC", "Asia/Dubai", "US/Eastern"],
            index=0
        )
    
    with col2:
        st.markdown("### 📊 Data Preferences")
        
        # Default date range
        default_date_range = st.selectbox(
            "Default Date Range",
            ["Last 7 Days", "Last 30 Days", "This Month", "This Quarter"],
            index=1
        )
        
        # Default view
        default_view = st.selectbox(
            "Default Landing Page",
            ["Dashboard", "Sales Reports", "Purchase Reports", "Inventory"],
            index=0
        )
        
        # Chart preferences
        chart_type_preference = st.selectbox(
            "Preferred Chart Type",
            ["Bar Charts", "Line Charts", "Pie Charts", "Mixed"],
            index=3
        )
        
        # Export format
        default_export_format = st.selectbox(
            "Default Export Format",
            ["Excel (.xlsx)", "CSV (.csv)", "PDF (.pdf)"],
            index=0
        )
        
        # Page size for tables
        table_page_size = st.slider("Table Page Size", 10, 100, 25)
    
    # Account Settings
    st.markdown("---")
    st.markdown("### 🔐 Account Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Profile Information")
        
        full_name = st.text_input("Full Name", value=st.session_state.get('username', ''))
        email = st.text_input("Email Address", value="")
        phone = st.text_input("Phone Number", value="")
        department = st.text_input("Department", value="")
    
    with col2:
        st.markdown("#### Security Settings")
        
        # Password change
        if st.button("🔒 Change Password"):
            st.info("Password change functionality will be implemented with proper authentication")
        
        # Session settings
        session_timeout = st.slider("Session Timeout (minutes)", 30, 480, 120)
        
        # Two-factor authentication
        enable_2fa = st.checkbox("Enable Two-Factor Authentication", value=False)
        
        if enable_2fa:
            st.info("2FA setup will be implemented with TOTP/SMS")
    
    # Notification Preferences
    st.markdown("---")
    st.markdown("### 🔔 Notification Preferences")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Alert Types")
        
        inventory_alerts = st.checkbox("Inventory Alerts", value=True)
        sales_alerts = st.checkbox("Sales Alerts", value=True)
        financial_alerts = st.checkbox("Financial Alerts", value=True)
        system_alerts = st.checkbox("System Alerts", value=True)
    
    with col2:
        st.markdown("#### Delivery Method")
        
        email_notifications = st.checkbox("Email Notifications", value=True)
        browser_notifications = st.checkbox("Browser Notifications", value=True)
        mobile_notifications = st.checkbox("Mobile Notifications", value=False)
    
    with col3:
        st.markdown("#### Frequency")
        
        alert_frequency = st.selectbox(
            "Alert Frequency",
            ["Immediate", "Hourly", "Daily", "Weekly"],
            index=0
        )
        
        digest_enabled = st.checkbox("Daily Digest", value=True)
        
        if digest_enabled:
            digest_time = st.time_input("Digest Time", value=datetime.strptime("09:00", "%H:%M").time())
    
    # Save preferences
    if st.button("💾 Save Preferences"):
        preferences = {
            'language': language,
            'currency_symbol': currency_symbol,
            'decimal_places': decimal_places,
            'thousand_separator': thousand_separator,
            'timezone': timezone,
            'default_date_range': default_date_range,
            'default_view': default_view,
            'chart_type_preference': chart_type_preference,
            'default_export_format': default_export_format,
            'table_page_size': table_page_size,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'department': department,
            'session_timeout': session_timeout,
            'enable_2fa': enable_2fa,
            'inventory_alerts': inventory_alerts,
            'sales_alerts': sales_alerts,
            'financial_alerts': financial_alerts,
            'system_alerts': system_alerts,
            'email_notifications': email_notifications,
            'browser_notifications': browser_notifications,
            'mobile_notifications': mobile_notifications,
            'alert_frequency': alert_frequency,
            'digest_enabled': digest_enabled
        }
        
        if digest_enabled:
            preferences['digest_time'] = digest_time.strftime("%H:%M")
        
        save_user_preferences(preferences)
        st.success("✅ Preferences saved successfully!")
        st.rerun()

def render_access_control_settings():
    """Render access control and user management settings"""
    st.markdown("## 🔐 Access Control")
    st.markdown("Manage user permissions and security settings")
    
    # Check if user has admin permissions
    user_role = st.session_state.get('user_role', 'User')
    
    if user_role != 'Administrator':
        st.warning("⚠️ You need administrator privileges to access these settings")
        return
    
    # User Management
    st.markdown("### 👥 User Management")
    
    # Mock user data (in production, this would come from a database)
    users_data = [
        {"username": "admin", "role": "Administrator", "status": "Active", "last_login": "2024-01-15 10:30:00"},
        {"username": "manager", "role": "Manager", "status": "Active", "last_login": "2024-01-15 09:15:00"},
        {"username": "viewer", "role": "Viewer", "status": "Inactive", "last_login": "2024-01-10 14:20:00"}
    ]
    
    users_df = pd.DataFrame(users_data)
    
    # Display user table
    st.dataframe(users_df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Add New User")
        
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["Administrator", "Manager", "Viewer"])
        new_email = st.text_input("Email")
        
        if st.button("➕ Add User"):
            if new_username and new_password:
                st.success(f"✅ User '{new_username}' added successfully!")
            else:
                st.error("❌ Username and password are required")
    
    with col2:
        st.markdown("#### User Actions")
        
        selected_user = st.selectbox("Select User", [user["username"] for user in users_data])
        
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("✏️ Edit User"):
                st.info(f"Edit functionality for user '{selected_user}'")
            
            if st.button("🔒 Reset Password"):
                st.info(f"Password reset for user '{selected_user}'")
        
        with col2b:
            if st.button("❌ Deactivate User"):
                st.warning(f"Deactivate user '{selected_user}'")
            
            if st.button("🗑️ Delete User"):
                st.error(f"Delete user '{selected_user}'")
    
    st.markdown("---")
    
    # Role-Based Permissions
    st.markdown("### 🛡️ Role-Based Permissions")
    
    # Permission matrix
    permissions = [
        "View Dashboard", "View Reports", "Export Data", "Analytics", 
        "Manage Users", "System Settings", "Alert Configuration"
    ]
    
    roles = ["Administrator", "Manager", "Viewer"]
    
    # Create permission matrix
    permission_matrix = {
        "Administrator": [True] * len(permissions),
        "Manager": [True, True, True, True, False, False, True],
        "Viewer": [True, True, False, False, False, False, False]
    }
    
    st.markdown("#### Permission Matrix")
    
    # Display permission matrix as a table
    matrix_data = []
    for permission in permissions:
        row = {"Permission": permission}
        for role in roles:
            row[role] = "✅" if permission_matrix[role][permissions.index(permission)] else "❌"
        matrix_data.append(row)
    
    matrix_df = pd.DataFrame(matrix_data)
    st.dataframe(matrix_df, use_container_width=True)
    
    # Edit permissions
    st.markdown("#### Edit Role Permissions")
    
    selected_role = st.selectbox("Select Role to Edit", roles)
    
    st.markdown(f"**Permissions for {selected_role}:**")
    
    updated_permissions = {}
    for permission in permissions:
        current_value = permission_matrix[selected_role][permissions.index(permission)]
        updated_permissions[permission] = st.checkbox(
            permission, 
            value=current_value,
            key=f"{selected_role}_{permission}"
        )
    
    if st.button("💾 Update Role Permissions"):
        st.success(f"✅ Permissions updated for role '{selected_role}'")
    
    st.markdown("---")
    
    # Security Settings
    st.markdown("### 🔒 Security Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Password Policy")
        
        min_password_length = st.slider("Minimum Password Length", 6, 20, 8)
        require_uppercase = st.checkbox("Require Uppercase Letters", value=True)
        require_lowercase = st.checkbox("Require Lowercase Letters", value=True)
        require_numbers = st.checkbox("Require Numbers", value=True)
        require_special_chars = st.checkbox("Require Special Characters", value=False)
        
        password_expiry_days = st.slider("Password Expiry (days)", 30, 365, 90)
    
    with col2:
        st.markdown("#### Session Security")
        
        max_session_duration = st.slider("Max Session Duration (hours)", 1, 24, 8)
        idle_timeout = st.slider("Idle Timeout (minutes)", 10, 120, 30)
        max_failed_attempts = st.slider("Max Failed Login Attempts", 3, 10, 5)
        lockout_duration = st.slider("Account Lockout Duration (minutes)", 5, 60, 15)
    
    # Audit Settings
    st.markdown("#### Audit & Logging")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_audit_log = st.checkbox("Enable Audit Logging", value=True)
        log_user_actions = st.checkbox("Log User Actions", value=True)
        log_data_access = st.checkbox("Log Data Access", value=False)
        log_system_events = st.checkbox("Log System Events", value=True)
    
    with col2:
        log_retention_days = st.slider("Log Retention (days)", 30, 365, 90)
        enable_log_export = st.checkbox("Enable Log Export", value=True)
        
        if st.button("📄 Export Audit Logs"):
            st.info("Audit log export functionality will be implemented")
    
    # Save security settings
    if st.button("💾 Save Security Settings"):
        security_settings = {
            'min_password_length': min_password_length,
            'require_uppercase': require_uppercase,
            'require_lowercase': require_lowercase,
            'require_numbers': require_numbers,
            'require_special_chars': require_special_chars,
            'password_expiry_days': password_expiry_days,
            'max_session_duration': max_session_duration,
            'idle_timeout': idle_timeout,
            'max_failed_attempts': max_failed_attempts,
            'lockout_duration': lockout_duration,
            'enable_audit_log': enable_audit_log,
            'log_user_actions': log_user_actions,
            'log_data_access': log_data_access,
            'log_system_events': log_system_events,
            'log_retention_days': log_retention_days,
            'enable_log_export': enable_log_export
        }
        
        st.session_state.security_settings = security_settings
        st.success("✅ Security settings saved successfully!")

def render_system_info():
    """Render system information and maintenance"""
    st.markdown("## 📊 System Information")
    st.markdown("View system status, performance metrics, and maintenance options")
    
    # System Status
    st.markdown("### 🖥️ System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("System Status", "🟢 Online")
        st.metric("Uptime", "5 days 14 hours")
    
    with col2:
        st.metric("Active Users", "3")
        st.metric("Total Sessions", "127")
    
    with col3:
        st.metric("Data Updates", "1,234")
        st.metric("Last Backup", "2024-01-15 02:00")
    
    with col4:
        st.metric("Disk Usage", "45.2 GB")
        st.metric("Memory Usage", "2.1 GB")
    
    # Performance Metrics
    st.markdown("### 📈 Performance Metrics")
    
    # Mock performance data
    performance_data = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='H'),
        'CPU_Usage': [20 + i % 30 for i in range(25)],
        'Memory_Usage': [40 + i % 20 for i in range(25)],
        'API_Calls': [100 + i % 50 for i in range(25)]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        import plotly.express as px
        
        fig = px.line(performance_data, x='Time', y=['CPU_Usage', 'Memory_Usage'], 
                     title='System Resource Usage (24h)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(performance_data, x='Time', y='API_Calls', 
                     title='API Call Volume (24h)')
        st.plotly_chart(fig, use_container_width=True)
    
    # System Configuration
    st.markdown("### ⚙️ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Application Info")
        
        app_info = {
            "Application": "Tally Prime Analytics",
            "Version": "1.0.0",
            "Build": "20240115-001",
            "Environment": "Production",
            "Python Version": "3.9.16",
            "Streamlit Version": "1.29.0"
        }
        
        for key, value in app_info.items():
            st.text(f"{key}: {value}")
    
    with col2:
        st.markdown("#### Database Info")
        
        db_info = {
            "Database Type": "SQLite",
            "Database Size": "125 MB",
            "Total Records": "45,231",
            "Last Optimized": "2024-01-10",
            "Backup Status": "✅ Up to date",
            "Connection Pool": "Active (5/10)"
        }
        
        for key, value in db_info.items():
            st.text(f"{key}: {value}")
    
    # Maintenance Actions
    st.markdown("### 🔧 Maintenance Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Cache Management")
        
        cache_size = "245 MB"
        st.text(f"Current cache size: {cache_size}")
        
        if st.button("🗑️ Clear Cache"):
            st.cache_data.clear()
            st.success("✅ Cache cleared successfully!")
        
        if st.button("🔄 Refresh Data"):
            st.info("Data refresh initiated...")
    
    with col2:
        st.markdown("#### Database Maintenance")
        
        if st.button("🛠️ Optimize Database"):
            st.info("Database optimization started...")
        
        if st.button("📊 Analyze Performance"):
            st.info("Performance analysis in progress...")
        
        if st.button("🔍 Check Integrity"):
            st.success("✅ Database integrity check passed")
    
    with col3:
        st.markdown("#### System Maintenance")
        
        if st.button("📄 Generate System Report"):
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'system_info': app_info,
                'database_info': db_info,
                'performance_summary': 'System running optimally'
            }
            
            report_json = json.dumps(report_data, indent=2)
            
            st.download_button(
                label="📥 Download System Report",
                data=report_json,
                file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        if st.button("🔄 Restart Application"):
            st.warning("⚠️ Application restart will disconnect all users")
        
        if st.button("⬆️ Check for Updates"):
            st.info("Checking for application updates...")
    
    # Logs and Diagnostics
    st.markdown("### 📋 Logs and Diagnostics")
    
    log_level = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
    
    # Mock log entries
    log_entries = [
        {"timestamp": "2024-01-15 10:30:00", "level": "INFO", "message": "User admin logged in"},
        {"timestamp": "2024-01-15 10:25:00", "level": "INFO", "message": "Data sync completed successfully"},
        {"timestamp": "2024-01-15 10:20:00", "level": "WARNING", "message": "High memory usage detected"},
        {"timestamp": "2024-01-15 10:15:00", "level": "ERROR", "message": "Connection timeout to Tally server"},
        {"timestamp": "2024-01-15 10:10:00", "level": "INFO", "message": "Cache cleanup completed"}
    ]
    
    # Filter logs by level if needed
    if log_level != "INFO":
        log_entries = [log for log in log_entries if log['level'] == log_level]
    
    # Display logs
    for log in log_entries[:10]:  # Show last 10 entries
        if log['level'] == 'ERROR':
            st.error(f"[{log['timestamp']}] {log['message']}")
        elif log['level'] == 'WARNING':
            st.warning(f"[{log['timestamp']}] {log['message']}")
        else:
            st.info(f"[{log['timestamp']}] {log['message']}")
    
    # Export logs
    if st.button("📤 Export Logs"):
        logs_text = "\n".join([f"[{log['timestamp']}] {log['level']}: {log['message']}" for log in log_entries])
        
        st.download_button(
            label="📥 Download Logs",
            data=logs_text,
            file_name=f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
