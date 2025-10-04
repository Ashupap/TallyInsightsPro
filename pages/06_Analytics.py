import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from src.auth import require_auth, check_permission
from src.tally_api import TallyAPIClient, fetch_cached_sales_data, fetch_cached_inventory_data
from src.analytics import (
    AdvancedAnalytics, render_sales_forecasting, render_customer_segmentation,
    render_seasonal_analysis, render_root_cause_analysis, calculate_kpis
)
from src.utils import load_custom_css, format_currency, get_date_range_options, export_dataframe_to_excel

# Page configuration
st.set_page_config(
    page_title="Advanced Analytics - Tally Prime Analytics",
    page_icon="🧠",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main analytics page with advanced business intelligence"""
    
    st.title("🧠 Advanced Analytics")
    st.markdown("### AI-powered insights and predictive analysis")
    
    # Check permissions
    if not check_permission('analytics'):
        st.error("You don't have permission to access advanced analytics")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ Analytics Controls")
        
        # Analytics type selection
        analytics_type = st.selectbox(
            "📊 Analysis Type",
            [
                "Analytics Dashboard", 
                "Sales Forecasting", 
                "Customer Segmentation", 
                "Product Analysis", 
                "Seasonal Patterns",
                "Performance KPIs",
                "Root Cause Analysis",
                "Predictive Insights"
            ]
        )
        
        # Date range for analysis
        st.markdown("---")
        st.markdown("#### Analysis Period")
        
        date_options = get_date_range_options()
        selected_range = st.selectbox(
            "📅 Date Range",
            options=list(date_options.keys()),
            index=6  # Default to "This Quarter"
        )
        
        if selected_range == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                from_date = st.date_input("From Date", datetime.now() - timedelta(days=90))
            with col2:
                to_date = st.date_input("To Date", datetime.now())
        else:
            from_date, to_date = date_options[selected_range]
        
        # Analysis parameters
        st.markdown("---")
        st.markdown("#### Analysis Settings")
        
        # Forecast parameters
        if analytics_type == "Sales Forecasting":
            forecast_days = st.slider("Forecast Period (days)", 7, 90, 30)
            confidence_level = st.slider("Confidence Level (%)", 80, 99, 95)
        
        # Segmentation parameters
        if analytics_type == "Customer Segmentation":
            segment_method = st.selectbox("Segmentation Method", ["RFM Analysis", "Value-based", "Frequency-based"])
            num_segments = st.slider("Number of Segments", 3, 6, 4)
        
        # Generate analysis button
        run_analysis = st.button("🔍 Run Analysis", type="primary")
        
        # Quick actions
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("📊 Export Analysis"):
            st.info("Export functionality will be available after running analysis")
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.success("Data cache cleared!")
            st.rerun()
        
        if st.button("📧 Schedule Report"):
            st.info("Report scheduling will be implemented with task scheduler")
    
    # Main content area
    if run_analysis or st.session_state.get('auto_load_analytics', False):
        
        # Get Tally client and data
        tally_server = st.session_state.get('tally_server')
        if not tally_server:
            st.error("Tally server not configured. Please check your settings.")
            return
        
        try:
            with st.spinner("Loading data for analysis..."):
                # Fetch required data
                sales_data = fetch_cached_sales_data(
                    tally_server,
                    from_date.strftime('%d-%b-%Y'),
                    to_date.strftime('%d-%b-%Y')
                )
                
                inventory_data = fetch_cached_inventory_data(tally_server)
                
                client = TallyAPIClient(tally_server)
                outstanding_data = client.get_outstanding_data()
                
                # Initialize analytics engine
                analytics = AdvancedAnalytics()
            
            # Process analysis based on selection
            if analytics_type == "Analytics Dashboard":
                render_analytics_dashboard(analytics, sales_data, inventory_data, outstanding_data)
            
            elif analytics_type == "Sales Forecasting":
                render_sales_forecasting(analytics, sales_data)
            
            elif analytics_type == "Customer Segmentation":
                render_customer_segmentation(analytics, sales_data)
            
            elif analytics_type == "Product Analysis":
                render_product_trend_analysis(analytics, sales_data)
            
            elif analytics_type == "Seasonal Patterns":
                render_seasonal_analysis(analytics, sales_data)
            
            elif analytics_type == "Performance KPIs":
                render_performance_kpis(sales_data, inventory_data, outstanding_data)
            
            elif analytics_type == "Root Cause Analysis":
                render_root_cause_analysis(sales_data, inventory_data)
            
            elif analytics_type == "Predictive Insights":
                render_predictive_insights(analytics, sales_data, inventory_data)
                
        except Exception as e:
            st.error(f"Error running analysis: {str(e)}")
            st.info("Please ensure Tally Prime is running and data is available for the selected period.")
    
    else:
        # Show analytics overview
        show_analytics_overview()

def render_analytics_dashboard(analytics: AdvancedAnalytics, sales_data: pd.DataFrame, 
                             inventory_data: pd.DataFrame, outstanding_data: pd.DataFrame):
    """Render comprehensive analytics dashboard"""
    st.markdown("## 📊 Analytics Dashboard")
    
    if sales_data.empty and inventory_data.empty:
        st.warning("No data available for analysis. Please check your Tally connection and data availability.")
        return
    
    # Key Performance Indicators
    st.markdown("### 🎯 Key Performance Indicators")
    
    kpis = calculate_kpis(sales_data, inventory_data, outstanding_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'total_sales' in kpis:
            st.metric("Total Sales", format_currency(kpis['total_sales']))
        else:
            st.metric("Total Sales", "₹0")
    
    with col2:
        if 'avg_transaction_value' in kpis:
            st.metric("Avg Transaction", format_currency(kpis['avg_transaction_value']))
        else:
            st.metric("Avg Transaction", "₹0")
    
    with col3:
        if 'total_inventory_value' in kpis:
            st.metric("Inventory Value", format_currency(kpis['total_inventory_value']))
        else:
            st.metric("Inventory Value", "₹0")
    
    with col4:
        if 'total_receivables' in kpis:
            st.metric("Receivables", format_currency(kpis['total_receivables']))
        else:
            st.metric("Receivables", "₹0")
    
    # Advanced Analytics Tiles
    col1, col2 = st.columns(2)
    
    with col1:
        if not sales_data.empty:
            st.markdown("### 🔮 Sales Forecast Preview")
            forecast_result = analytics.sales_forecasting(sales_data, 7)  # 7-day preview
            
            if 'error' not in forecast_result:
                # Show quick forecast chart
                historical = forecast_result['historical_data'].tail(14)  # Last 14 days
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=historical['date'],
                    y=historical['amount'],
                    mode='lines+markers',
                    name='Historical',
                    line=dict(color='blue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=forecast_result['forecast_dates'][:7],
                    y=forecast_result['forecast_values'][:7],
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='red', dash='dash')
                ))
                
                fig.update_layout(title="7-Day Sales Forecast", height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data for forecasting")
        else:
            st.info("No sales data available for forecasting")
    
    with col2:
        if not sales_data.empty:
            st.markdown("### 👥 Customer Segments Preview")
            segmentation_result = analytics.customer_segmentation(sales_data)
            
            if 'error' not in segmentation_result:
                segment_stats = segmentation_result['segment_stats']
                
                fig = px.pie(
                    values=segment_stats['customer'],
                    names=segment_stats.index,
                    title='Customer Segments'
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data for segmentation")
        else:
            st.info("No sales data available for segmentation")
    
    # Business Intelligence Insights
    st.markdown("### 🧠 Business Intelligence Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📈 Growth Insights")
        if not sales_data.empty and len(sales_data) > 1:
            # Calculate growth metrics
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            recent_sales = sales_data['amount'].tail(7).mean()
            previous_sales = sales_data['amount'].head(7).mean() if len(sales_data) > 14 else recent_sales
            
            if previous_sales > 0:
                growth_rate = ((recent_sales - previous_sales) / previous_sales) * 100
                if growth_rate > 0:
                    st.success(f"📈 Sales growing by {growth_rate:.1f}%")
                else:
                    st.warning(f"📉 Sales declining by {abs(growth_rate):.1f}%")
            else:
                st.info("Growth analysis needs more historical data")
        else:
            st.info("Insufficient data for growth analysis")
    
    with col2:
        st.markdown("#### 🎯 Efficiency Metrics")
        if 'low_stock_items' in kpis and kpis.get('inventory_items', 0) > 0:
            stock_efficiency = (1 - (kpis['low_stock_items'] / kpis['inventory_items'])) * 100
            if stock_efficiency >= 90:
                st.success(f"✅ Stock efficiency: {stock_efficiency:.1f}%")
            elif stock_efficiency >= 70:
                st.warning(f"⚠️ Stock efficiency: {stock_efficiency:.1f}%")
            else:
                st.error(f"🚨 Stock efficiency: {stock_efficiency:.1f}%")
        else:
            st.info("Stock efficiency data not available")
    
    with col3:
        st.markdown("#### 💰 Cash Flow Health")
        if 'total_receivables' in kpis and 'total_sales' in kpis:
            if kpis['total_sales'] > 0:
                receivables_ratio = (kpis['total_receivables'] / kpis['total_sales']) * 100
                if receivables_ratio <= 30:
                    st.success(f"💚 Healthy receivables: {receivables_ratio:.1f}%")
                elif receivables_ratio <= 50:
                    st.warning(f"🟡 Moderate receivables: {receivables_ratio:.1f}%")
                else:
                    st.error(f"🔴 High receivables: {receivables_ratio:.1f}%")
            else:
                st.info("No sales data for cash flow analysis")
        else:
            st.info("Cash flow data not available")
    
    # Trend Analysis
    if not sales_data.empty:
        st.markdown("### 📊 Trend Analysis")
        
        # Create trend analysis
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        daily_sales = sales_data.groupby(sales_data['date'].dt.date)['amount'].sum().reset_index()
        
        if len(daily_sales) > 7:
            # Calculate moving average
            daily_sales['MA7'] = daily_sales['amount'].rolling(window=7).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_sales['date'],
                y=daily_sales['amount'],
                mode='lines',
                name='Daily Sales',
                line=dict(color='lightblue')
            ))
            
            fig.add_trace(go.Scatter(
                x=daily_sales['date'],
                y=daily_sales['MA7'],
                mode='lines',
                name='7-day Moving Average',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(title="Sales Trend Analysis", height=400)
            st.plotly_chart(fig, use_container_width=True)

def render_product_trend_analysis(analytics: AdvancedAnalytics, sales_data: pd.DataFrame):
    """Render product trend analysis"""
    st.markdown("## 📦 Product Trend Analysis")
    
    if sales_data.empty:
        st.warning("No sales data available for product analysis")
        return
    
    with st.spinner("Analyzing product trends..."):
        product_result = analytics.product_trend_analysis(sales_data)
    
    if 'error' in product_result:
        st.error(product_result['error'])
        return
    
    # Product performance overview
    product_analysis = product_result['product_analysis']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_products = len(product_analysis)
        st.metric("Total Products", f"{total_products:,}")
    
    with col2:
        if not product_analysis.empty:
            avg_product_sales = product_analysis['total_sales'].mean()
            st.metric("Avg Product Sales", format_currency(avg_product_sales))
    
    with col3:
        if 'fast_movers' in product_result:
            fast_movers_count = len(product_result['fast_movers'])
            st.metric("Fast Moving Products", f"{fast_movers_count:,}")
    
    # Product performance visualization
    if not product_analysis.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 Top Performing Products")
            top_products = product_analysis.head(10)
            
            fig = px.bar(top_products, x='product', y='total_sales',
                        title='Top 10 Products by Sales')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Product Category Distribution")
            
            category_dist = product_analysis['category'].value_counts()
            fig = px.pie(values=category_dist.values, names=category_dist.index,
                        title='Products by Category')
            st.plotly_chart(fig, use_container_width=True)
    
    # Fast vs Slow movers
    col1, col2 = st.columns(2)
    
    with col1:
        if 'fast_movers' in product_result and not product_result['fast_movers'].empty:
            st.markdown("### 🚀 Fast Moving Products")
            fast_movers = product_result['fast_movers'][['product', 'total_sales', 'transaction_count']]
            fast_movers['total_sales'] = fast_movers['total_sales'].apply(format_currency)
            st.dataframe(fast_movers, use_container_width=True, hide_index=True)
        else:
            st.info("No fast-moving products identified")
    
    with col2:
        if 'slow_movers' in product_result and not product_result['slow_movers'].empty:
            st.markdown("### 🐌 Slow Moving Products")
            slow_movers = product_result['slow_movers'][['product', 'total_sales', 'transaction_count']]
            slow_movers['total_sales'] = slow_movers['total_sales'].apply(format_currency)
            st.dataframe(slow_movers, use_container_width=True, hide_index=True)
        else:
            st.info("No slow-moving products identified")

def render_performance_kpis(sales_data: pd.DataFrame, inventory_data: pd.DataFrame, outstanding_data: pd.DataFrame):
    """Render performance KPIs dashboard"""
    st.markdown("## 🎯 Performance KPIs")
    
    # Calculate comprehensive KPIs
    kpis = calculate_kpis(sales_data, inventory_data, outstanding_data)
    
    # Sales Performance KPIs
    st.markdown("### 📈 Sales Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'total_sales' in kpis:
            st.metric("Total Revenue", format_currency(kpis['total_sales']))
        else:
            st.metric("Total Revenue", "₹0")
    
    with col2:
        if 'sales_count' in kpis and kpis['sales_count'] > 0:
            st.metric("Total Transactions", f"{kpis['sales_count']:,}")
        else:
            st.metric("Total Transactions", "0")
    
    with col3:
        if 'avg_transaction_value' in kpis:
            st.metric("Avg Transaction Value", format_currency(kpis['avg_transaction_value']))
        else:
            st.metric("Avg Transaction Value", "₹0")
    
    with col4:
        # Calculate sales growth if possible
        if not sales_data.empty and len(sales_data) > 1:
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            recent_period = sales_data['amount'].tail(len(sales_data)//2).sum()
            earlier_period = sales_data['amount'].head(len(sales_data)//2).sum()
            
            if earlier_period > 0:
                growth_rate = ((recent_period - earlier_period) / earlier_period) * 100
                st.metric("Sales Growth", f"{growth_rate:.1f}%")
            else:
                st.metric("Sales Growth", "N/A")
        else:
            st.metric("Sales Growth", "N/A")
    
    # Inventory Performance KPIs
    st.markdown("### 📦 Inventory Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'total_inventory_value' in kpis:
            st.metric("Inventory Value", format_currency(kpis['total_inventory_value']))
        else:
            st.metric("Inventory Value", "₹0")
    
    with col2:
        if 'inventory_items' in kpis:
            st.metric("Total SKUs", f"{kpis['inventory_items']:,}")
        else:
            st.metric("Total SKUs", "0")
    
    with col3:
        if 'low_stock_items' in kpis:
            st.metric("Low Stock Items", f"{kpis['low_stock_items']:,}")
        else:
            st.metric("Low Stock Items", "0")
    
    with col4:
        # Calculate inventory turnover ratio
        if 'total_sales' in kpis and 'total_inventory_value' in kpis and kpis['total_inventory_value'] > 0:
            inventory_turnover = kpis['total_sales'] / kpis['total_inventory_value']
            st.metric("Inventory Turnover", f"{inventory_turnover:.2f}x")
        else:
            st.metric("Inventory Turnover", "N/A")
    
    # Financial Health KPIs
    st.markdown("### 💰 Financial Health")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'total_receivables' in kpis:
            st.metric("Total Receivables", format_currency(kpis['total_receivables']))
        else:
            st.metric("Total Receivables", "₹0")
    
    with col2:
        if 'overdue_customers' in kpis:
            st.metric("Overdue Customers", f"{kpis['overdue_customers']:,}")
        else:
            st.metric("Overdue Customers", "0")
    
    with col3:
        # Calculate days sales outstanding
        if 'total_receivables' in kpis and 'total_sales' in kpis and kpis['total_sales'] > 0:
            # Simplified DSO calculation (assumes 30-day period)
            dso = (kpis['total_receivables'] / kpis['total_sales']) * 30
            st.metric("Days Sales Outstanding", f"{dso:.0f} days")
        else:
            st.metric("Days Sales Outstanding", "N/A")
    
    with col4:
        # Calculate collection efficiency
        if 'total_sales' in kpis and 'total_receivables' in kpis and kpis['total_sales'] > 0:
            collection_efficiency = ((kpis['total_sales'] - kpis['total_receivables']) / kpis['total_sales']) * 100
            st.metric("Collection Efficiency", f"{collection_efficiency:.1f}%")
        else:
            st.metric("Collection Efficiency", "N/A")
    
    # KPI Trends Visualization
    if not sales_data.empty:
        st.markdown("### 📊 KPI Trends")
        
        # Create KPI trend chart
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        
        # Weekly aggregation for trends
        weekly_sales = sales_data.groupby(sales_data['date'].dt.to_period('W')).agg({
            'amount': 'sum',
            'voucher_number': 'count'
        }).reset_index()
        
        weekly_sales['avg_transaction'] = weekly_sales['amount'] / weekly_sales['voucher_number']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Weekly Sales', 'Transaction Count', 'Average Transaction Value', 'Cumulative Sales'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Weekly sales
        fig.add_trace(
            go.Scatter(x=weekly_sales['date'].astype(str), y=weekly_sales['amount'],
                      mode='lines+markers', name='Weekly Sales'),
            row=1, col=1
        )
        
        # Transaction count
        fig.add_trace(
            go.Scatter(x=weekly_sales['date'].astype(str), y=weekly_sales['voucher_number'],
                      mode='lines+markers', name='Transactions'),
            row=1, col=2
        )
        
        # Average transaction value
        fig.add_trace(
            go.Scatter(x=weekly_sales['date'].astype(str), y=weekly_sales['avg_transaction'],
                      mode='lines+markers', name='Avg Transaction'),
            row=2, col=1
        )
        
        # Cumulative sales
        cumulative_sales = weekly_sales['amount'].cumsum()
        fig.add_trace(
            go.Scatter(x=weekly_sales['date'].astype(str), y=cumulative_sales,
                      mode='lines+markers', name='Cumulative Sales'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def render_predictive_insights(analytics: AdvancedAnalytics, sales_data: pd.DataFrame, inventory_data: pd.DataFrame):
    """Render predictive insights and recommendations"""
    st.markdown("## 🔮 Predictive Insights")
    
    if sales_data.empty:
        st.warning("No sales data available for predictive analysis")
        return
    
    # Sales Prediction
    st.markdown("### 📈 Sales Predictions")
    
    with st.spinner("Generating sales predictions..."):
        forecast_result = analytics.sales_forecasting(sales_data, 30)
    
    if 'error' not in forecast_result:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            next_week_sales = sum(forecast_result['forecast_values'][:7])
            st.metric("Next 7 Days Forecast", format_currency(next_week_sales))
        
        with col2:
            next_month_sales = sum(forecast_result['forecast_values'])
            st.metric("Next 30 Days Forecast", format_currency(next_month_sales))
        
        with col3:
            model_accuracy = forecast_result.get('model_accuracy', 0) * 100
            st.metric("Prediction Accuracy", f"{model_accuracy:.1f}%")
        
        # Forecast visualization
        historical = forecast_result['historical_data']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical['date'],
            y=historical['amount'],
            mode='lines+markers',
            name='Historical Sales',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_result['forecast_dates'],
            y=forecast_result['forecast_values'],
            mode='lines+markers',
            name='Predicted Sales',
            line=dict(color='red', dash='dash')
        ))
        
        # Add confidence intervals
        fig.add_trace(go.Scatter(
            x=forecast_result['forecast_dates'],
            y=forecast_result['confidence_upper'],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_result['forecast_dates'],
            y=forecast_result['confidence_lower'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='Confidence Interval',
            fillcolor='rgba(255,0,0,0.2)'
        ))
        
        fig.update_layout(title="30-Day Sales Forecast", height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.error(forecast_result['error'])
    
    # Business Recommendations
    st.markdown("### 💡 AI-Powered Recommendations")
    
    recommendations = generate_business_recommendations(sales_data, inventory_data, forecast_result if 'error' not in forecast_result else None)
    
    for i, recommendation in enumerate(recommendations, 1):
        with st.expander(f"Recommendation {i}: {recommendation['title']}"):
            st.write(recommendation['description'])
            
            if 'metrics' in recommendation:
                cols = st.columns(len(recommendation['metrics']))
                for j, (metric, value) in enumerate(recommendation['metrics'].items()):
                    with cols[j]:
                        st.metric(metric, value)
            
            if 'action' in recommendation:
                st.info(f"**Action:** {recommendation['action']}")

def generate_business_recommendations(sales_data: pd.DataFrame, inventory_data: pd.DataFrame, forecast_result: dict = None):
    """Generate AI-powered business recommendations"""
    recommendations = []
    
    # Sales trend recommendation
    if not sales_data.empty and len(sales_data) > 14:
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        recent_sales = sales_data.tail(7)['amount'].mean()
        earlier_sales = sales_data.head(7)['amount'].mean()
        
        if recent_sales > earlier_sales * 1.1:  # 10% growth
            recommendations.append({
                'title': 'Capitalize on Sales Growth',
                'description': 'Your sales are showing strong upward momentum. Consider expanding marketing efforts and inventory levels.',
                'metrics': {'Growth Rate': f"{((recent_sales - earlier_sales) / earlier_sales * 100):.1f}%"},
                'action': 'Increase marketing budget and stock levels for high-performing products'
            })
        elif recent_sales < earlier_sales * 0.9:  # 10% decline
            recommendations.append({
                'title': 'Address Sales Decline',
                'description': 'Sales have declined recently. Review pricing, competition, and customer feedback.',
                'metrics': {'Decline Rate': f"{((earlier_sales - recent_sales) / earlier_sales * 100):.1f}%"},
                'action': 'Conduct market analysis and consider promotional activities'
            })
    
    # Inventory recommendation
    if not inventory_data.empty:
        low_stock_items = len(inventory_data[inventory_data['closing_balance'] <= inventory_data['reorder_level']])
        total_items = len(inventory_data)
        
        if low_stock_items > total_items * 0.2:  # More than 20% low stock
            recommendations.append({
                'title': 'Optimize Inventory Management',
                'description': 'A significant portion of your inventory is running low. Implement better forecasting and reorder processes.',
                'metrics': {'Low Stock Items': f"{low_stock_items}", 'Percentage': f"{(low_stock_items/total_items*100):.1f}%"},
                'action': 'Review reorder levels and implement automated purchasing for critical items'
            })
    
    # Forecast-based recommendation
    if forecast_result and 'forecast_values' in forecast_result:
        avg_historical = forecast_result['historical_data']['amount'].mean()
        avg_forecast = sum(forecast_result['forecast_values']) / len(forecast_result['forecast_values'])
        
        if avg_forecast > avg_historical * 1.05:  # 5% increase predicted
            recommendations.append({
                'title': 'Prepare for Increased Demand',
                'description': 'Our AI model predicts higher sales in the coming period. Prepare inventory and resources accordingly.',
                'metrics': {'Predicted Increase': f"{((avg_forecast - avg_historical) / avg_historical * 100):.1f}%"},
                'action': 'Increase inventory levels and ensure adequate staffing'
            })
    
    # Customer concentration recommendation
    if not sales_data.empty and 'party_name' in sales_data.columns:
        customer_sales = sales_data.groupby('party_name')['amount'].sum()
        top_customer_share = customer_sales.max() / customer_sales.sum()
        
        if top_customer_share > 0.3:  # Top customer > 30% of sales
            recommendations.append({
                'title': 'Diversify Customer Base',
                'description': 'Your business is heavily dependent on a few key customers. Consider strategies to diversify your customer base.',
                'metrics': {'Top Customer Share': f"{top_customer_share*100:.1f}%"},
                'action': 'Develop new customer acquisition strategies and reduce dependency risk'
            })
    
    # Default recommendation if none generated
    if not recommendations:
        recommendations.append({
            'title': 'Continue Monitoring Performance',
            'description': 'Your business metrics appear stable. Continue monitoring key performance indicators and market trends.',
            'action': 'Maintain current strategies while staying alert to market changes'
        })
    
    return recommendations

def show_analytics_overview():
    """Show analytics overview when no analysis is selected"""
    st.markdown("## 🚀 Advanced Analytics Overview")
    st.markdown("Leverage AI and machine learning for deeper business insights and predictive analysis.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📊 Analytics Dashboard**
        - Comprehensive KPI overview
        - Real-time business intelligence
        - Trend analysis and insights
        """)
        
        st.info("""
        **🔮 Sales Forecasting**
        - AI-powered sales predictions
        - Confidence intervals and accuracy metrics
        - 7-90 day forecasting horizon
        """)
        
        st.info("""
        **👥 Customer Segmentation**
        - RFM analysis and behavioral clustering
        - Customer lifetime value analysis
        - Targeted marketing insights
        """)
        
        st.info("""
        **📦 Product Analysis**
        - Fast vs slow-moving product identification
        - Product performance trends
        - Category-wise analysis
        """)
    
    with col2:
        st.info("""
        **📅 Seasonal Patterns**
        - Monthly and quarterly trends
        - Seasonal demand analysis
        - Holiday and event impact
        """)
        
        st.info("""
        **🎯 Performance KPIs**
        - Sales, inventory, and financial metrics
        - Efficiency and productivity ratios
        - Growth and trend indicators
        """)
        
        st.info("""
        **🔍 Root Cause Analysis**
        - Performance variance investigation
        - Impact factor identification
        - Business insight generation
        """)
        
        st.info("""
        **🔮 Predictive Insights**
        - AI-powered business recommendations
        - Risk and opportunity identification
        - Strategic planning support
        """)
    
    # Quick start guide
    st.markdown("### 🚀 Quick Start Guide")
    
    st.markdown("""
    1. **Select Analysis Type**: Choose from the sidebar menu
    2. **Set Date Range**: Define the period for analysis
    3. **Configure Parameters**: Adjust settings as needed
    4. **Run Analysis**: Click the analysis button
    5. **Review Insights**: Examine results and recommendations
    6. **Export Results**: Save analysis for reporting
    """)
    
    # Sample insights (placeholder for when no data is available)
    st.markdown("### 🧠 Sample Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("✅ **Sales Growth Detected**\nLast 7 days show 12% increase")
    
    with col2:
        st.warning("⚠️ **Inventory Alert**\n15 items below reorder level")
    
    with col3:
        st.info("💡 **Opportunity**\nCustomer segment expansion potential identified")

if __name__ == "__main__":
    main()
