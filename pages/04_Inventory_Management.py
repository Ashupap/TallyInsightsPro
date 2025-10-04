import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from src.auth import require_auth, check_permission
from src.tally_api import TallyAPIClient, fetch_cached_inventory_data
from src.utils import load_custom_css, format_currency, format_number, export_dataframe_to_excel
from src.alerts import AlertManager, AlertType, AlertPriority

# Page configuration
st.set_page_config(
    page_title="Inventory Management - Tally Prime Analytics",
    page_icon="📦",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main inventory management page"""
    
    st.title("📦 Inventory Management")
    st.markdown("### Complete stock control and inventory analytics")
    
    # Check permissions
    if not check_permission('view_reports'):
        st.error("You don't have permission to view inventory reports")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ Inventory Controls")
        
        # View selection
        view_type = st.selectbox(
            "📊 View Type",
            ["Inventory Overview", "Stock Levels", "Reorder Management", "Stock Movement", "Inventory Valuation", "ABC Analysis"]
        )
        
        # Filters
        st.markdown("---")
        st.markdown("#### Filters")
        
        # Stock category filter
        stock_category = st.multiselect(
            "Stock Categories",
            options=[],  # Would be populated from Tally data
            help="Filter by stock categories"
        )
        
        # Stock level filter
        stock_level_filter = st.selectbox(
            "Stock Level",
            ["All Items", "In Stock", "Low Stock", "Out of Stock", "Overstock"]
        )
        
        # Value range filter
        min_value = st.number_input("Minimum Stock Value", min_value=0.0, value=0.0)
        max_value = st.number_input("Maximum Stock Value", min_value=0.0, value=0.0)
        
        # Refresh data button
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # Main content area
    try:
        with st.spinner("Loading inventory data..."):
            # Fetch inventory data
            tally_server = st.session_state.get('tally_server')
            if not tally_server:
                st.error("Tally server not configured. Please check your settings.")
                return
            
            inventory_data = fetch_cached_inventory_data(tally_server)
            
            if inventory_data.empty:
                st.warning("No inventory data found. Please check your Tally connection and ensure you have stock items configured.")
                return
            
            # Process data based on view type
            if view_type == "Inventory Overview":
                render_inventory_overview(inventory_data)
            elif view_type == "Stock Levels":
                render_stock_levels(inventory_data, stock_level_filter)
            elif view_type == "Reorder Management":
                render_reorder_management(inventory_data)
            elif view_type == "Stock Movement":
                render_stock_movement(inventory_data)
            elif view_type == "Inventory Valuation":
                render_inventory_valuation(inventory_data)
            elif view_type == "ABC Analysis":
                render_abc_analysis(inventory_data)
            
    except Exception as e:
        st.error(f"Error loading inventory data: {str(e)}")

def render_inventory_overview(inventory_data: pd.DataFrame):
    """Render inventory overview dashboard"""
    st.markdown("## 📊 Inventory Overview")
    
    # Calculate key metrics
    total_items = len(inventory_data)
    total_value = inventory_data['closing_value'].sum()
    in_stock_items = len(inventory_data[inventory_data['closing_balance'] > 0])
    out_of_stock_items = len(inventory_data[inventory_data['closing_balance'] <= 0])
    
    # Low stock calculation
    inventory_data['is_low_stock'] = (
        (inventory_data['closing_balance'] <= inventory_data['reorder_level']) &
        (inventory_data['closing_balance'] > 0)
    )
    low_stock_items = inventory_data['is_low_stock'].sum()
    
    # Overview metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Items", f"{total_items:,}")
    with col2:
        st.metric("Total Value", format_currency(total_value))
    with col3:
        st.metric("In Stock", f"{in_stock_items:,}")
    with col4:
        st.metric("Out of Stock", f"{out_of_stock_items:,}")
    with col5:
        st.metric("Low Stock", f"{low_stock_items:,}")
    
    # Stock status distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Stock Status Distribution")
        
        # Create status categories
        def get_stock_status(row):
            if row['closing_balance'] <= 0:
                return 'Out of Stock'
            elif row['is_low_stock']:
                return 'Low Stock'
            elif row['closing_balance'] > row['reorder_level'] * 2:
                return 'Overstock'
            else:
                return 'Normal Stock'
        
        inventory_data['stock_status'] = inventory_data.apply(get_stock_status, axis=1)
        status_counts = inventory_data['stock_status'].value_counts()
        
        fig = px.pie(values=status_counts.values, names=status_counts.index,
                     title='Stock Status Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 Inventory Value Distribution")
        
        # Value by category
        if 'category' in inventory_data.columns:
            category_value = inventory_data.groupby('category')['closing_value'].sum().head(10)
            fig = px.bar(x=category_value.values, y=category_value.index,
                        orientation='h', title='Top Categories by Value')
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Create value ranges
            def categorize_value(value):
                if value < 1000:
                    return 'Low Value (< ₹1K)'
                elif value < 10000:
                    return 'Medium Value (₹1K-₹10K)'
                elif value < 50000:
                    return 'High Value (₹10K-₹50K)'
                else:
                    return 'Very High Value (> ₹50K)'
            
            inventory_data['value_category'] = inventory_data['closing_value'].apply(categorize_value)
            value_distribution = inventory_data['value_category'].value_counts()
            
            fig = px.bar(x=value_distribution.index, y=value_distribution.values,
                        title='Items by Value Range')
            st.plotly_chart(fig, use_container_width=True)
    
    # Top items by value and quantity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💎 Top Items by Value")
        top_by_value = inventory_data.nlargest(10, 'closing_value')[['name', 'closing_value', 'closing_balance']]
        top_by_value['closing_value'] = top_by_value['closing_value'].apply(format_currency)
        top_by_value.columns = ['Item Name', 'Stock Value', 'Quantity']
        st.dataframe(top_by_value, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 📦 Top Items by Quantity")
        top_by_quantity = inventory_data.nlargest(10, 'closing_balance')[['name', 'closing_balance', 'base_unit']]
        top_by_quantity.columns = ['Item Name', 'Quantity', 'Unit']
        st.dataframe(top_by_quantity, use_container_width=True, hide_index=True)
    
    # Recent alerts and actions needed
    st.markdown("### 🔔 Action Items")
    
    alert_col1, alert_col2 = st.columns(2)
    
    with alert_col1:
        st.markdown("#### ⚠️ Low Stock Items")
        if low_stock_items > 0:
            low_stock_list = inventory_data[inventory_data['is_low_stock']].nsmallest(5, 'closing_balance')
            for _, item in low_stock_list.iterrows():
                st.warning(f"**{item['name']}**: {item['closing_balance']} {item['base_unit']} remaining (Reorder: {item['reorder_level']})")
        else:
            st.success("No items below reorder level")
    
    with alert_col2:
        st.markdown("#### 🚫 Out of Stock Items")
        if out_of_stock_items > 0:
            out_of_stock_list = inventory_data[inventory_data['closing_balance'] <= 0]['name'].head(5)
            for item_name in out_of_stock_list:
                st.error(f"**{item_name}**: Out of stock")
        else:
            st.success("No items out of stock")
    
    # Export section
    render_export_section(inventory_data, "inventory_overview")

def render_stock_levels(inventory_data: pd.DataFrame, filter_type: str):
    """Render stock levels analysis"""
    st.markdown("## 📊 Stock Levels Analysis")
    
    # Apply filter
    if filter_type == "In Stock":
        filtered_data = inventory_data[inventory_data['closing_balance'] > 0]
    elif filter_type == "Low Stock":
        filtered_data = inventory_data[
            (inventory_data['closing_balance'] <= inventory_data['reorder_level']) &
            (inventory_data['closing_balance'] > 0)
        ]
    elif filter_type == "Out of Stock":
        filtered_data = inventory_data[inventory_data['closing_balance'] <= 0]
    elif filter_type == "Overstock":
        filtered_data = inventory_data[inventory_data['closing_balance'] > inventory_data['reorder_level'] * 2]
    else:
        filtered_data = inventory_data
    
    st.markdown(f"**Showing:** {filter_type} ({len(filtered_data):,} items)")
    
    # Stock level metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_stock_level = filtered_data['closing_balance'].mean()
        st.metric("Avg Stock Level", f"{avg_stock_level:.1f}")
    
    with col2:
        total_stock_value = filtered_data['closing_value'].sum()
        st.metric("Total Stock Value", format_currency(total_stock_value))
    
    with col3:
        median_stock = filtered_data['closing_balance'].median()
        st.metric("Median Stock Level", f"{median_stock:.1f}")
    
    with col4:
        stock_variance = filtered_data['closing_balance'].std()
        st.metric("Stock Variance", f"{stock_variance:.1f}")
    
    # Stock level distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Stock Level Distribution")
        
        # Create histogram of stock levels
        fig = px.histogram(filtered_data, x='closing_balance', nbins=20,
                          title='Distribution of Stock Levels')
        fig.update_layout(xaxis_title='Stock Quantity', yaxis_title='Number of Items')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Stock vs Reorder Levels")
        
        # Scatter plot of stock vs reorder levels
        fig = px.scatter(filtered_data, x='reorder_level', y='closing_balance',
                        hover_data=['name'], title='Current Stock vs Reorder Level')
        
        # Add diagonal line for reference
        max_val = max(filtered_data['reorder_level'].max(), filtered_data['closing_balance'].max())
        fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                     line=dict(color="red", dash="dash"))
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed stock levels table
    st.markdown("### 📋 Detailed Stock Levels")
    
    # Add search and sort options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search Items", "")
    
    with col2:
        sort_by = st.selectbox("Sort By", ["Name", "Stock Level", "Stock Value", "Reorder Level"])
    
    with col3:
        sort_order = st.selectbox("Order", ["Ascending", "Descending"])
    
    # Apply search filter
    if search_term:
        filtered_data = filtered_data[filtered_data['name'].str.contains(search_term, case=False, na=False)]
    
    # Apply sorting
    sort_column_map = {
        "Name": "name",
        "Stock Level": "closing_balance", 
        "Stock Value": "closing_value",
        "Reorder Level": "reorder_level"
    }
    
    sort_ascending = sort_order == "Ascending"
    display_data = filtered_data.sort_values(sort_column_map[sort_by], ascending=sort_ascending)
    
    # Format display data
    display_columns = display_data[['name', 'closing_balance', 'base_unit', 'closing_value', 'reorder_level']].copy()
    display_columns.columns = ['Item Name', 'Current Stock', 'Unit', 'Stock Value', 'Reorder Level']
    display_columns['Stock Value'] = display_columns['Stock Value'].apply(format_currency)
    
    # Color code rows based on stock status
    def highlight_stock_levels(row):
        if row['Current Stock'] <= 0:
            return ['background-color: #ffebee'] * len(row)  # Light red for out of stock
        elif row['Current Stock'] <= row['Reorder Level']:
            return ['background-color: #fff3e0'] * len(row)  # Light orange for low stock
        else:
            return [''] * len(row)
    
    styled_data = display_columns.style.apply(highlight_stock_levels, axis=1)
    st.dataframe(styled_data, use_container_width=True)
    
    # Export section
    render_export_section(display_data, f"stock_levels_{filter_type.lower().replace(' ', '_')}")

def render_reorder_management(inventory_data: pd.DataFrame):
    """Render reorder management interface"""
    st.markdown("## 🔄 Reorder Management")
    
    # Calculate reorder requirements
    inventory_data['needs_reorder'] = inventory_data['closing_balance'] <= inventory_data['reorder_level']
    reorder_items = inventory_data[inventory_data['needs_reorder'] & (inventory_data['closing_balance'] >= 0)]
    
    # Reorder metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_reorder_items = len(reorder_items)
        st.metric("Items Need Reorder", f"{total_reorder_items:,}")
    
    with col2:
        reorder_value = reorder_items['closing_value'].sum()
        st.metric("Current Value at Risk", format_currency(reorder_value))
    
    with col3:
        critical_items = len(reorder_items[reorder_items['closing_balance'] == 0])
        st.metric("Critical (Zero Stock)", f"{critical_items:,}")
    
    with col4:
        avg_days_stock = inventory_data['closing_balance'].mean() / inventory_data['reorder_level'].mean() if inventory_data['reorder_level'].mean() > 0 else 0
        st.metric("Avg Days of Stock", f"{avg_days_stock:.1f}")
    
    # Reorder priority matrix
    st.markdown("### 🎯 Reorder Priority Matrix")
    
    if not reorder_items.empty:
        # Calculate priority score (based on value and stock level)
        reorder_items = reorder_items.copy()
        reorder_items['stock_ratio'] = reorder_items['closing_balance'] / (reorder_items['reorder_level'] + 0.001)
        reorder_items['priority_score'] = (1 - reorder_items['stock_ratio']) * reorder_items['closing_value']
        
        # Priority categorization
        def get_priority(row):
            if row['closing_balance'] == 0:
                return 'Critical'
            elif row['stock_ratio'] < 0.2:
                return 'High'
            elif row['stock_ratio'] < 0.5:
                return 'Medium'
            else:
                return 'Low'
        
        reorder_items['priority'] = reorder_items.apply(get_priority, axis=1)
        
        # Priority distribution
        col1, col2 = st.columns(2)
        
        with col1:
            priority_counts = reorder_items['priority'].value_counts()
            fig = px.pie(values=priority_counts.values, names=priority_counts.index,
                        title='Reorder Priority Distribution',
                        color_discrete_map={'Critical': '#ff4444', 'High': '#ff8800', 'Medium': '#ffaa00', 'Low': '#88cc00'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Priority vs Value scatter
            fig = px.scatter(reorder_items, x='stock_ratio', y='closing_value', 
                           color='priority', hover_data=['name'],
                           title='Stock Ratio vs Item Value')
            fig.update_layout(xaxis_title='Stock Ratio (Current/Reorder Level)', yaxis_title='Item Value (₹)')
            st.plotly_chart(fig, use_container_width=True)
        
        # Reorder recommendations
        st.markdown("### 📋 Reorder Recommendations")
        
        # Filter by priority
        priority_filter = st.multiselect(
            "Filter by Priority",
            ['Critical', 'High', 'Medium', 'Low'],
            default=['Critical', 'High']
        )
        
        filtered_reorder = reorder_items[reorder_items['priority'].isin(priority_filter)]
        
        if not filtered_reorder.empty:
            # Calculate recommended order quantities
            filtered_reorder['recommended_qty'] = filtered_reorder.apply(
                lambda row: max(row['reorder_level'] * 2 - row['closing_balance'], row['reorder_level']), axis=1
            )
            
            # Estimate order values
            filtered_reorder['estimated_cost'] = filtered_reorder['recommended_qty'] * (
                filtered_reorder['closing_value'] / (filtered_reorder['closing_balance'] + 0.001)
            )
            
            # Display recommendations
            reorder_display = filtered_reorder[['name', 'closing_balance', 'base_unit', 'reorder_level', 
                                             'recommended_qty', 'estimated_cost', 'priority']].copy()
            reorder_display.columns = ['Item Name', 'Current Stock', 'Unit', 'Reorder Level', 
                                     'Recommended Qty', 'Estimated Cost', 'Priority']
            reorder_display['Estimated Cost'] = reorder_display['Estimated Cost'].apply(format_currency)
            
            # Sort by priority and stock ratio
            priority_order = ['Critical', 'High', 'Medium', 'Low']
            reorder_display['priority_rank'] = reorder_display['Priority'].map({p: i for i, p in enumerate(priority_order)})
            reorder_display = reorder_display.sort_values(['priority_rank', 'Current Stock'])
            reorder_display = reorder_display.drop('priority_rank', axis=1)
            
            st.dataframe(reorder_display, use_container_width=True, hide_index=True)
            
            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Email Reorder List"):
                    st.info("Email functionality will be implemented with SMTP configuration")
            
            with col2:
                if st.button("📊 Export Purchase Order"):
                    po_data = reorder_display[['Item Name', 'Recommended Qty', 'Unit', 'Estimated Cost']]
                    excel_data = export_dataframe_to_excel(po_data, "purchase_order.xlsx")
                    st.download_button(
                        label="📥 Download PO",
                        data=excel_data,
                        file_name=f"purchase_order_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col3:
                if st.button("🔄 Generate Alerts"):
                    alert_manager = AlertManager()
                    for _, item in filtered_reorder.head(5).iterrows():
                        alert_manager.add_alert(
                            title=f"Reorder Alert: {item['name']}",
                            message=f"Item needs reordering. Current stock: {item['closing_balance']} {item['base_unit']}",
                            alert_type=AlertType.WARNING,
                            priority=AlertPriority.HIGH if item['priority'] == 'Critical' else AlertPriority.MEDIUM,
                            source="inventory",
                            data={'item_name': item['name'], 'current_stock': item['closing_balance']}
                        )
                    st.success(f"Generated {len(filtered_reorder.head(5))} reorder alerts")
        
        else:
            st.info("No items match the selected priority filters")
    
    else:
        st.success("🎉 No items currently need reordering!")
    
    # Export section
    if not reorder_items.empty:
        render_export_section(reorder_items, "reorder_management")

def render_stock_movement(inventory_data: pd.DataFrame):
    """Render stock movement analysis"""
    st.markdown("## 📊 Stock Movement Analysis")
    
    st.info("📋 Stock movement analysis requires transaction history data from Tally Prime. This view shows current stock status and projected movement patterns.")
    
    # Stock velocity analysis (simplified based on current stock levels)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏃‍♂️ Stock Velocity Categories")
        
        # Categorize items by stock levels as proxy for velocity
        def categorize_velocity(row):
            if row['closing_balance'] == 0:
                return 'No Stock'
            elif row['closing_balance'] <= row['reorder_level'] * 0.5:
                return 'Fast Moving'
            elif row['closing_balance'] <= row['reorder_level']:
                return 'Medium Moving'
            elif row['closing_balance'] > row['reorder_level'] * 3:
                return 'Slow Moving'
            else:
                return 'Normal Moving'
        
        inventory_data['velocity_category'] = inventory_data.apply(categorize_velocity, axis=1)
        velocity_counts = inventory_data['velocity_category'].value_counts()
        
        fig = px.bar(x=velocity_counts.index, y=velocity_counts.values,
                    title='Items by Movement Category')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 Value by Movement Category")
        
        velocity_value = inventory_data.groupby('velocity_category')['closing_value'].sum()
        fig = px.pie(values=velocity_value.values, names=velocity_value.index,
                    title='Stock Value by Movement Category')
        st.plotly_chart(fig, use_container_width=True)
    
    # Stock turnover analysis
    st.markdown("### 🔄 Stock Analysis by Category")
    
    # Group by movement category
    movement_analysis = inventory_data.groupby('velocity_category').agg({
        'name': 'count',
        'closing_balance': ['sum', 'mean'],
        'closing_value': ['sum', 'mean'],
        'reorder_level': 'mean'
    }).round(2)
    
    movement_analysis.columns = ['Item Count', 'Total Stock', 'Avg Stock Level', 'Total Value', 'Avg Value', 'Avg Reorder Level']
    movement_analysis['Total Value'] = movement_analysis['Total Value'].apply(format_currency)
    movement_analysis['Avg Value'] = movement_analysis['Avg Value'].apply(format_currency)
    
    st.dataframe(movement_analysis, use_container_width=True)
    
    # Detailed movement table
    st.markdown("### 📋 Detailed Movement Analysis")
    
    # Filter by movement category
    selected_categories = st.multiselect(
        "Select Movement Categories",
        inventory_data['velocity_category'].unique(),
        default=inventory_data['velocity_category'].unique()
    )
    
    filtered_movement = inventory_data[inventory_data['velocity_category'].isin(selected_categories)]
    
    movement_display = filtered_movement[['name', 'closing_balance', 'base_unit', 'closing_value', 
                                        'reorder_level', 'velocity_category']].copy()
    movement_display.columns = ['Item Name', 'Current Stock', 'Unit', 'Stock Value', 'Reorder Level', 'Movement Category']
    movement_display['Stock Value'] = movement_display['Stock Value'].apply(format_currency)
    
    st.dataframe(movement_display, use_container_width=True, hide_index=True)
    
    # Export section
    render_export_section(filtered_movement, "stock_movement")

def render_inventory_valuation(inventory_data: pd.DataFrame):
    """Render inventory valuation analysis"""
    st.markdown("## 💰 Inventory Valuation")
    
    # Valuation metrics
    total_inventory_value = inventory_data['closing_value'].sum()
    average_item_value = inventory_data['closing_value'].mean()
    median_item_value = inventory_data['closing_value'].median()
    highest_value_item = inventory_data.loc[inventory_data['closing_value'].idxmax()]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Inventory Value", format_currency(total_inventory_value))
    with col2:
        st.metric("Average Item Value", format_currency(average_item_value))
    with col3:
        st.metric("Median Item Value", format_currency(median_item_value))
    with col4:
        st.metric("Highest Value Item", format_currency(highest_value_item['closing_value']))
    
    # Valuation distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Value Distribution")
        
        # Create value buckets
        def value_bucket(value):
            if value < 1000:
                return '< ₹1K'
            elif value < 5000:
                return '₹1K - ₹5K'
            elif value < 10000:
                return '₹5K - ₹10K'
            elif value < 50000:
                return '₹10K - ₹50K'
            else:
                return '> ₹50K'
        
        inventory_data['value_bucket'] = inventory_data['closing_value'].apply(value_bucket)
        value_distribution = inventory_data['value_bucket'].value_counts()
        
        fig = px.bar(x=value_distribution.index, y=value_distribution.values,
                    title='Items by Value Range')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🥧 Value Concentration")
        
        # Show top 10 items by value
        top_value_items = inventory_data.nlargest(10, 'closing_value')
        other_value = total_inventory_value - top_value_items['closing_value'].sum()
        
        # Create pie chart data
        pie_data = top_value_items['closing_value'].tolist() + [other_value]
        pie_labels = top_value_items['name'].tolist() + ['Others']
        
        fig = px.pie(values=pie_data, names=pie_labels,
                    title='Top 10 Items vs Others by Value')
        st.plotly_chart(fig, use_container_width=True)
    
    # Valuation trends (if categories are available)
    if 'category' in inventory_data.columns:
        st.markdown("### 📈 Valuation by Category")
        
        category_valuation = inventory_data.groupby('category').agg({
            'closing_value': ['sum', 'mean', 'count']
        }).round(2)
        category_valuation.columns = ['Total Value', 'Average Value', 'Item Count']
        category_valuation = category_valuation.sort_values('Total Value', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(category_valuation.head(10), x=category_valuation.head(10).index, 
                        y='Total Value', title='Top Categories by Total Value')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(category_valuation, x='Item Count', y='Average Value',
                           hover_data=category_valuation.index,
                           title='Category Analysis: Count vs Avg Value')
            st.plotly_chart(fig, use_container_width=True)
        
        # Category valuation table
        category_valuation['Total Value'] = category_valuation['Total Value'].apply(format_currency)
        category_valuation['Average Value'] = category_valuation['Average Value'].apply(format_currency)
        st.dataframe(category_valuation, use_container_width=True)
    
    # Dead stock analysis
    st.markdown("### 🔍 Dead Stock Analysis")
    
    # Items with zero stock value or very high stock relative to reorder level
    dead_stock_candidates = inventory_data[
        (inventory_data['closing_balance'] == 0) | 
        (inventory_data['closing_balance'] > inventory_data['reorder_level'] * 5)
    ]
    
    if not dead_stock_candidates.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            zero_stock_count = len(dead_stock_candidates[dead_stock_candidates['closing_balance'] == 0])
            st.metric("Zero Stock Items", f"{zero_stock_count:,}")
        
        with col2:
            overstock_count = len(dead_stock_candidates[dead_stock_candidates['closing_balance'] > 0])
            st.metric("Potential Overstock", f"{overstock_count:,}")
        
        # Show dead stock candidates
        dead_stock_display = dead_stock_candidates[['name', 'closing_balance', 'closing_value', 'reorder_level']].copy()
        dead_stock_display.columns = ['Item Name', 'Current Stock', 'Stock Value', 'Reorder Level']
        dead_stock_display['Stock Value'] = dead_stock_display['Stock Value'].apply(format_currency)
        
        st.dataframe(dead_stock_display, use_container_width=True, hide_index=True)
    else:
        st.success("No dead stock identified")
    
    # Export section
    render_export_section(inventory_data, "inventory_valuation")

def render_abc_analysis(inventory_data: pd.DataFrame):
    """Render ABC analysis of inventory"""
    st.markdown("## 📊 ABC Analysis")
    st.markdown("Classify inventory items based on their value contribution (Pareto Analysis)")
    
    # Calculate ABC classification based on value
    inventory_sorted = inventory_data.sort_values('closing_value', ascending=False)
    inventory_sorted['cumulative_value'] = inventory_sorted['closing_value'].cumsum()
    total_value = inventory_sorted['closing_value'].sum()
    inventory_sorted['cumulative_percentage'] = (inventory_sorted['cumulative_value'] / total_value) * 100
    
    # Classify items
    def classify_abc(cum_percentage):
        if cum_percentage <= 80:
            return 'A'
        elif cum_percentage <= 95:
            return 'B'
        else:
            return 'C'
    
    inventory_sorted['abc_category'] = inventory_sorted['cumulative_percentage'].apply(classify_abc)
    
    # ABC Summary
    abc_summary = inventory_sorted.groupby('abc_category').agg({
        'name': 'count',
        'closing_value': 'sum',
        'closing_balance': 'sum'
    }).round(2)
    abc_summary.columns = ['Item Count', 'Total Value', 'Total Stock']
    abc_summary['Value %'] = (abc_summary['Total Value'] / total_value * 100).round(1)
    abc_summary['Item %'] = (abc_summary['Item Count'] / len(inventory_data) * 100).round(1)
    
    st.markdown("### 📋 ABC Classification Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Category A (High Value)")
        a_items = abc_summary.loc['A']
        st.metric("Items", f"{a_items['Item Count']:,.0f} ({a_items['Item %']:.1f}%)")
        st.metric("Value", f"{format_currency(a_items['Total Value'])} ({a_items['Value %']:.1f}%)")
    
    with col2:
        st.markdown("#### Category B (Medium Value)")
        if 'B' in abc_summary.index:
            b_items = abc_summary.loc['B']
            st.metric("Items", f"{b_items['Item Count']:,.0f} ({b_items['Item %']:.1f}%)")
            st.metric("Value", f"{format_currency(b_items['Total Value'])} ({b_items['Value %']:.1f}%)")
        else:
            st.info("No Category B items")
    
    with col3:
        st.markdown("#### Category C (Low Value)")
        if 'C' in abc_summary.index:
            c_items = abc_summary.loc['C']
            st.metric("Items", f"{c_items['Item Count']:,.0f} ({c_items['Item %']:.1f}%)")
            st.metric("Value", f"{format_currency(c_items['Total Value'])} ({c_items['Value %']:.1f}%)")
        else:
            st.info("No Category C items")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 ABC Distribution by Count")
        fig = px.pie(abc_summary, values='Item Count', names=abc_summary.index,
                    title='Item Count Distribution',
                    color_discrete_map={'A': '#ff6b6b', 'B': '#ffd93d', 'C': '#6bcf7f'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 ABC Distribution by Value")
        fig = px.pie(abc_summary, values='Total Value', names=abc_summary.index,
                    title='Value Distribution',
                    color_discrete_map={'A': '#ff6b6b', 'B': '#ffd93d', 'C': '#6bcf7f'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Pareto Chart
    st.markdown("### 📈 Pareto Analysis")
    
    fig = go.Figure()
    
    # Bar chart for individual values
    fig.add_trace(go.Bar(
        x=list(range(len(inventory_sorted))),
        y=inventory_sorted['closing_value'],
        name='Item Value',
        marker_color='lightblue'
    ))
    
    # Line chart for cumulative percentage
    fig.add_trace(go.Scatter(
        x=list(range(len(inventory_sorted))),
        y=inventory_sorted['cumulative_percentage'],
        mode='lines',
        name='Cumulative %',
        yaxis='y2',
        line=dict(color='red', width=2)
    ))
    
    # Add reference lines
    fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="80%")
    fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="95%")
    
    fig.update_layout(
        title='Pareto Chart - Item Value vs Cumulative Percentage',
        xaxis_title='Items (Ranked by Value)',
        yaxis=dict(title='Item Value (₹)', side='left'),
        yaxis2=dict(title='Cumulative Percentage (%)', side='right', overlaying='y'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed ABC tables
    st.markdown("### 📋 Detailed ABC Analysis")
    
    # Category filter
    selected_category = st.selectbox("Select Category for Details", ['A', 'B', 'C'])
    
    category_items = inventory_sorted[inventory_sorted['abc_category'] == selected_category]
    
    if not category_items.empty:
        category_display = category_items[['name', 'closing_balance', 'closing_value', 
                                         'cumulative_percentage', 'abc_category']].copy()
        category_display.columns = ['Item Name', 'Stock Quantity', 'Stock Value', 
                                   'Cumulative %', 'ABC Category']
        category_display['Stock Value'] = category_display['Stock Value'].apply(format_currency)
        category_display['Cumulative %'] = category_display['Cumulative %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(category_display, use_container_width=True, hide_index=True)
        
        # Management recommendations
        st.markdown(f"### 💡 Management Recommendations for Category {selected_category}")
        
        if selected_category == 'A':
            st.info("""
            **High-Priority Items (Category A)**
            - Monitor stock levels closely with frequent reviews
            - Maintain safety stock to avoid stockouts
            - Negotiate better terms with suppliers
            - Consider just-in-time inventory management
            - Implement tight inventory controls
            """)
        elif selected_category == 'B':
            st.info("""
            **Medium-Priority Items (Category B)**
            - Regular monitoring with periodic reviews
            - Moderate safety stock levels
            - Standard ordering procedures
            - Good supplier relationships
            - Balanced inventory investment
            """)
        else:  # Category C
            st.info("""
            **Low-Priority Items (Category C)**
            - Simple controls and less frequent monitoring
            - Higher stock levels acceptable
            - Bulk ordering to reduce administrative costs
            - Review for obsolete or slow-moving items
            - Consider discontinuation of very slow movers
            """)
    else:
        st.info(f"No items in Category {selected_category}")
    
    # Export section
    render_export_section(inventory_sorted, "abc_analysis")

def render_export_section(data: pd.DataFrame, report_name: str):
    """Render export options for inventory reports"""
    st.markdown("---")
    st.markdown("### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export to Excel", key=f"excel_{report_name}"):
            try:
                excel_data = export_dataframe_to_excel(data, f"{report_name}_{datetime.now().strftime('%Y%m%d')}.xlsx")
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name=f"{report_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Export error: {str(e)}")
    
    with col2:
        csv_data = data.to_csv(index=False)
        st.download_button(
            label="📄 Export to CSV",
            data=csv_data,
            file_name=f"{report_name}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col3:
        if st.button("📧 Email Report", key=f"email_{report_name}"):
            st.info("Email functionality will be implemented with SMTP configuration")

if __name__ == "__main__":
    main()
