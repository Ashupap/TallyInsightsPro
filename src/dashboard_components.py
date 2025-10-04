import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.tally_api import TallyAPIClient, fetch_cached_sales_data, fetch_cached_inventory_data
from src.auth import check_permission

class DashboardTile:
    """Base class for dashboard tiles"""
    
    def __init__(self, tile_id: str, title: str, size: str = "medium"):
        self.tile_id = tile_id
        self.title = title
        self.size = size  # small, medium, large
        self.enabled = True
    
    def render(self, data: Any = None):
        """Render the tile - to be implemented by subclasses"""
        raise NotImplementedError

class SalesSummaryTile(DashboardTile):
    """Sales summary tile with trend chart"""
    
    def __init__(self):
        super().__init__("sales_summary", "📈 Sales Summary")
    
    def render(self, sales_data: pd.DataFrame = None):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {self.title}")
                
                if sales_data is not None and not sales_data.empty:
                    # Calculate metrics
                    total_sales = sales_data['amount'].sum()
                    sales_count = len(sales_data)
                    avg_sale = total_sales / sales_count if sales_count > 0 else 0
                    
                    # Display metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Total Sales", f"₹{total_sales:,.0f}")
                    with metric_col2:
                        st.metric("Transactions", f"{sales_count}")
                    with metric_col3:
                        st.metric("Avg. Sale", f"₹{avg_sale:,.0f}")
                    
                    # Sales trend chart
                    if 'date' in sales_data.columns:
                        sales_data['date'] = pd.to_datetime(sales_data['date'])
                        daily_sales = sales_data.groupby(sales_data['date'].dt.date)['amount'].sum().reset_index()
                        
                        fig = px.line(daily_sales, x='date', y='amount', 
                                    title='Sales Trend', height=200)
                        fig.update_layout(showlegend=False, margin=dict(t=30, b=30))
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No sales data available")
                    st.metric("Total Sales", "₹0")
            
            with col2:
                if st.button("📊 Details", key=f"{self.tile_id}_details"):
                    st.session_state.drill_down = "sales_detail"

class PurchaseSummaryTile(DashboardTile):
    """Purchase summary tile"""
    
    def __init__(self):
        super().__init__("purchase_summary", "📦 Purchase Summary")
    
    def render(self, purchase_data: pd.DataFrame = None):
        with st.container():
            st.markdown(f"### {self.title}")
            
            if purchase_data is not None and not purchase_data.empty:
                total_purchases = purchase_data['amount'].sum()
                purchase_count = len(purchase_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Purchases", f"₹{total_purchases:,.0f}")
                with col2:
                    st.metric("Orders", f"{purchase_count}")
                
                # Top suppliers
                if 'party_name' in purchase_data.columns:
                    top_suppliers = purchase_data.groupby('party_name')['amount'].sum().nlargest(5)
                    fig = px.bar(x=top_suppliers.values, y=top_suppliers.index, 
                               orientation='h', title='Top Suppliers', height=200)
                    fig.update_layout(margin=dict(t=30, b=30))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No purchase data available")
                st.metric("Total Purchases", "₹0")

class InventoryStatusTile(DashboardTile):
    """Inventory status tile with stock alerts"""
    
    def __init__(self):
        super().__init__("inventory_status", "📦 Inventory Status")
    
    def render(self, inventory_data: pd.DataFrame = None):
        with st.container():
            st.markdown(f"### {self.title}")
            
            if inventory_data is not None and not inventory_data.empty:
                total_items = len(inventory_data)
                total_value = inventory_data['closing_value'].sum()
                
                # Calculate low stock items
                inventory_data['is_low_stock'] = (
                    inventory_data['closing_balance'] <= inventory_data['reorder_level']
                )
                low_stock_count = inventory_data['is_low_stock'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Items", f"{total_items}")
                with col2:
                    st.metric("Total Value", f"₹{total_value:,.0f}")
                with col3:
                    st.metric("Low Stock", f"{low_stock_count}", delta=None, 
                            delta_color="inverse" if low_stock_count > 0 else "normal")
                
                # Stock level gauge
                if total_items > 0:
                    stock_health = ((total_items - low_stock_count) / total_items) * 100
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = stock_health,
                        title = {'text': "Stock Health %"},
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "gray"}],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75, 'value': 90}}))
                    fig.update_layout(height=200, margin=dict(t=30, b=30))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No inventory data available")
                st.metric("Total Items", "0")

class OutstandingReceivablesTile(DashboardTile):
    """Outstanding receivables tile"""
    
    def __init__(self):
        super().__init__("outstanding_receivables", "💰 Outstanding Receivables")
    
    def render(self, outstanding_data: pd.DataFrame = None):
        with st.container():
            st.markdown(f"### {self.title}")
            
            if outstanding_data is not None and not outstanding_data.empty:
                total_outstanding = outstanding_data['closing_balance'].sum()
                overdue_count = len(outstanding_data[outstanding_data['closing_balance'] > 0])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Outstanding", f"₹{total_outstanding:,.0f}")
                with col2:
                    st.metric("Overdue Parties", f"{overdue_count}")
                
                # Top debtors
                top_debtors = outstanding_data.nlargest(5, 'closing_balance')
                if not top_debtors.empty:
                    fig = px.bar(top_debtors, x='closing_balance', y='party_name',
                               orientation='h', title='Top Debtors', height=200)
                    fig.update_layout(margin=dict(t=30, b=30))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No outstanding data available")
                st.metric("Total Outstanding", "₹0")

