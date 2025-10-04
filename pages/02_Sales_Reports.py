import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from src.auth import require_auth, check_permission
from src.reports import render_sales_report_page, ReportGenerator
from src.tally_api import TallyAPIClient, fetch_cached_sales_data
from src.utils import load_custom_css, format_currency, get_date_range_options, export_dataframe_to_excel
from src.analytics import AdvancedAnalytics, render_customer_segmentation

# Page configuration
st.set_page_config(
    page_title="Sales Reports - Tally Prime Analytics",
    page_icon="📈",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main sales reports page"""
    
    st.title("📈 Sales Reports & Analysis")
    st.markdown("### Comprehensive sales performance insights")
    
    # Check permissions
    if not check_permission('view_reports'):
        st.error("You don't have permission to view sales reports")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🎛️ Report Filters")
        
        # Date range selection
        date_options = get_date_range_options()
        selected_range = st.selectbox(
            "📅 Date Range",
            options=list(date_options.keys()),
            index=2  # Default to "Last 7 Days"
        )
        
        if selected_range == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                from_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
            with col2:
                to_date = st.date_input("To Date", datetime.now())
        else:
            from_date, to_date = date_options[selected_range]
        
        # Report type selection
        report_type = st.selectbox(
            "📊 Report Type",
            ["Sales Summary", "Customer Analysis", "Product Analysis", "Sales Trend", "Regional Analysis"]
        )
        
        # Group by options
        if report_type in ["Sales Summary", "Sales Trend"]:
            group_by = st.selectbox(
                "Group By",
                ["Daily", "Weekly", "Monthly", "Customer", "Product"]
            )
        
        # Additional filters
        st.markdown("---")
        st.markdown("#### Additional Filters")
        
        # Customer filter (would be populated from actual data)
        customer_filter = st.multiselect(
            "Customers",
            options=[],  # Would be populated from Tally data
            help="Select specific customers to filter"
        )
        
        # Product category filter
        category_filter = st.multiselect(
            "Product Categories",
            options=[],  # Would be populated from Tally data
            help="Select product categories to filter"
        )
        
        # Generate report button
        generate_report = st.button("📊 Generate Report", type="primary")
    
    # Main content area
    if generate_report or st.session_state.get('auto_load_sales', False):
        
        # Get Tally client
        tally_server = st.session_state.get('tally_server')
        if not tally_server:
            st.error("Tally server not configured. Please check your settings.")
            return
        
        try:
            with st.spinner("Generating sales report..."):
                # Fetch sales data
                sales_data = fetch_cached_sales_data(
                    tally_server,
                    from_date.strftime('%d-%b-%Y'),
                    to_date.strftime('%d-%b-%Y')
                )
                
                if sales_data.empty:
                    st.warning("No sales data found for the selected period.")
                    return
                
                # Process data based on report type
                if report_type == "Sales Summary":
                    render_sales_summary_report(sales_data, from_date, to_date, group_by)
                
                elif report_type == "Customer Analysis":
                    render_customer_analysis_report(sales_data)
                
                elif report_type == "Product Analysis":
                    render_product_analysis_report(sales_data)
                
                elif report_type == "Sales Trend":
                    render_sales_trend_report(sales_data, group_by)
                
                elif report_type == "Regional Analysis":
                    render_regional_analysis_report(sales_data)
                
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
    
    else:
        # Show welcome message and instructions
        st.info("👈 Use the sidebar to configure and generate your sales report")
        
        # Show quick stats if data is available
        show_quick_sales_overview()

def render_sales_summary_report(sales_data: pd.DataFrame, from_date, to_date, group_by: str):
    """Render sales summary report"""
    st.markdown("## 📊 Sales Summary Report")
    st.markdown(f"**Period:** {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}")
    
    # Summary metrics
    total_sales = sales_data['amount'].sum()
    total_transactions = len(sales_data)
    avg_transaction = sales_data['amount'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", format_currency(total_sales))
    with col2:
        st.metric("Transactions", f"{total_transactions:,}")
    with col3:
        st.metric("Avg Transaction", format_currency(avg_transaction))
    with col4:
        unique_customers = sales_data['party_name'].nunique() if 'party_name' in sales_data.columns else 0
        st.metric("Customers", f"{unique_customers:,}")
    
    # Sales trend chart
    st.markdown("### 📈 Sales Trend")
    
    sales_data['date'] = pd.to_datetime(sales_data['date'])
    
    if group_by.lower() == "daily":
        grouped_data = sales_data.groupby(sales_data['date'].dt.date)['amount'].sum().reset_index()
        x_col, title_suffix = 'date', 'Daily'
    elif group_by.lower() == "weekly":
        sales_data['week'] = sales_data['date'].dt.to_period('W')
        grouped_data = sales_data.groupby('week')['amount'].sum().reset_index()
        x_col, title_suffix = 'week', 'Weekly'
    elif group_by.lower() == "monthly":
        sales_data['month'] = sales_data['date'].dt.to_period('M')
        grouped_data = sales_data.groupby('month')['amount'].sum().reset_index()
        x_col, title_suffix = 'month', 'Monthly'
    elif group_by.lower() == "customer":
        grouped_data = sales_data.groupby('party_name')['amount'].sum().nlargest(10).reset_index()
        x_col, title_suffix = 'party_name', 'by Customer (Top 10)'
    else:  # product
        if 'stock_item' in sales_data.columns:
            grouped_data = sales_data.groupby('stock_item')['amount'].sum().nlargest(10).reset_index()
            x_col, title_suffix = 'stock_item', 'by Product (Top 10)'
        else:
            st.warning("Product information not available in sales data")
            return
    
    fig = px.line(grouped_data, x=x_col, y='amount', 
                  title=f'{title_suffix} Sales Trend',
                  labels={'amount': 'Sales Amount (₹)', x_col: x_col.replace('_', ' ').title()})
    
    if group_by.lower() in ["customer", "product"]:
        fig = px.bar(grouped_data, x=x_col, y='amount',
                     title=f'{title_suffix} Sales',
                     labels={'amount': 'Sales Amount (₹)', x_col: x_col.replace('_', ' ').title()})
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top customers/products table
    if group_by.lower() != "customer":
        st.markdown("### 👥 Top Customers")
        if 'party_name' in sales_data.columns:
            top_customers = sales_data.groupby('party_name')['amount'].agg(['sum', 'count']).reset_index()
            top_customers.columns = ['Customer', 'Total Sales', 'Transactions']
            top_customers = top_customers.sort_values('Total Sales', ascending=False).head(10)
            top_customers['Total Sales'] = top_customers['Total Sales'].apply(format_currency)
            st.dataframe(top_customers, use_container_width=True)
    
    # Export options
    render_export_section(sales_data, "sales_summary")

def render_customer_analysis_report(sales_data: pd.DataFrame):
    """Render customer analysis report"""
    st.markdown("## 👥 Customer Analysis Report")
    
    if 'party_name' not in sales_data.columns:
        st.error("Customer information not available in sales data")
        return
    
    # Customer metrics
    customer_summary = sales_data.groupby('party_name').agg({
        'amount': ['sum', 'count', 'mean'],
        'date': ['min', 'max']
    }).reset_index()
    
    customer_summary.columns = ['Customer', 'Total Sales', 'Transactions', 'Avg Transaction', 'First Sale', 'Last Sale']
    customer_summary = customer_summary.sort_values('Total Sales', ascending=False)
    
    # Customer distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Customer Distribution")
        top_10_customers = customer_summary.head(10)
        fig = px.pie(top_10_customers, values='Total Sales', names='Customer',
                     title='Top 10 Customers by Sales')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Customer Value Analysis")
        fig = px.scatter(customer_summary, x='Transactions', y='Total Sales',
                        hover_data=['Customer'], title='Customer Value vs Frequency')
        st.plotly_chart(fig, use_container_width=True)
    
    # RFM Analysis using advanced analytics
    st.markdown("### 🎯 Customer Segmentation (RFM Analysis)")
    analytics = AdvancedAnalytics()
    render_customer_segmentation(analytics, sales_data)
    
    # Detailed customer table
    st.markdown("### 📋 Detailed Customer Analysis")
    
    # Format currency columns
    display_summary = customer_summary.copy()
    display_summary['Total Sales'] = display_summary['Total Sales'].apply(format_currency)
    display_summary['Avg Transaction'] = display_summary['Avg Transaction'].apply(format_currency)
    
    st.dataframe(display_summary, use_container_width=True)
    
    # Export options
    render_export_section(customer_summary, "customer_analysis")

def render_product_analysis_report(sales_data: pd.DataFrame):
    """Render product analysis report"""
    st.markdown("## 📦 Product Analysis Report")
    
    # Check if product data is available
    if 'stock_item' not in sales_data.columns:
        st.warning("Product information not available in sales data")
        # Show alternative analysis based on available columns
        st.info("Showing analysis based on available data...")
        
        # Show sales by voucher type or other available groupings
        if 'voucher_type' in sales_data.columns:
            voucher_analysis = sales_data.groupby('voucher_type')['amount'].agg(['sum', 'count']).reset_index()
            voucher_analysis.columns = ['Voucher Type', 'Total Sales', 'Count']
            
            fig = px.bar(voucher_analysis, x='Voucher Type', y='Total Sales',
                        title='Sales by Voucher Type')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(voucher_analysis, use_container_width=True)
        
        return
    
    # Product sales analysis
    product_summary = sales_data.groupby('stock_item').agg({
        'amount': ['sum', 'count', 'mean'],
        'date': ['min', 'max']
    }).reset_index()
    
    product_summary.columns = ['Product', 'Total Sales', 'Transactions', 'Avg Sale', 'First Sale', 'Last Sale']
    product_summary = product_summary.sort_values('Total Sales', ascending=False)
    
    # Product performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_products = len(product_summary)
        st.metric("Total Products", f"{total_products:,}")
    
    with col2:
        top_product_sales = product_summary.iloc[0]['Total Sales'] if not product_summary.empty else 0
        st.metric("Top Product Sales", format_currency(top_product_sales))
    
    with col3:
        avg_product_sales = product_summary['Total Sales'].mean()
        st.metric("Avg Product Sales", format_currency(avg_product_sales))
    
    # Product performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 Top Performing Products")
        top_products = product_summary.head(10)
        fig = px.bar(top_products, x='Product', y='Total Sales',
                     title='Top 10 Products by Sales')
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Product Sales Distribution")
        fig = px.histogram(product_summary, x='Total Sales', nbins=20,
                          title='Distribution of Product Sales')
        st.plotly_chart(fig, use_container_width=True)
    
    # ABC Analysis
    st.markdown("### 📈 ABC Analysis")
    
    # Calculate cumulative sales percentage
    product_summary = product_summary.sort_values('Total Sales', ascending=False)
    product_summary['Cumulative Sales'] = product_summary['Total Sales'].cumsum()
    total_sales = product_summary['Total Sales'].sum()
    product_summary['Cumulative %'] = (product_summary['Cumulative Sales'] / total_sales) * 100
    
    # Classify products
    def classify_abc(cum_pct):
        if cum_pct <= 80:
            return 'A'
        elif cum_pct <= 95:
            return 'B'
        else:
            return 'C'
    
    product_summary['ABC Category'] = product_summary['Cumulative %'].apply(classify_abc)
    
    # ABC distribution
    abc_summary = product_summary.groupby('ABC Category').agg({
        'Product': 'count',
        'Total Sales': 'sum'
    }).reset_index()
    abc_summary.columns = ['Category', 'Product Count', 'Total Sales']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(abc_summary, x='Category', y='Product Count',
                     title='ABC Analysis - Product Count')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(abc_summary, x='Category', y='Total Sales',
                     title='ABC Analysis - Sales Value')
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed product table
    st.markdown("### 📋 Detailed Product Analysis")
    
    # Add filters for the table
    col1, col2 = st.columns(2)
    with col1:
        abc_filter = st.multiselect("Filter by ABC Category", ['A', 'B', 'C'], default=['A', 'B', 'C'])
    with col2:
        min_sales = st.number_input("Minimum Sales Amount", min_value=0.0, value=0.0)
    
    filtered_products = product_summary[
        (product_summary['ABC Category'].isin(abc_filter)) &
        (product_summary['Total Sales'] >= min_sales)
    ]
    
    # Format display
    display_products = filtered_products.copy()
    display_products['Total Sales'] = display_products['Total Sales'].apply(format_currency)
    display_products['Avg Sale'] = display_products['Avg Sale'].apply(format_currency)
    display_products['Cumulative %'] = display_products['Cumulative %'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(display_products, use_container_width=True)
    
    # Export options
    render_export_section(product_summary, "product_analysis")

def render_sales_trend_report(sales_data: pd.DataFrame, group_by: str):
    """Render sales trend analysis report"""
    st.markdown("## 📈 Sales Trend Analysis")
    
    sales_data['date'] = pd.to_datetime(sales_data['date'])
    
    # Time series analysis
    if group_by.lower() == "daily":
        time_series = sales_data.groupby(sales_data['date'].dt.date)['amount'].sum()
        freq = 'D'
        title = 'Daily Sales Trend'
    elif group_by.lower() == "weekly":
        time_series = sales_data.groupby(sales_data['date'].dt.to_period('W'))['amount'].sum()
        freq = 'W'
        title = 'Weekly Sales Trend'
    elif group_by.lower() == "monthly":
        time_series = sales_data.groupby(sales_data['date'].dt.to_period('M'))['amount'].sum()
        freq = 'M'
        title = 'Monthly Sales Trend'
    
    # Create trend chart with moving average
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=time_series.index,
        y=time_series.values,
        mode='lines+markers',
        name='Sales',
        line=dict(color='blue')
    ))
    
    # Add moving average if enough data points
    if len(time_series) >= 7:
        if group_by.lower() == "daily":
            ma_window = 7
            ma_label = '7-day Moving Average'
        elif group_by.lower() == "weekly":
            ma_window = 4
            ma_label = '4-week Moving Average'
        else:
            ma_window = 3
            ma_label = '3-month Moving Average'
        
        moving_avg = time_series.rolling(window=ma_window).mean()
        
        fig.add_trace(go.Scatter(
            x=moving_avg.index,
            y=moving_avg.values,
            mode='lines',
            name=ma_label,
            line=dict(color='red', dash='dash')
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Period',
        yaxis_title='Sales Amount (₹)',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_sales = time_series.mean()
        st.metric("Average Sales", format_currency(avg_sales))
    
    with col2:
        max_sales = time_series.max()
        st.metric("Peak Sales", format_currency(max_sales))
    
    with col3:
        min_sales = time_series.min()
        st.metric("Lowest Sales", format_currency(min_sales))
    
    with col4:
        sales_volatility = time_series.std()
        st.metric("Volatility", format_currency(sales_volatility))
    
    # Growth analysis
    if len(time_series) >= 2:
        st.markdown("### 📊 Growth Analysis")
        
        # Period-over-period growth
        growth_rates = time_series.pct_change() * 100
        growth_rates = growth_rates.dropna()
        
        if not growth_rates.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                avg_growth = growth_rates.mean()
                st.metric("Average Growth Rate", f"{avg_growth:.1f}%")
            
            with col2:
                latest_growth = growth_rates.iloc[-1]
                st.metric("Latest Growth Rate", f"{latest_growth:.1f}%")
            
            # Growth rate chart
            fig = px.bar(x=growth_rates.index, y=growth_rates.values,
                        title=f'{group_by} Growth Rates (%)')
            fig.update_layout(xaxis_title='Period', yaxis_title='Growth Rate (%)')
            st.plotly_chart(fig, use_container_width=True)

def render_regional_analysis_report(sales_data: pd.DataFrame):
    """Render regional sales analysis"""
    st.markdown("## 🗺️ Regional Sales Analysis")
    
    # Check for regional data
    regional_columns = ['region', 'state', 'city', 'location', 'branch']
    available_column = None
    
    for col in regional_columns:
        if col in sales_data.columns:
            available_column = col
            break
    
    if not available_column:
        st.warning("Regional information not available in sales data")
        st.info("To enable regional analysis, ensure your Tally data includes location/regional information")
        return
    
    # Regional sales summary
    regional_summary = sales_data.groupby(available_column).agg({
        'amount': ['sum', 'count', 'mean']
    }).reset_index()
    
    regional_summary.columns = ['Region', 'Total Sales', 'Transactions', 'Avg Sale']
    regional_summary = regional_summary.sort_values('Total Sales', ascending=False)
    
    # Regional performance chart
    fig = px.bar(regional_summary, x='Region', y='Total Sales',
                 title='Sales by Region')
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Regional comparison
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(regional_summary, values='Total Sales', names='Region',
                     title='Regional Sales Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(regional_summary, x='Transactions', y='Total Sales',
                        text='Region', title='Region Performance Matrix')
        st.plotly_chart(fig, use_container_width=True)
    
    # Regional table
    st.markdown("### 📋 Regional Performance Details")
    display_regional = regional_summary.copy()
    display_regional['Total Sales'] = display_regional['Total Sales'].apply(format_currency)
    display_regional['Avg Sale'] = display_regional['Avg Sale'].apply(format_currency)
    
    st.dataframe(display_regional, use_container_width=True)

def render_export_section(data: pd.DataFrame, report_name: str):
    """Render export options for reports"""
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

def show_quick_sales_overview():
    """Show quick sales overview when no specific report is selected"""
    st.markdown("## 🚀 Quick Sales Overview")
    st.markdown("Select a report type from the sidebar to get started with detailed analysis.")
    
    # Show sample metrics (would be replaced with actual data)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **📈 Sales Summary**
        - View total sales, transactions, and trends
        - Analyze performance by day, week, or month
        - Compare with previous periods
        """)
    
    with col2:
        st.info("""
        **👥 Customer Analysis** 
        - RFM segmentation and customer profiling
        - Top customers and loyalty analysis
        - Customer lifetime value insights
        """)
    
    with col3:
        st.info("""
        **📦 Product Analysis**
        - ABC analysis and product performance
        - Best and slow-moving items
        - Product profitability insights
        """)

if __name__ == "__main__":
    main()

