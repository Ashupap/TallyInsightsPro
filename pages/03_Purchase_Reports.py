import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from src.auth import require_auth, check_permission
from src.tally_api import TallyAPIClient
from src.utils import load_custom_css, format_currency, get_date_range_options, export_dataframe_to_excel

# Page configuration
st.set_page_config(
    page_title="Purchase Reports - Tally Prime Analytics",
    page_icon="📦",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main purchase reports page"""
    
    st.title("📦 Purchase Reports & Analysis")
    st.markdown("### Comprehensive procurement and vendor analysis")
    
    # Check permissions
    if not check_permission('view_reports'):
        st.error("You don't have permission to view purchase reports")
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
            ["Purchase Summary", "Vendor Analysis", "Purchase Trend", "Category Analysis", "Payment Analysis"]
        )
        
        # Additional filters
        st.markdown("---")
        st.markdown("#### Additional Filters")
        
        # Vendor filter
        vendor_filter = st.multiselect(
            "Vendors",
            options=[],  # Would be populated from Tally data
            help="Select specific vendors to filter"
        )
        
        # Amount range filter
        min_amount = st.number_input("Minimum Amount", min_value=0.0, value=0.0)
        max_amount = st.number_input("Maximum Amount", min_value=0.0, value=0.0)
        
        # Generate report button
        generate_report = st.button("📊 Generate Report", type="primary")
    
    # Main content area
    if generate_report or st.session_state.get('auto_load_purchase', False):
        
        # Get Tally client
        tally_server = st.session_state.get('tally_server')
        if not tally_server:
            st.error("Tally server not configured. Please check your settings.")
            return
        
        try:
            with st.spinner("Generating purchase report..."):
                # Fetch purchase data
                client = TallyAPIClient(tally_server)
                purchase_data = client.get_purchase_data(
                    from_date.strftime('%d-%b-%Y'),
                    to_date.strftime('%d-%b-%Y')
                )
                
                if purchase_data.empty:
                    st.warning("No purchase data found for the selected period.")
                    return
                
                # Apply filters
                if min_amount > 0:
                    purchase_data = purchase_data[purchase_data['amount'] >= min_amount]
                
                if max_amount > 0:
                    purchase_data = purchase_data[purchase_data['amount'] <= max_amount]
                
                if vendor_filter:
                    purchase_data = purchase_data[purchase_data['party_name'].isin(vendor_filter)]
                
                # Process data based on report type
                if report_type == "Purchase Summary":
                    render_purchase_summary_report(purchase_data, from_date, to_date)
                
                elif report_type == "Vendor Analysis":
                    render_vendor_analysis_report(purchase_data)
                
                elif report_type == "Purchase Trend":
                    render_purchase_trend_report(purchase_data)
                
                elif report_type == "Category Analysis":
                    render_category_analysis_report(purchase_data)
                
                elif report_type == "Payment Analysis":
                    render_payment_analysis_report(purchase_data)
                
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
    
    else:
        # Show welcome message and instructions
        st.info("👈 Use the sidebar to configure and generate your purchase report")
        show_purchase_overview()

def render_purchase_summary_report(purchase_data: pd.DataFrame, from_date, to_date):
    """Render purchase summary report"""
    st.markdown("## 📊 Purchase Summary Report")
    st.markdown(f"**Period:** {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}")
    
    # Summary metrics
    total_purchases = purchase_data['amount'].sum()
    total_orders = len(purchase_data)
    avg_order_value = purchase_data['amount'].mean()
    unique_vendors = purchase_data['party_name'].nunique() if 'party_name' in purchase_data.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Purchases", format_currency(total_purchases))
    with col2:
        st.metric("Purchase Orders", f"{total_orders:,}")
    with col3:
        st.metric("Avg Order Value", format_currency(avg_order_value))
    with col4:
        st.metric("Active Vendors", f"{unique_vendors:,}")
    
    # Purchase trend chart
    st.markdown("### 📈 Purchase Trend")
    
    purchase_data['date'] = pd.to_datetime(purchase_data['date'])
    daily_purchases = purchase_data.groupby(purchase_data['date'].dt.date)['amount'].sum().reset_index()
    
    fig = px.line(daily_purchases, x='date', y='amount',
                  title='Daily Purchase Trend',
                  labels={'amount': 'Purchase Amount (₹)', 'date': 'Date'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Top vendors
    st.markdown("### 🏪 Top Vendors")
    if 'party_name' in purchase_data.columns:
        vendor_summary = purchase_data.groupby('party_name').agg({
            'amount': ['sum', 'count', 'mean']
        }).reset_index()
        vendor_summary.columns = ['Vendor', 'Total Purchases', 'Orders', 'Avg Order Value']
        vendor_summary = vendor_summary.sort_values('Total Purchases', ascending=False).head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(vendor_summary, x='Vendor', y='Total Purchases',
                        title='Top 10 Vendors by Purchase Value')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(vendor_summary, values='Total Purchases', names='Vendor',
                        title='Vendor Purchase Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        # Vendor summary table
        display_summary = vendor_summary.copy()
        display_summary['Total Purchases'] = display_summary['Total Purchases'].apply(format_currency)
        display_summary['Avg Order Value'] = display_summary['Avg Order Value'].apply(format_currency)
        
        st.dataframe(display_summary, use_container_width=True)
    
    # Purchase distribution analysis
    st.markdown("### 📊 Purchase Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Purchase amount distribution
        fig = px.histogram(purchase_data, x='amount', nbins=20,
                          title='Purchase Amount Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Monthly comparison
        purchase_data['month'] = purchase_data['date'].dt.to_period('M')
        monthly_purchases = purchase_data.groupby('month')['amount'].sum().reset_index()
        
        if len(monthly_purchases) > 1:
            fig = px.bar(monthly_purchases, x='month', y='amount',
                        title='Monthly Purchase Comparison')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need more than one month of data for comparison")
    
    # Export options
    render_export_section(purchase_data, "purchase_summary")

def render_vendor_analysis_report(purchase_data: pd.DataFrame):
    """Render vendor analysis report"""
    st.markdown("## 🏪 Vendor Analysis Report")
    
    if 'party_name' not in purchase_data.columns:
        st.error("Vendor information not available in purchase data")
        return
    
    # Vendor performance metrics
    vendor_analysis = purchase_data.groupby('party_name').agg({
        'amount': ['sum', 'count', 'mean', 'std'],
        'date': ['min', 'max'],
        'voucher_number': 'count'
    }).reset_index()
    
    vendor_analysis.columns = ['Vendor', 'Total Purchases', 'Order Count', 'Avg Order', 'Order Std', 'First Order', 'Last Order', 'Voucher Count']
    vendor_analysis = vendor_analysis.sort_values('Total Purchases', ascending=False)
    
    # Calculate vendor metrics
    vendor_analysis['Order Consistency'] = 1 / (1 + vendor_analysis['Order Std'] / vendor_analysis['Avg Order'])
    vendor_analysis['Order Frequency'] = vendor_analysis['Order Count'] / ((vendor_analysis['Last Order'] - vendor_analysis['First Order']).dt.days + 1)
    
    # Vendor classification
    total_purchases = vendor_analysis['Total Purchases'].sum()
    vendor_analysis['Purchase Share %'] = (vendor_analysis['Total Purchases'] / total_purchases) * 100
    
    def classify_vendor(share):
        if share >= 20:
            return 'Strategic'
        elif share >= 10:
            return 'Important'
        elif share >= 5:
            return 'Regular'
        else:
            return 'Occasional'
    
    vendor_analysis['Vendor Category'] = vendor_analysis['Purchase Share %'].apply(classify_vendor)
    
    # Vendor category distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Vendor Category Distribution")
        category_summary = vendor_analysis.groupby('Vendor Category').agg({
            'Vendor': 'count',
            'Total Purchases': 'sum'
        }).reset_index()
        category_summary.columns = ['Category', 'Vendor Count', 'Total Purchases']
        
        fig = px.bar(category_summary, x='Category', y='Vendor Count',
                     title='Vendors by Category')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 Purchase Value by Category")
        fig = px.pie(category_summary, values='Total Purchases', names='Category',
                     title='Purchase Distribution by Vendor Category')
        st.plotly_chart(fig, use_container_width=True)
    
    # Vendor performance matrix
    st.markdown("### 📈 Vendor Performance Matrix")
    
    fig = px.scatter(vendor_analysis, x='Order Frequency', y='Avg Order',
                    size='Total Purchases', color='Vendor Category',
                    hover_data=['Vendor'], 
                    title='Vendor Performance: Frequency vs Order Value')
    st.plotly_chart(fig, use_container_width=True)
    
    # Top performing vendors
    st.markdown("### 🏆 Top Performing Vendors")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### By Purchase Value")
        top_by_value = vendor_analysis.nlargest(5, 'Total Purchases')[['Vendor', 'Total Purchases']]
        top_by_value['Total Purchases'] = top_by_value['Total Purchases'].apply(format_currency)
        st.dataframe(top_by_value, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### By Order Frequency")
        top_by_frequency = vendor_analysis.nlargest(5, 'Order Count')[['Vendor', 'Order Count']]
        st.dataframe(top_by_frequency, use_container_width=True, hide_index=True)
    
    with col3:
        st.markdown("#### By Consistency")
        top_by_consistency = vendor_analysis.nlargest(5, 'Order Consistency')[['Vendor', 'Order Consistency']]
        top_by_consistency['Order Consistency'] = top_by_consistency['Order Consistency'].apply(lambda x: f"{x:.2f}")
        st.dataframe(top_by_consistency, use_container_width=True, hide_index=True)
    
    # Detailed vendor table
    st.markdown("### 📋 Detailed Vendor Analysis")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.multiselect("Filter by Category", 
                                       vendor_analysis['Vendor Category'].unique(),
                                       default=vendor_analysis['Vendor Category'].unique())
    with col2:
        min_purchases = st.number_input("Minimum Purchase Value", min_value=0.0, value=0.0)
    
    filtered_vendors = vendor_analysis[
        (vendor_analysis['Vendor Category'].isin(category_filter)) &
        (vendor_analysis['Total Purchases'] >= min_purchases)
    ]
    
    # Format display columns
    display_vendors = filtered_vendors.copy()
    display_vendors['Total Purchases'] = display_vendors['Total Purchases'].apply(format_currency)
    display_vendors['Avg Order'] = display_vendors['Avg Order'].apply(format_currency)
    display_vendors['Purchase Share %'] = display_vendors['Purchase Share %'].apply(lambda x: f"{x:.1f}%")
    display_vendors['Order Consistency'] = display_vendors['Order Consistency'].apply(lambda x: f"{x:.2f}")
    
    selected_columns = ['Vendor', 'Total Purchases', 'Order Count', 'Avg Order', 
                       'Purchase Share %', 'Vendor Category', 'Order Consistency']
    
    st.dataframe(display_vendors[selected_columns], use_container_width=True)
    
    # Export options
    render_export_section(vendor_analysis, "vendor_analysis")

def render_purchase_trend_report(purchase_data: pd.DataFrame):
    """Render purchase trend analysis report"""
    st.markdown("## 📈 Purchase Trend Analysis")
    
    purchase_data['date'] = pd.to_datetime(purchase_data['date'])
    
    # Time series analysis options
    col1, col2 = st.columns(2)
    with col1:
        trend_period = st.selectbox("Trend Period", ["Daily", "Weekly", "Monthly"])
    with col2:
        show_moving_avg = st.checkbox("Show Moving Average", value=True)
    
    # Generate time series based on selection
    if trend_period == "Daily":
        time_series = purchase_data.groupby(purchase_data['date'].dt.date)['amount'].sum()
        ma_window = 7
        ma_label = '7-day Moving Average'
    elif trend_period == "Weekly":
        time_series = purchase_data.groupby(purchase_data['date'].dt.to_period('W'))['amount'].sum()
        ma_window = 4
        ma_label = '4-week Moving Average'
    else:  # Monthly
        time_series = purchase_data.groupby(purchase_data['date'].dt.to_period('M'))['amount'].sum()
        ma_window = 3
        ma_label = '3-month Moving Average'
    
    # Create trend chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=time_series.index,
        y=time_series.values,
        mode='lines+markers',
        name='Purchases',
        line=dict(color='blue')
    ))
    
    if show_moving_avg and len(time_series) >= ma_window:
        moving_avg = time_series.rolling(window=ma_window).mean()
        fig.add_trace(go.Scatter(
            x=moving_avg.index,
            y=moving_avg.values,
            mode='lines',
            name=ma_label,
            line=dict(color='red', dash='dash')
        ))
    
    fig.update_layout(
        title=f'{trend_period} Purchase Trend',
        xaxis_title='Period',
        yaxis_title='Purchase Amount (₹)',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_purchases = time_series.mean()
        st.metric("Average Purchases", format_currency(avg_purchases))
    
    with col2:
        max_purchases = time_series.max()
        st.metric("Peak Purchases", format_currency(max_purchases))
    
    with col3:
        min_purchases = time_series.min()
        st.metric("Lowest Purchases", format_currency(min_purchases))
    
    with col4:
        purchase_volatility = time_series.std()
        st.metric("Volatility", format_currency(purchase_volatility))
    
    # Seasonal analysis
    st.markdown("### 🗓️ Seasonal Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly pattern
        purchase_data['month'] = purchase_data['date'].dt.month
        monthly_pattern = purchase_data.groupby('month')['amount'].mean().reset_index()
        monthly_pattern['month_name'] = monthly_pattern['month'].apply(
            lambda x: datetime(2023, x, 1).strftime('%B')
        )
        
        fig = px.bar(monthly_pattern, x='month_name', y='amount',
                     title='Average Monthly Purchase Pattern')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Day of week pattern
        purchase_data['day_of_week'] = purchase_data['date'].dt.dayofweek
        daily_pattern = purchase_data.groupby('day_of_week')['amount'].mean().reset_index()
        daily_pattern['day_name'] = daily_pattern['day_of_week'].apply(
            lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
        )
        
        fig = px.bar(daily_pattern, x='day_name', y='amount',
                     title='Average Daily Purchase Pattern')
        st.plotly_chart(fig, use_container_width=True)
    
    # Growth analysis
    if len(time_series) >= 2:
        st.markdown("### 📊 Growth Analysis")
        
        growth_rates = time_series.pct_change() * 100
        growth_rates = growth_rates.dropna()
        
        if not growth_rates.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_growth = growth_rates.mean()
                st.metric("Average Growth Rate", f"{avg_growth:.1f}%")
            
            with col2:
                latest_growth = growth_rates.iloc[-1]
                st.metric("Latest Growth Rate", f"{latest_growth:.1f}%")
            
            with col3:
                positive_growth_periods = (growth_rates > 0).sum()
                total_periods = len(growth_rates)
                growth_consistency = (positive_growth_periods / total_periods) * 100
                st.metric("Growth Consistency", f"{growth_consistency:.1f}%")
            
            # Growth rate visualization
            fig = px.line(x=growth_rates.index, y=growth_rates.values,
                         title=f'{trend_period} Growth Rates (%)')
            fig.add_hline(y=0, line_dash="dash", line_color="red")
            fig.update_layout(xaxis_title='Period', yaxis_title='Growth Rate (%)')
            st.plotly_chart(fig, use_container_width=True)

def render_category_analysis_report(purchase_data: pd.DataFrame):
    """Render category analysis report"""
    st.markdown("## 📂 Category Analysis Report")
    
    # Check for category information
    category_columns = ['category', 'product_category', 'item_group', 'stock_group']
    available_column = None
    
    for col in category_columns:
        if col in purchase_data.columns:
            available_column = col
            break
    
    if not available_column:
        st.warning("Category information not available in purchase data")
        st.info("To enable category analysis, ensure your Tally data includes product category/group information")
        
        # Show alternative analysis
        show_alternative_categorization(purchase_data)
        return
    
    # Category analysis
    category_summary = purchase_data.groupby(available_column).agg({
        'amount': ['sum', 'count', 'mean'],
        'party_name': 'nunique'
    }).reset_index()
    
    category_summary.columns = ['Category', 'Total Purchases', 'Order Count', 'Avg Order', 'Vendor Count']
    category_summary = category_summary.sort_values('Total Purchases', ascending=False)
    
    # Category performance overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_categories = len(category_summary)
        st.metric("Total Categories", f"{total_categories:,}")
    
    with col2:
        top_category_value = category_summary.iloc[0]['Total Purchases'] if not category_summary.empty else 0
        st.metric("Top Category Value", format_currency(top_category_value))
    
    with col3:
        avg_category_value = category_summary['Total Purchases'].mean()
        st.metric("Avg Category Value", format_currency(avg_category_value))
    
    # Category visualization
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Category Purchase Distribution")
        top_categories = category_summary.head(10)
        fig = px.pie(top_categories, values='Total Purchases', names='Category',
                     title='Top 10 Categories by Purchase Value')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Category Performance")
        fig = px.bar(top_categories, x='Category', y='Total Purchases',
                     title='Top 10 Categories by Purchase Value')
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Category details table
    st.markdown("### 📋 Category Details")
    
    display_categories = category_summary.copy()
    display_categories['Total Purchases'] = display_categories['Total Purchases'].apply(format_currency)
    display_categories['Avg Order'] = display_categories['Avg Order'].apply(format_currency)
    
    st.dataframe(display_categories, use_container_width=True)
    
    # Export options
    render_export_section(category_summary, "category_analysis")

def render_payment_analysis_report(purchase_data: pd.DataFrame):
    """Render payment analysis report"""
    st.markdown("## 💳 Payment Analysis Report")
    
    # Basic payment analysis based on available data
    st.info("Detailed payment analysis requires additional payment terms data from Tally")
    
    # Purchase amount distribution for payment analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Purchase Amount Distribution")
        
        # Categorize purchases by amount
        def categorize_amount(amount):
            if amount < 10000:
                return 'Small (< ₹10K)'
            elif amount < 50000:
                return 'Medium (₹10K - ₹50K)'
            elif amount < 100000:
                return 'Large (₹50K - ₹1L)'
            else:
                return 'Very Large (> ₹1L)'
        
        purchase_data['Amount Category'] = purchase_data['amount'].apply(categorize_amount)
        amount_distribution = purchase_data['Amount Category'].value_counts().reset_index()
        amount_distribution.columns = ['Category', 'Count']
        
        fig = px.pie(amount_distribution, values='Count', names='Category',
                     title='Purchase Distribution by Amount')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📅 Payment Timeline Analysis")
        
        # Monthly payment analysis
        purchase_data['date'] = pd.to_datetime(purchase_data['date'])
        purchase_data['month_year'] = purchase_data['date'].dt.to_period('M')
        monthly_payments = purchase_data.groupby('month_year')['amount'].sum().reset_index()
        
        fig = px.bar(monthly_payments, x='month_year', y='amount',
                     title='Monthly Purchase Payments')
        st.plotly_chart(fig, use_container_width=True)
    
    # Vendor payment analysis
    if 'party_name' in purchase_data.columns:
        st.markdown("### 🏪 Vendor Payment Analysis")
        
        vendor_payments = purchase_data.groupby('party_name').agg({
            'amount': ['sum', 'count', 'mean', 'max']
        }).reset_index()
        vendor_payments.columns = ['Vendor', 'Total Paid', 'Transactions', 'Avg Payment', 'Max Payment']
        vendor_payments = vendor_payments.sort_values('Total Paid', ascending=False).head(10)
        
        # Format display
        display_payments = vendor_payments.copy()
        display_payments['Total Paid'] = display_payments['Total Paid'].apply(format_currency)
        display_payments['Avg Payment'] = display_payments['Avg Payment'].apply(format_currency)
        display_payments['Max Payment'] = display_payments['Max Payment'].apply(format_currency)
        
        st.dataframe(display_payments, use_container_width=True)

def show_alternative_categorization(purchase_data: pd.DataFrame):
    """Show alternative categorization when category data is not available"""
    st.markdown("### 📊 Alternative Analysis")
    
    # Categorize by amount ranges
    def categorize_by_amount(amount):
        if amount < 10000:
            return 'Small Purchases'
        elif amount < 50000:
            return 'Medium Purchases'
        elif amount < 100000:
            return 'Large Purchases'
        else:
            return 'Very Large Purchases'
    
    purchase_data['Purchase Category'] = purchase_data['amount'].apply(categorize_by_amount)
    
    amount_category_analysis = purchase_data.groupby('Purchase Category').agg({
        'amount': ['sum', 'count', 'mean']
    }).reset_index()
    amount_category_analysis.columns = ['Category', 'Total Amount', 'Count', 'Average']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(amount_category_analysis, values='Total Amount', names='Category',
                     title='Purchase Distribution by Amount Range')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(amount_category_analysis, x='Category', y='Count',
                     title='Purchase Count by Amount Range')
        st.plotly_chart(fig, use_container_width=True)

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

def show_purchase_overview():
    """Show purchase overview when no specific report is selected"""
    st.markdown("## 🚀 Purchase Reports Overview")
    st.markdown("Select a report type from the sidebar to get started with detailed procurement analysis.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📦 Purchase Summary**
        - Total purchase value and order analysis
        - Daily, weekly, and monthly trends
        - Purchase distribution insights
        """)
        
        st.info("""
        **📈 Purchase Trend** 
        - Time series analysis with moving averages
        - Seasonal patterns and growth rates
        - Purchase volatility analysis
        """)
    
    with col2:
        st.info("""
        **🏪 Vendor Analysis**
        - Vendor performance and categorization
        - Strategic supplier identification
        - Order frequency and consistency metrics
        """)
        
        st.info("""
        **💳 Payment Analysis**
        - Payment timeline and amount distribution
        - Vendor payment patterns
        - Cash flow impact analysis
        """)

if __name__ == "__main__":
    main()

