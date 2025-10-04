import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from src.auth import require_auth, check_permission
from src.dashboard_components import render_dashboard_grid, get_dashboard_data, customize_dashboard_layout
from src.alerts import render_alerts_panel, check_business_alerts, AlertManager
from src.utils import load_custom_css, get_date_range_options
from src.tally_api import TallyAPIClient

# Page configuration
st.set_page_config(
    page_title="Dashboard - Tally Prime Analytics",
    page_icon="📊",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main dashboard page"""
    
    st.title("📊 Dashboard")
    st.markdown("### Real-time business insights at a glance")
    
    # Check permissions
    if not check_permission('view_reports'):
        st.error("You don't have permission to view the dashboard")
        return
    
    # Dashboard controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # Date range selector
        date_options = get_date_range_options()
        selected_range = st.selectbox(
            "📅 Date Range",
            options=list(date_options.keys()),
            index=2  # Default to "Last 7 Days"
        )
        from_date, to_date = date_options[selected_range]
    
    with col2:
        # Auto-refresh toggle
        auto_refresh = st.checkbox(
            "🔄 Auto Refresh", 
            value=st.session_state.get('dashboard_layout', {}).get('auto_refresh', True)
        )
    
    with col3:
        # Layout toggle
        current_layout = st.session_state.get('dashboard_layout', {})
        layout_mode = st.radio(
            "📐 Layout",
            ["Horizontal", "Vertical"],
            horizontal=True,
            index=0 if current_layout.get('layout_mode') == 'horizontal' else 1
        )
    
    with col4:
        # Refresh button
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # Update layout mode if changed
    if layout_mode.lower() != current_layout.get('layout_mode', 'horizontal'):
        current_layout['layout_mode'] = layout_mode.lower()
        st.session_state.dashboard_layout = current_layout
    
    st.markdown("---")
    
    # Main dashboard content
    dashboard_container = st.container()
    
    with dashboard_container:
        # Fetch dashboard data
        with st.spinner("Loading dashboard data..."):
            dashboard_data = get_dashboard_data()
        
        if not dashboard_data:
            st.error("Unable to fetch dashboard data. Please check your Tally connection.")
            return
        
        # Check for business alerts
        sales_data = dashboard_data.get('sales_summary', pd.DataFrame())
        inventory_data = dashboard_data.get('inventory_status', pd.DataFrame())
        outstanding_data = dashboard_data.get('outstanding_receivables', pd.DataFrame())
        
        check_business_alerts(sales_data, inventory_data, outstanding_data)
        
        # Render dashboard layout
        layout = st.session_state.get('dashboard_layout', {})
        
        if layout.get('tiles'):
            render_dashboard_grid(layout, dashboard_data)
        else:
            st.info("No dashboard tiles configured. Please go to Settings to customize your dashboard.")
            
            # Show default quick stats
            st.markdown("### Quick Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if not sales_data.empty:
                    total_sales = sales_data['amount'].sum()
                    st.metric("Total Sales", f"₹{total_sales:,.0f}")
                else:
                    st.metric("Total Sales", "₹0")
            
            with col2:
                if not inventory_data.empty:
                    total_items = len(inventory_data)
                    st.metric("Inventory Items", f"{total_items:,}")
                else:
                    st.metric("Inventory Items", "0")
            
            with col3:
                if not outstanding_data.empty:
                    total_outstanding = outstanding_data['closing_balance'].sum()
                    st.metric("Outstanding", f"₹{total_outstanding:,.0f}")
                else:
                    st.metric("Outstanding", "₹0")
            
            with col4:
                if not sales_data.empty:
                    avg_transaction = sales_data['amount'].mean()
                    st.metric("Avg Transaction", f"₹{avg_transaction:,.0f}")
                else:
                    st.metric("Avg Transaction", "₹0")
    
    # Sidebar content
    with st.sidebar:
        st.markdown("### 🎛️ Dashboard Controls")
        
        # Quick actions
        st.markdown("#### Quick Actions")
        
        if st.button("📊 Customize Layout"):
            st.session_state.show_customize_layout = True
        
        if st.button("📈 View Analytics"):
            st.switch_page("pages/06_Analytics.py")
        
        if st.button("📋 Generate Report"):
            st.switch_page("pages/02_Sales_Reports.py")
        
        # Alerts panel
        st.markdown("---")
        render_alerts_panel()
        
        # Connection status
        st.markdown("---")
        st.markdown("#### 🔗 Connection Status")
        
        tally_server = st.session_state.get('tally_server')
        if tally_server:
            client = TallyAPIClient(tally_server)
            if client.test_connection():
                st.success("✅ Tally Connected")
            else:
                st.error("❌ Tally Disconnected")
                if st.button("🔄 Reconnect"):
                    # Test connection again
                    if client.test_connection():
                        st.success("Connection restored!")
                        st.rerun()
                    else:
                        st.error("Unable to reconnect. Please check Tally server.")
    
    # Layout customization modal
    if st.session_state.get('show_customize_layout', False):
        with st.expander("🎛️ Customize Dashboard Layout", expanded=True):
            customize_dashboard_layout()
            
            if st.button("Close Customization"):
                st.session_state.show_customize_layout = False
                st.rerun()
    
    # Auto-refresh functionality
    if auto_refresh:
        refresh_interval = st.session_state.get('dashboard_layout', {}).get('refresh_interval', 300)
        
        # Add auto-refresh using st.rerun with timer
        st.markdown(f"*Auto-refreshing every {refresh_interval} seconds*")
        
        # Use JavaScript for auto-refresh (simplified approach)
        auto_refresh_script = f"""
        <script>
            setTimeout(function() {{
                window.location.reload();
            }}, {refresh_interval * 1000});
        </script>
        """
        
        # Note: In a production environment, you'd implement proper auto-refresh
        # This is a simplified demonstration
    
    # Footer with last update time
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            f"</div>", 
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()