class CashFlowTile(DashboardTile):
    """Cash flow tile"""
    
    def __init__(self):
        super().__init__("cash_flow", "💳 Cash Flow")
    
    def render(self, cash_flow_data: Dict = None):
        with st.container():
            st.markdown(f"### {self.title}")
            
            if cash_flow_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Cash Inflow", f"₹{cash_flow_data.get('inflow', 0):,.0f}")
                with col2:
                    st.metric("Cash Outflow", f"₹{cash_flow_data.get('outflow', 0):,.0f}")
                with col3:
                    net_flow = cash_flow_data.get('inflow', 0) - cash_flow_data.get('outflow', 0)
                    st.metric("Net Cash Flow", f"₹{net_flow:,.0f}")
                
                # Cash flow waterfall chart
                categories = ['Opening', 'Inflows', 'Outflows', 'Closing']
                values = [
                    cash_flow_data.get('opening', 0),
                    cash_flow_data.get('inflow', 0),
                    -cash_flow_data.get('outflow', 0),
                    cash_flow_data.get('closing', 0)
                ]
                
                fig = go.Figure(go.Waterfall(
                    x=categories, y=values,
                    measure=["absolute", "relative", "relative", "total"]
                ))
                fig.update_layout(title="Cash Flow", height=200, margin=dict(t=30, b=30))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No cash flow data available")

class ProfitLossTile(DashboardTile):
    """Profit and Loss tile"""
    
    def __init__(self):
        super().__init__("profit_loss", "📊 Profit & Loss")
    
    def render(self, pl_data: Dict = None):
        with st.container():
            st.markdown(f"### {self.title}")
            
            if pl_data:
                revenue = pl_data.get('revenue', 0)
                expenses = pl_data.get('expenses', 0)
                net_profit = pl_data.get('net_profit', 0)
                gross_profit = pl_data.get('gross_profit', 0)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Revenue", f"₹{revenue:,.0f}")
                    st.metric("Gross Profit", f"₹{gross_profit:,.0f}")
                with col2:
                    st.metric("Expenses", f"₹{expenses:,.0f}")
                    st.metric("Net Profit", f"₹{net_profit:,.0f}")
                
                # P&L chart
                categories = ['Revenue', 'COGS', 'Expenses', 'Net Profit']
                values = [revenue, -pl_data.get('cost_of_goods_sold', 0), -expenses, net_profit]
                colors = ['green', 'red', 'red', 'blue']
                
                fig = go.Figure(data=[
                    go.Bar(x=categories, y=values, marker_color=colors)
                ])
                fig.update_layout(title="P&L Summary", height=200, margin=dict(t=30, b=30))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No P&L data available")

