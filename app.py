import streamlit as st
import os
from datetime import datetime, timedelta
from src.auth import authenticate_user, initialize_session
from src.tally_api import TallyAPIClient
from src.utils import load_custom_css

# Page configuration
st.set_page_config(
    page_title="Tally Prime Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session()

# Custom CSS for Tally-inspired styling
load_custom_css()

def main():
    """Main application entry point"""
    
    # Authentication check
    if not st.session_state.get('authenticated', False):
        st.title("🏢 Tally Prime Analytics Dashboard")
        st.markdown("### Welcome to your comprehensive business intelligence platform")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("#### Please login to continue")
                
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    tally_server = st.text_input("Tally Server URL", value="http://localhost:9000")
                    submitted = st.form_submit_button("Login")
                    
                    if submitted:
                        if authenticate_user(username, password, tally_server):
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("Invalid credentials or unable to connect to Tally server")
        
        # Show features preview
        st.markdown("---")
        st.markdown("### 🌟 Key Features")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **📈 Real-time Analytics**
            - Live data from Tally Prime
            - 15+ interactive dashboards
            - Drill-down capabilities
            """)
        
        with col2:
            st.markdown("""
            **🎯 Advanced Insights**
            - AI-powered forecasting
            - Customer segmentation
            - Trend analysis
            """)
        
        with col3:
            st.markdown("""
            **🔧 Customizable Views**
            - Drag-and-drop tiles
            - Role-based access
            - Export functionality
            """)
        
        return
    
    # Main application for authenticated users
    st.sidebar.title("📊 Tally Analytics")
    st.sidebar.markdown(f"**User:** {st.session_state.get('username', 'Unknown')}")
    st.sidebar.markdown(f"**Role:** {st.session_state.get('user_role', 'User')}")
    st.sidebar.markdown(f"**Company:** {st.session_state.get('company_name', 'Not Connected')}")
    
    # Connection status indicator
    tally_client = TallyAPIClient(st.session_state.get('tally_server'))
    connection_status = tally_client.test_connection()
    
    if connection_status:
        st.sidebar.success("🟢 Tally Connected")
    else:
        st.sidebar.error("🔴 Tally Disconnected")
        st.sidebar.button("Reconnect", key="reconnect_btn")
    
    # Navigation info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Navigation")
    st.sidebar.markdown("""
    - **Dashboard**: Overview tiles and KPIs
    - **Sales Reports**: Customer and product analysis
    - **Purchase Reports**: Vendor and procurement insights
    - **Inventory**: Stock levels and movement
    - **Financial**: P&L, Balance Sheet, Cash Flow
    - **Analytics**: AI insights and forecasting
    - **Settings**: Configuration and preferences
    """)
    
    # Quick actions
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Quick Actions")
    
    if st.sidebar.button("🔄 Refresh All Data"):
        st.session_state.clear_cache = True
        st.success("Data refresh initiated!")
        st.rerun()
    
    if st.sidebar.button("📊 Export Current View"):
        st.info("Export functionality will be implemented based on current page")
    
    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Main content area
    st.title("🏠 Welcome to Tally Prime Analytics")
    st.markdown("### Your comprehensive business intelligence dashboard")
    
    # Quick stats overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📈 Today's Sales", 
            value="₹0", 
            delta="0%",
            help="Real-time sales data from Tally"
        )
    
    with col2:
        st.metric(
            label="📦 Stock Items", 
            value="0", 
            delta="0",
            help="Total number of stock items"
        )
    
    with col3:
        st.metric(
            label="👥 Active Customers", 
            value="0", 
            delta="0",
            help="Customers with recent transactions"
        )
    
    with col4:
        st.metric(
            label="💰 Outstanding", 
            value="₹0", 
            delta="₹0",
            help="Total receivables"
        )
    
    # Recent activity and alerts
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Quick Dashboard Preview")
        st.info("Navigate to the Dashboard page to view and customize your tiles")
        
        # Sample tile preview
        tile_col1, tile_col2 = st.columns(2)
        with tile_col1:
            with st.container():
                st.markdown("**Sales Trend**")
                st.line_chart([10, 15, 13, 17, 20, 18, 25])
        
        with tile_col2:
            with st.container():
                st.markdown("**Top Products**")
                st.bar_chart({'Product A': 30, 'Product B': 25, 'Product C': 20})
    
    with col2:
        st.markdown("### 🔔 Alerts & Notifications")
        
        # Sample alerts (will be replaced with real data)
        alert_container = st.container()
        with alert_container:
            if connection_status:
                st.info("📡 System ready - All connections active")
            else:
                st.error("⚠️ Tally connection lost - Please check server")
            
            st.warning("📦 3 items below reorder level")
            st.info("💳 GST filing due in 5 days")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Tally Prime Analytics Dashboard | Powered by Streamlit | Last updated: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