class AlertsTile(DashboardTile):
    """Alerts and notifications tile"""
    
    def __init__(self):
        super().__init__("alerts", "🔔 Alerts")
    
    def render(self, alerts_data: List[Dict] = None):
        with st.container():
            st.markdown(f"### {self.title}")
            
            if alerts_data:
                alert_count = len(alerts_data)
                critical_count = len([a for a in alerts_data if a.get('priority') == 'critical'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Alerts", f"{alert_count}")
                with col2:
                    st.metric("Critical", f"{critical_count}")
                
                # Show recent alerts
                for alert in alerts_data[:3]:  # Show top 3 alerts
                    alert_type = alert.get('type', 'info')
                    message = alert.get('message', 'No message')
                    
                    if alert_type == 'critical':
                        st.error(f"🚨 {message}")
                    elif alert_type == 'warning':
                        st.warning(f"⚠️ {message}")
                    else:
                        st.info(f"ℹ️ {message}")
            else:
                st.success("✅ No active alerts")

# Dashboard tile registry
TILE_REGISTRY = {
    "sales_summary": SalesSummaryTile,
    "purchase_summary": PurchaseSummaryTile,
    "inventory_status": InventoryStatusTile,
    "outstanding_receivables": OutstandingReceivablesTile,
    "cash_flow": CashFlowTile,
    "profit_loss": ProfitLossTile,
    "alerts": AlertsTile
}

def create_tile(tile_id: str) -> Optional[DashboardTile]:
    """Create a tile instance by ID"""
    tile_class = TILE_REGISTRY.get(tile_id)
    if tile_class:
        return tile_class()
    return None

def render_dashboard_grid(layout: Dict, data: Dict = None):
    """Render dashboard tiles in grid layout"""
    tiles = layout.get('tiles', [])
    enabled_tiles = [t for t in tiles if t.get('enabled', True)]
    
    if not enabled_tiles:
        st.info("No tiles configured. Please go to Settings to customize your dashboard.")
        return
    
    # Group tiles by row based on y position
    tiles_by_row = {}
    for tile_config in enabled_tiles:
        y_pos = tile_config['position']['y']
        if y_pos not in tiles_by_row:
            tiles_by_row[y_pos] = []
        tiles_by_row[y_pos].append(tile_config)
    
    # Render tiles row by row
    for row_y in sorted(tiles_by_row.keys()):
        row_tiles = sorted(tiles_by_row[row_y], key=lambda t: t['position']['x'])
        
        # Create columns based on tile widths
        col_widths = [tile['position']['w'] for tile in row_tiles]
        columns = st.columns(col_widths)
        
        for i, tile_config in enumerate(row_tiles):
            tile_id = tile_config['id']
            tile = create_tile(tile_id)
            
            if tile and i < len(columns):
                with columns[i]:
                    with st.container():
                        # Get data for this specific tile
                        tile_data = data.get(tile_id) if data else None
                        tile.render(tile_data)

def get_dashboard_data() -> Dict:
    """Fetch all data needed for dashboard tiles"""
    if not st.session_state.get('authenticated'):
        return {}
    
    tally_server = st.session_state.get('tally_server')
    if not tally_server:
        return {}
    
    # Date range for data fetching
    today = datetime.now()
    from_date = (today - timedelta(days=30)).strftime('%d-%b-%Y')
    to_date = today.strftime('%d-%b-%Y')
    
    data = {}
    
    try:
        # Fetch sales data
        sales_data = fetch_cached_sales_data(tally_server, from_date, to_date)
        data['sales_summary'] = sales_data
        
        # Fetch inventory data
        inventory_data = fetch_cached_inventory_data(tally_server)
        data['inventory_status'] = inventory_data
        
        # For other tiles, we'll use TallyAPIClient directly
        client = TallyAPIClient(tally_server)
        
        # Purchase data
        purchase_data = client.get_purchase_data(from_date, to_date)
        data['purchase_summary'] = purchase_data
        
        # Outstanding data
        outstanding_data = client.get_outstanding_data()
        data['outstanding_receivables'] = outstanding_data
        
        # P&L data
        pl_data = client.get_profit_loss_data(from_date, to_date)
        data['profit_loss'] = pl_data
        
        # Sample cash flow data (would be calculated from actual transactions)
        data['cash_flow'] = {
            'opening': 100000,
            'inflow': 75000,
            'outflow': 60000,
            'closing': 115000
        }
        
        # Sample alerts data
        alerts = []
        if not inventory_data.empty:
            low_stock_items = inventory_data[
                inventory_data['closing_balance'] <= inventory_data['reorder_level']
            ]
            if not low_stock_items.empty:
                alerts.append({
                    'type': 'warning',
                    'message': f"{len(low_stock_items)} items below reorder level",
                    'priority': 'high'
                })
        
        data['alerts'] = alerts
        
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")
        data = {}
    
    return data

def customize_dashboard_layout():
    """UI for customizing dashboard layout"""
    st.markdown("### 🎛️ Customize Dashboard Layout")
    
    current_layout = st.session_state.get('dashboard_layout', {})
    tiles = current_layout.get('tiles', [])
    
    # Layout mode selection
    layout_mode = st.radio(
        "Layout Mode",
        ["horizontal", "vertical"],
        index=0 if current_layout.get('layout_mode') == 'horizontal' else 1
    )
    
    # Tile configuration
    st.markdown("#### Available Tiles")
    
    available_tiles = {
        "sales_summary": "📈 Sales Summary",
        "purchase_summary": "📦 Purchase Summary", 
        "inventory_status": "📦 Inventory Status",
        "outstanding_receivables": "💰 Outstanding Receivables",
        "cash_flow": "💳 Cash Flow",
        "profit_loss": "📊 Profit & Loss",
        "alerts": "🔔 Alerts"
    }
    
    enabled_tiles = []
    for tile_id, tile_name in available_tiles.items():
        # Find if tile is currently enabled
        current_tile = next((t for t in tiles if t['id'] == tile_id), None)
        is_enabled = current_tile is not None and current_tile.get('enabled', True)
        
        if st.checkbox(tile_name, value=is_enabled, key=f"tile_{tile_id}"):
            enabled_tiles.append({
                'id': tile_id,
                'position': current_tile['position'] if current_tile else {'x': 0, 'y': 0, 'w': 2, 'h': 1},
                'enabled': True
            })
    
    # Auto-refresh settings
    auto_refresh = st.checkbox("Auto-refresh dashboard", value=current_layout.get('auto_refresh', True))
    refresh_interval = st.slider("Refresh interval (seconds)", 60, 600, current_layout.get('refresh_interval', 300))
    
    # Save configuration
    if st.button("Save Layout"):
        new_layout = {
            'tiles': enabled_tiles,
            'layout_mode': layout_mode,
            'auto_refresh': auto_refresh,
            'refresh_interval': refresh_interval
        }
        st.session_state.dashboard_layout = new_layout
        st.success("Dashboard layout saved!")
        st.rerun()
    
    # Reset to default
    if st.button("Reset to Default"):
        from src.auth import get_default_dashboard_layout
        st.session_state.dashboard_layout = get_default_dashboard_layout()
        st.success("Dashboard reset to default!")
        st.rerun()
