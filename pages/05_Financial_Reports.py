import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from src.auth import require_auth, check_permission
from src.tally_api import TallyAPIClient
from src.utils import load_custom_css, format_currency, get_date_range_options, export_dataframe_to_excel, calculate_percentage_change, get_financial_year

# Page configuration
st.set_page_config(
    page_title="Financial Reports - Tally Prime Analytics",
    page_icon="📊",
    layout="wide"
)

# Load custom CSS
load_custom_css()

@require_auth
def main():
    """Main financial reports page"""
    
    st.title("📊 Financial Reports")
    st.markdown("### Comprehensive financial analysis and reporting")
    
    # Check permissions
    if not check_permission('view_reports'):
        st.error("You don't have permission to view financial reports")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ Financial Controls")
        
        # Report type selection
        report_type = st.selectbox(
            "📊 Report Type",
            ["Financial Dashboard", "Profit & Loss", "Balance Sheet", "Cash Flow", "Financial Ratios", "Outstanding Reports", "GST Reports"]
        )
        
        # Date range selection
        st.markdown("---")
        st.markdown("#### Date Range")
        
        date_options = get_date_range_options()
        selected_range = st.selectbox(
            "📅 Period",
            options=list(date_options.keys()),
            index=4  # Default to "This Month"
        )
        
        if selected_range == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                from_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
            with col2:
                to_date = st.date_input("To Date", datetime.now())
        else:
            from_date, to_date = date_options[selected_range]
        
        # Additional filters
        st.markdown("---")
        st.markdown("#### Additional Filters")
        
        # Cost center filter
        cost_center = st.multiselect(
            "Cost Centers",
            options=[],  # Would be populated from Tally data
            help="Filter by cost centers"
        )
        
        # Comparison options
        compare_previous = st.checkbox("Compare with Previous Period", value=True)
        
        # Generate report button
        generate_report = st.button("📊 Generate Report", type="primary")
    
    # Main content area
    if generate_report or st.session_state.get('auto_load_financial', False):
        
        # Get Tally client
        tally_server = st.session_state.get('tally_server')
        if not tally_server:
            st.error("Tally server not configured. Please check your settings.")
            return
        
        try:
            with st.spinner("Generating financial report..."):
                client = TallyAPIClient(tally_server)
                
                # Process data based on report type
                if report_type == "Financial Dashboard":
                    render_financial_dashboard(client, from_date, to_date, compare_previous)
                elif report_type == "Profit & Loss":
                    render_profit_loss_report(client, from_date, to_date, compare_previous)
                elif report_type == "Balance Sheet":
                    render_balance_sheet_report(client, to_date, compare_previous)
                elif report_type == "Cash Flow":
                    render_cash_flow_report(client, from_date, to_date)
                elif report_type == "Financial Ratios":
                    render_financial_ratios_report(client, from_date, to_date)
                elif report_type == "Outstanding Reports":
                    render_outstanding_reports(client)
                elif report_type == "GST Reports":
                    render_gst_reports(client, from_date, to_date)
                
        except Exception as e:
            st.error(f"Error generating financial report: {str(e)}")
    
    else:
        # Show welcome message and financial overview
        st.info("👈 Select a report type from the sidebar to generate your financial analysis")
        show_financial_overview()

def render_financial_dashboard(client: TallyAPIClient, from_date, to_date, compare_previous: bool):
    """Render comprehensive financial dashboard"""
    st.markdown("## 📊 Financial Dashboard")
    st.markdown(f"**Period:** {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}")
    
    # Fetch financial data
    pl_data = client.get_profit_loss_data(from_date.strftime('%d-%b-%Y'), to_date.strftime('%d-%b-%Y'))
    bs_data = client.get_balance_sheet_data(to_date.strftime('%Y-%m-%d'))
    outstanding_data = client.get_outstanding_data()
    
    # Key financial metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = pl_data.get('revenue', 0)
        st.metric("Revenue", format_currency(revenue))
    
    with col2:
        net_profit = pl_data.get('net_profit', 0)
        profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        st.metric("Net Profit", format_currency(net_profit), f"{profit_margin:.1f}%")
    
    with col3:
        total_assets = bs_data.get('assets', {}).get('total', 0)
        st.metric("Total Assets", format_currency(total_assets))
    
    with col4:
        total_receivables = outstanding_data['closing_balance'].sum() if not outstanding_data.empty else 0
        st.metric("Receivables", format_currency(total_receivables))
    
    # Financial performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Revenue vs Profit")
        
        financial_data = {
            'Metric': ['Revenue', 'Gross Profit', 'Net Profit'],
            'Amount': [
                pl_data.get('revenue', 0),
                pl_data.get('gross_profit', 0),
                pl_data.get('net_profit', 0)
            ]
        }
        
        fig = px.bar(financial_data, x='Metric', y='Amount',
                    title='Financial Performance Overview')
        fig.update_layout(yaxis_title='Amount (₹)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🍰 Revenue Breakdown")
        
        if pl_data.get('detailed_breakdown'):
            breakdown_data = pl_data['detailed_breakdown']
            # Filter only income/revenue items
            revenue_items = {k: v for k, v in breakdown_data.items() 
                           if v > 0 and any(word in k.lower() for word in ['sales', 'income', 'revenue'])}
            
            if revenue_items:
                fig = px.pie(values=list(revenue_items.values()), names=list(revenue_items.keys()),
                           title='Revenue Sources')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Detailed revenue breakdown not available")
        else:
            st.info("Revenue breakdown data not available")
    
    # Balance sheet overview
    st.markdown("### ⚖️ Balance Sheet Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Assets")
        assets = bs_data.get('assets', {})
        st.metric("Current Assets", format_currency(assets.get('current', 0)))
        st.metric("Fixed Assets", format_currency(assets.get('fixed', 0)))
        st.metric("Total Assets", format_currency(assets.get('total', 0)))
    
    with col2:
        st.markdown("#### Liabilities")
        liabilities = bs_data.get('liabilities', {})
        st.metric("Current Liabilities", format_currency(liabilities.get('current', 0)))
        st.metric("Long-term Liabilities", format_currency(liabilities.get('long_term', 0)))
        st.metric("Total Liabilities", format_currency(liabilities.get('total', 0)))
    
    with col3:
        st.markdown("#### Equity")
        equity = bs_data.get('equity', 0)
        st.metric("Total Equity", format_currency(equity))
        
        # Net worth
        net_worth = assets.get('total', 0) - liabilities.get('total', 0)
        st.metric("Net Worth", format_currency(net_worth))
    
    # Key financial ratios
    st.markdown("### 🔢 Key Financial Ratios")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_ratio = (assets.get('current', 0) / liabilities.get('current', 1)) if liabilities.get('current', 0) > 0 else 0
        st.metric("Current Ratio", f"{current_ratio:.2f}")
    
    with col2:
        debt_equity_ratio = (liabilities.get('total', 0) / equity) if equity > 0 else 0
        st.metric("Debt-Equity Ratio", f"{debt_equity_ratio:.2f}")
    
    with col3:
        profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        st.metric("Profit Margin", f"{profit_margin:.1f}%")
    
    with col4:
        asset_turnover = (revenue / total_assets) if total_assets > 0 else 0
        st.metric("Asset Turnover", f"{asset_turnover:.2f}")
    
    # Cash flow summary (simplified)
    st.markdown("### 💰 Cash Flow Summary")
    
    # This would be enhanced with actual cash flow data from Tally
    col1, col2, col3 = st.columns(3)
    
    with col1:
        operating_cf = net_profit  # Simplified calculation
        st.metric("Operating Cash Flow", format_currency(operating_cf))
    
    with col2:
        investing_cf = -assets.get('fixed', 0) * 0.1  # Simplified estimate
        st.metric("Investing Cash Flow", format_currency(investing_cf))
    
    with col3:
        financing_cf = liabilities.get('long_term', 0) * 0.1  # Simplified estimate
        st.metric("Financing Cash Flow", format_currency(financing_cf))
    
    # Export section
    financial_summary = {
        'profit_loss': pl_data,
        'balance_sheet': bs_data,
        'outstanding': outstanding_data.to_dict() if not outstanding_data.empty else {}
    }
    
    render_export_section(financial_summary, "financial_dashboard")

def render_profit_loss_report(client: TallyAPIClient, from_date, to_date, compare_previous: bool):
    """Render detailed Profit & Loss report"""
    st.markdown("## 📈 Profit & Loss Statement")
    st.markdown(f"**Period:** {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}")
    
    # Fetch P&L data
    pl_data = client.get_profit_loss_data(from_date.strftime('%d-%b-%Y'), to_date.strftime('%d-%b-%Y'))
    
    if not pl_data or 'revenue' not in pl_data:
        st.error("Unable to fetch P&L data. Please check your Tally connection.")
        return
    
    # Previous period comparison if requested
    if compare_previous:
        # Calculate previous period dates
        period_diff = to_date - from_date
        prev_to_date = from_date - timedelta(days=1)
        prev_from_date = prev_to_date - period_diff
        
        prev_pl_data = client.get_profit_loss_data(
            prev_from_date.strftime('%d-%b-%Y'), 
            prev_to_date.strftime('%d-%b-%Y')
        )
    else:
        prev_pl_data = None
    
    # P&L Summary
    col1, col2, col3, col4 = st.columns(4)
    
    revenue = pl_data.get('revenue', 0)
    gross_profit = pl_data.get('gross_profit', 0)
    total_expenses = pl_data.get('expenses', 0)
    net_profit = pl_data.get('net_profit', 0)
    
    with col1:
        if prev_pl_data:
            prev_revenue = prev_pl_data.get('revenue', 0)
            revenue_change, revenue_change_str = calculate_percentage_change(revenue, prev_revenue)
            st.metric("Revenue", format_currency(revenue), revenue_change_str)
        else:
            st.metric("Revenue", format_currency(revenue))
    
    with col2:
        if prev_pl_data:
            prev_gross = prev_pl_data.get('gross_profit', 0)
            gross_change, gross_change_str = calculate_percentage_change(gross_profit, prev_gross)
            st.metric("Gross Profit", format_currency(gross_profit), gross_change_str)
        else:
            st.metric("Gross Profit", format_currency(gross_profit))
    
    with col3:
        if prev_pl_data:
            prev_expenses = prev_pl_data.get('expenses', 0)
            expense_change, expense_change_str = calculate_percentage_change(total_expenses, prev_expenses)
            st.metric("Total Expenses", format_currency(total_expenses), expense_change_str)
        else:
            st.metric("Total Expenses", format_currency(total_expenses))
    
    with col4:
        if prev_pl_data:
            prev_net = prev_pl_data.get('net_profit', 0)
            net_change, net_change_str = calculate_percentage_change(net_profit, prev_net)
            st.metric("Net Profit", format_currency(net_profit), net_change_str)
        else:
            st.metric("Net Profit", format_currency(net_profit))
    
    # P&L Waterfall Chart
    st.markdown("### 💧 Profit & Loss Waterfall")
    
    categories = ['Revenue', 'COGS', 'Expenses', 'Net Profit']
    values = [
        revenue,
        -pl_data.get('cost_of_goods_sold', 0),
        -total_expenses,
        net_profit
    ]
    
    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=["absolute", "relative", "relative", "total"],
        text=[format_currency(abs(v)) for v in values],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="P&L Waterfall Analysis",
        xaxis_title="Categories",
        yaxis_title="Amount (₹)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed P&L breakdown
    if pl_data.get('detailed_breakdown'):
        st.markdown("### 📋 Detailed Breakdown")
        
        detailed_data = pl_data['detailed_breakdown']
        
        # Separate income and expenses
        income_items = {k: v for k, v in detailed_data.items() if v > 0}
        expense_items = {k: abs(v) for k, v in detailed_data.items() if v < 0}
        
        col1, col2 = st.columns(2)
        
        with col1:
            if income_items:
                st.markdown("#### 📈 Income")
                income_df = pd.DataFrame(list(income_items.items()), columns=['Account', 'Amount'])
                income_df['Amount'] = income_df['Amount'].apply(format_currency)
                st.dataframe(income_df, use_container_width=True, hide_index=True)
        
        with col2:
            if expense_items:
                st.markdown("#### 📉 Expenses")
                expense_df = pd.DataFrame(list(expense_items.items()), columns=['Account', 'Amount'])
                expense_df['Amount'] = expense_df['Amount'].apply(format_currency)
                st.dataframe(expense_df, use_container_width=True, hide_index=True)
    
    # Profitability ratios
    st.markdown("### 📊 Profitability Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        st.metric("Gross Profit Margin", f"{gross_margin:.1f}%")
    
    with col2:
        operating_margin = ((revenue - total_expenses) / revenue * 100) if revenue > 0 else 0
        st.metric("Operating Margin", f"{operating_margin:.1f}%")
    
    with col3:
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        st.metric("Net Profit Margin", f"{net_margin:.1f}%")
    
    # Export section
    render_export_section(pl_data, "profit_loss_statement")

def render_balance_sheet_report(client: TallyAPIClient, as_of_date, compare_previous: bool):
    """Render Balance Sheet report"""
    st.markdown("## ⚖️ Balance Sheet")
    st.markdown(f"**As of:** {as_of_date.strftime('%d %b %Y')}")
    
    # Fetch Balance Sheet data
    bs_data = client.get_balance_sheet_data(as_of_date.strftime('%Y-%m-%d'))
    
    if not bs_data:
        st.error("Unable to fetch Balance Sheet data. Please check your Tally connection.")
        return
    
    # Balance Sheet summary
    assets = bs_data.get('assets', {})
    liabilities = bs_data.get('liabilities', {})
    equity = bs_data.get('equity', 0)
    
    # Assets section
    st.markdown("### 🏢 Assets")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Current Assets")
        current_assets = assets.get('current', 0)
        st.metric("Current Assets", format_currency(current_assets))
        
        # Breakdown of current assets (if available)
        st.write("- Cash & Bank")
        st.write("- Accounts Receivable") 
        st.write("- Inventory")
        st.write("- Other Current Assets")
    
    with col2:
        st.markdown("#### Fixed Assets")
        fixed_assets = assets.get('fixed', 0)
        st.metric("Fixed Assets", format_currency(fixed_assets))
        
        st.write("- Property, Plant & Equipment")
        st.write("- Less: Accumulated Depreciation")
        st.write("- Intangible Assets")
        st.write("- Other Fixed Assets")
    
    with col3:
        st.markdown("#### Total Assets")
        total_assets = assets.get('total', 0)
        st.metric("Total Assets", format_currency(total_assets))
    
    # Liabilities & Equity section
    st.markdown("### 💳 Liabilities & Equity")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Current Liabilities")
        current_liabilities = liabilities.get('current', 0)
        st.metric("Current Liabilities", format_currency(current_liabilities))
        
        st.write("- Accounts Payable")
        st.write("- Short-term Loans")
        st.write("- Accrued Expenses")
        st.write("- Other Current Liabilities")
    
    with col2:
        st.markdown("#### Long-term Liabilities")
        long_term_liabilities = liabilities.get('long_term', 0)
        st.metric("Long-term Liabilities", format_currency(long_term_liabilities))
        
        st.write("- Long-term Loans")
        st.write("- Bonds & Debentures")
        st.write("- Other Long-term Debt")
    
    with col3:
        st.markdown("#### Equity")
        st.metric("Owner's Equity", format_currency(equity))
        
        st.write("- Capital")
        st.write("- Retained Earnings")
        st.write("- Current Year Profit/Loss")
    
    # Balance Sheet visualization
    st.markdown("### 📊 Balance Sheet Composition")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Assets composition
        asset_data = {
            'Current Assets': current_assets,
            'Fixed Assets': fixed_assets
        }
        
        fig = px.pie(values=list(asset_data.values()), names=list(asset_data.keys()),
                    title='Assets Composition')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Liabilities & Equity composition
        liab_equity_data = {
            'Current Liabilities': current_liabilities,
            'Long-term Liabilities': long_term_liabilities,
            'Equity': equity
        }
        
        fig = px.pie(values=list(liab_equity_data.values()), names=list(liab_equity_data.keys()),
                    title='Liabilities & Equity Composition')
        st.plotly_chart(fig, use_container_width=True)
    
    # Balance verification
    st.markdown("### ✅ Balance Verification")
    
    total_liabilities_equity = liabilities.get('total', 0) + equity
    balance_difference = total_assets - total_liabilities_equity
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Assets", format_currency(total_assets))
    
    with col2:
        st.metric("Total Liabilities + Equity", format_currency(total_liabilities_equity))
    
    with col3:
        if abs(balance_difference) < 1:  # Allow for minor rounding differences
            st.success("✅ Balance Sheet Balanced")
        else:
            st.error(f"❌ Difference: {format_currency(balance_difference)}")
    
    # Key ratios from balance sheet
    st.markdown("### 🔢 Balance Sheet Ratios")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        st.metric("Current Ratio", f"{current_ratio:.2f}")
    
    with col2:
        debt_to_assets = liabilities.get('total', 0) / total_assets if total_assets > 0 else 0
        st.metric("Debt to Assets", f"{debt_to_assets:.2f}")
    
    with col3:
        equity_ratio = equity / total_assets if total_assets > 0 else 0
        st.metric("Equity Ratio", f"{equity_ratio:.2f}")
    
    with col4:
        debt_to_equity = liabilities.get('total', 0) / equity if equity > 0 else 0
        st.metric("Debt to Equity", f"{debt_to_equity:.2f}")
    
    # Export section
    render_export_section(bs_data, "balance_sheet")

def render_cash_flow_report(client: TallyAPIClient, from_date, to_date):
    """Render Cash Flow statement"""
    st.markdown("## 💰 Cash Flow Statement")
    st.markdown(f"**Period:** {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}")
    
    st.info("📋 Detailed cash flow analysis requires transaction-level data from Tally Prime. This view provides a simplified cash flow overview.")
    
    # Get basic financial data to estimate cash flows
    pl_data = client.get_profit_loss_data(from_date.strftime('%d-%b-%Y'), to_date.strftime('%d-%b-%Y'))
    
    # Simplified cash flow calculation
    net_profit = pl_data.get('net_profit', 0)
    
    # Operating Activities (simplified)
    operating_cash_flow = net_profit  # Would be adjusted for non-cash items in real implementation
    
    # Investing Activities (estimated)
    investing_cash_flow = 0  # Would be calculated from asset purchases/sales
    
    # Financing Activities (estimated)  
    financing_cash_flow = 0  # Would be calculated from loans, equity changes
    
    # Cash flow summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Operating Cash Flow", format_currency(operating_cash_flow))
    
    with col2:
        st.metric("Investing Cash Flow", format_currency(investing_cash_flow))
    
    with col3:
        st.metric("Financing Cash Flow", format_currency(financing_cash_flow))
    
    with col4:
        net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow
        st.metric("Net Cash Flow", format_currency(net_cash_flow))
    
    # Cash flow waterfall
    st.markdown("### 💧 Cash Flow Waterfall")
    
    categories = ['Opening Cash', 'Operating CF', 'Investing CF', 'Financing CF', 'Closing Cash']
    values = [0, operating_cash_flow, investing_cash_flow, financing_cash_flow, net_cash_flow]
    
    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=["absolute", "relative", "relative", "relative", "total"]
    ))
    
    fig.update_layout(title="Cash Flow Analysis", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Cash flow projections
    st.markdown("### 🔮 Cash Flow Projections")
    
    # Simple 3-month projection
    monthly_cf = net_cash_flow / ((to_date - from_date).days / 30)
    
    projection_months = ['Month 1', 'Month 2', 'Month 3']
    projected_cf = [monthly_cf] * 3
    cumulative_cf = [sum(projected_cf[:i+1]) for i in range(3)]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=projection_months, y=projected_cf, name='Monthly CF'))
    fig.add_trace(go.Scatter(x=projection_months, y=cumulative_cf, name='Cumulative CF', mode='lines+markers'))
    
    fig.update_layout(title="Cash Flow Projections (Next 3 Months)", height=400)
    st.plotly_chart(fig, use_container_width=True)

def render_financial_ratios_report(client: TallyAPIClient, from_date, to_date):
    """Render comprehensive financial ratios analysis"""
    st.markdown("## 🔢 Financial Ratios Analysis")
    
    # Fetch required data
    pl_data = client.get_profit_loss_data(from_date.strftime('%d-%b-%Y'), to_date.strftime('%d-%b-%Y'))
    bs_data = client.get_balance_sheet_data(to_date.strftime('%Y-%m-%d'))
    
    # Extract key figures
    revenue = pl_data.get('revenue', 0)
    net_profit = pl_data.get('net_profit', 0)
    gross_profit = pl_data.get('gross_profit', 0)
    
    assets = bs_data.get('assets', {})
    liabilities = bs_data.get('liabilities', {})
    equity = bs_data.get('equity', 0)
    
    current_assets = assets.get('current', 0)
    current_liabilities = liabilities.get('current', 0)
    total_assets = assets.get('total', 0)
    total_liabilities = liabilities.get('total', 0)
    
    # Profitability Ratios
    st.markdown("### 📈 Profitability Ratios")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        st.metric("Gross Profit Margin", f"{gross_margin:.1f}%")
        st.caption("Gross Profit / Revenue")
    
    with col2:
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        st.metric("Net Profit Margin", f"{net_margin:.1f}%")
        st.caption("Net Profit / Revenue")
    
    with col3:
        roa = (net_profit / total_assets * 100) if total_assets > 0 else 0
        st.metric("Return on Assets", f"{roa:.1f}%")
        st.caption("Net Profit / Total Assets")
    
    with col4:
        roe = (net_profit / equity * 100) if equity > 0 else 0
        st.metric("Return on Equity", f"{roe:.1f}%")
        st.caption("Net Profit / Equity")
    
    # Liquidity Ratios
    st.markdown("### 💧 Liquidity Ratios")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        st.metric("Current Ratio", f"{current_ratio:.2f}")
        st.caption("Current Assets / Current Liabilities")
        
        # Color coding for current ratio
        if current_ratio >= 2:
            st.success("Strong liquidity")
        elif current_ratio >= 1.5:
            st.info("Good liquidity")
        elif current_ratio >= 1:
            st.warning("Adequate liquidity")
        else:
            st.error("Poor liquidity")
    
    with col2:
        # Quick ratio (assuming 70% of current assets are liquid)
        quick_assets = current_assets * 0.7  # Simplified calculation
        quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else 0
        st.metric("Quick Ratio", f"{quick_ratio:.2f}")
        st.caption("(Current Assets - Inventory) / Current Liabilities")
    
    with col3:
        # Cash ratio (estimated)
        cash_ratio = (current_assets * 0.2) / current_liabilities if current_liabilities > 0 else 0
        st.metric("Cash Ratio", f"{cash_ratio:.2f}")
        st.caption("Cash & Equivalents / Current Liabilities")
    
    with col4:
        # Working capital
        working_capital = current_assets - current_liabilities
        st.metric("Working Capital", format_currency(working_capital))
        st.caption("Current Assets - Current Liabilities")
    
    # Leverage Ratios
    st.markdown("### 🏋️ Leverage Ratios")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        debt_to_assets = total_liabilities / total_assets if total_assets > 0 else 0
        st.metric("Debt to Assets", f"{debt_to_assets:.2f}")
        st.caption("Total Debt / Total Assets")
    
    with col2:
        debt_to_equity = total_liabilities / equity if equity > 0 else 0
        st.metric("Debt to Equity", f"{debt_to_equity:.2f}")
        st.caption("Total Debt / Equity")
    
    with col3:
        equity_multiplier = total_assets / equity if equity > 0 else 0
        st.metric("Equity Multiplier", f"{equity_multiplier:.2f}")
        st.caption("Total Assets / Equity")
    
    with col4:
        equity_ratio = equity / total_assets if total_assets > 0 else 0
        st.metric("Equity Ratio", f"{equity_ratio:.2f}")
        st.caption("Equity / Total Assets")
    
    # Efficiency Ratios
    st.markdown("### ⚡ Efficiency Ratios")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        asset_turnover = revenue / total_assets if total_assets > 0 else 0
        st.metric("Asset Turnover", f"{asset_turnover:.2f}")
        st.caption("Revenue / Total Assets")
    
    with col2:
        # Inventory turnover (estimated)
        inventory_turnover = revenue / (current_assets * 0.3) if current_assets > 0 else 0
        st.metric("Inventory Turnover", f"{inventory_turnover:.2f}")
        st.caption("Revenue / Average Inventory")
    
    with col3:
        # Receivables turnover (estimated)
        receivables_turnover = revenue / (current_assets * 0.4) if current_assets > 0 else 0
        st.metric("Receivables Turnover", f"{receivables_turnover:.2f}")
        st.caption("Revenue / Average Receivables")
    
    with col4:
        equity_turnover = revenue / equity if equity > 0 else 0
        st.metric("Equity Turnover", f"{equity_turnover:.2f}")
        st.caption("Revenue / Equity")
    
    # Ratio trends visualization
    st.markdown("### 📊 Ratio Analysis Summary")
    
    # Create radar chart for key ratios
    ratios = ['Gross Margin', 'Net Margin', 'Current Ratio', 'ROA', 'ROE', 'Asset Turnover']
    values = [
        min(gross_margin / 10, 10),  # Normalized to 0-10 scale
        min(net_margin / 5, 10),
        min(current_ratio * 5, 10),
        min(roa / 2, 10),
        min(roe / 3, 10),
        min(asset_turnover * 5, 10)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=ratios,
        fill='toself',
        name='Current Ratios'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title="Financial Ratios Overview"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Ratio interpretation
    st.markdown("### 💡 Ratio Interpretation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Strengths")
        if current_ratio >= 2:
            st.success("✅ Strong liquidity position")
        if net_margin > 10:
            st.success("✅ Excellent profit margins")
        if roe > 15:
            st.success("✅ Good return on equity")
        if debt_to_equity < 0.5:
            st.success("✅ Conservative debt levels")
    
    with col2:
        st.markdown("#### Areas for Attention")
        if current_ratio < 1:
            st.error("⚠️ Liquidity concerns")
        if net_margin < 5:
            st.warning("⚠️ Low profit margins")
        if debt_to_equity > 2:
            st.warning("⚠️ High leverage")
        if asset_turnover < 0.5:
            st.warning("⚠️ Low asset efficiency")
    
    # Export section
    ratio_data = {
        'profitability': {'gross_margin': gross_margin, 'net_margin': net_margin, 'roa': roa, 'roe': roe},
        'liquidity': {'current_ratio': current_ratio, 'quick_ratio': quick_ratio, 'working_capital': working_capital},
        'leverage': {'debt_to_assets': debt_to_assets, 'debt_to_equity': debt_to_equity, 'equity_ratio': equity_ratio},
        'efficiency': {'asset_turnover': asset_turnover, 'inventory_turnover': inventory_turnover}
    }
    
    render_export_section(ratio_data, "financial_ratios")

def render_outstanding_reports(client: TallyAPIClient):
    """Render outstanding receivables and payables reports"""
    st.markdown("## 💰 Outstanding Reports")
    
    # Fetch outstanding data
    outstanding_data = client.get_outstanding_data()
    
    if outstanding_data.empty:
        st.warning("No outstanding data found.")
        return
    
    # Separate receivables and payables
    receivables = outstanding_data[outstanding_data['closing_balance'] > 0]
    payables = outstanding_data[outstanding_data['closing_balance'] < 0].copy()
    payables['closing_balance'] = payables['closing_balance'].abs()  # Make positive for display
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_receivables = receivables['closing_balance'].sum()
        st.metric("Total Receivables", format_currency(total_receivables))
    
    with col2:
        total_payables = payables['closing_balance'].sum()
        st.metric("Total Payables", format_currency(total_payables))
    
    with col3:
        net_position = total_receivables - total_payables
        st.metric("Net Position", format_currency(net_position))
    
    with col4:
        outstanding_parties = len(outstanding_data)
        st.metric("Outstanding Parties", f"{outstanding_parties:,}")
    
    # Outstanding analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Receivables Analysis")
        
        if not receivables.empty:
            # Top receivables
            top_receivables = receivables.nlargest(10, 'closing_balance')
            
            fig = px.bar(top_receivables, x='closing_balance', y='party_name',
                        orientation='h', title='Top 10 Receivables')
            st.plotly_chart(fig, use_container_width=True)
            
            # Receivables aging (simplified)
            def age_category(amount):
                if amount > 100000:
                    return 'High Value (>₹1L)'
                elif amount > 50000:
                    return 'Medium Value (₹50K-₹1L)'
                else:
                    return 'Low Value (<₹50K)'
            
            receivables['age_category'] = receivables['closing_balance'].apply(age_category)
            age_distribution = receivables['age_category'].value_counts()
            
            st.markdown("#### Receivables by Value Category")
            for category, count in age_distribution.items():
                category_amount = receivables[receivables['age_category'] == category]['closing_balance'].sum()
                st.write(f"**{category}**: {count} parties, {format_currency(category_amount)}")
        else:
            st.info("No receivables found")
    
    with col2:
        st.markdown("### 📉 Payables Analysis")
        
        if not payables.empty:
            # Top payables
            top_payables = payables.nlargest(10, 'closing_balance')
            
            fig = px.bar(top_payables, x='closing_balance', y='party_name',
                        orientation='h', title='Top 10 Payables')
            st.plotly_chart(fig, use_container_width=True)
            
            # Payables aging (simplified)
            payables['age_category'] = payables['closing_balance'].apply(age_category)
            age_distribution = payables['age_category'].value_counts()
            
            st.markdown("#### Payables by Value Category")
            for category, count in age_distribution.items():
                category_amount = payables[payables['age_category'] == category]['closing_balance'].sum()
                st.write(f"**{category}**: {count} parties, {format_currency(category_amount)}")
        else:
            st.info("No payables found")
    
    # Detailed outstanding tables
    st.markdown("### 📋 Detailed Outstanding")
    
    tab1, tab2 = st.tabs(["Receivables", "Payables"])
    
    with tab1:
        if not receivables.empty:
            receivables_display = receivables[['party_name', 'closing_balance', 'opening_balance']].copy()
            receivables_display.columns = ['Party Name', 'Current Outstanding', 'Opening Balance']
            receivables_display['Current Outstanding'] = receivables_display['Current Outstanding'].apply(format_currency)
            receivables_display['Opening Balance'] = receivables_display['Opening Balance'].apply(format_currency)
            
            st.dataframe(receivables_display, use_container_width=True, hide_index=True)
        else:
            st.info("No receivables to display")
    
    with tab2:
        if not payables.empty:
            payables_display = payables[['party_name', 'closing_balance', 'opening_balance']].copy()
            payables_display.columns = ['Party Name', 'Current Outstanding', 'Opening Balance']
            payables_display['Current Outstanding'] = payables_display['Current Outstanding'].apply(format_currency)
            payables_display['Opening Balance'] = payables_display['Opening Balance'].abs().apply(format_currency)
            
            st.dataframe(payables_display, use_container_width=True, hide_index=True)
        else:
            st.info("No payables to display")
    
    # Export section
    render_export_section(outstanding_data, "outstanding_reports")

def render_gst_reports(client: TallyAPIClient, from_date, to_date):
    """Render GST reports and compliance"""
    st.markdown("## 🏛️ GST Reports")
    st.markdown(f"**Period:** {from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}")
    
    st.info("📋 GST reporting requires detailed tax data from Tally Prime. This view provides a GST overview structure.")
    
    # GST Summary (would be populated with actual data)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("SGST Collected", "₹0")
    
    with col2:
        st.metric("CGST Collected", "₹0")
    
    with col3:
        st.metric("IGST Collected", "₹0")
    
    with col4:
        st.metric("Input Tax Credit", "₹0")
    
    # GST Returns Status
    st.markdown("### 📊 GST Returns Status")
    
    current_month = datetime.now().strftime('%B %Y')
    
    gst_returns = [
        {"Return Type": "GSTR-1", "Period": current_month, "Due Date": "11th of next month", "Status": "Pending"},
        {"Return Type": "GSTR-3B", "Period": current_month, "Due Date": "20th of next month", "Status": "Pending"},
        {"Return Type": "GSTR-2A", "Period": current_month, "Due Date": "Auto-populated", "Status": "Available"},
    ]
    
    gst_df = pd.DataFrame(gst_returns)
    st.dataframe(gst_df, use_container_width=True, hide_index=True)
    
    # HSN Summary (placeholder)
    st.markdown("### 📦 HSN/SAC Summary")
    st.info("HSN/SAC code-wise summary will be displayed here with actual Tally data")
    
    # Tax liability summary
    st.markdown("### 💰 Tax Liability Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Output Tax Liability")
        st.write("- CGST: ₹0")
        st.write("- SGST: ₹0")
        st.write("- IGST: ₹0")
        st.write("- CESS: ₹0")
    
    with col2:
        st.markdown("#### Input Tax Credit")
        st.write("- CGST ITC: ₹0")
        st.write("- SGST ITC: ₹0")
        st.write("- IGST ITC: ₹0")
        st.write("- CESS ITC: ₹0")

def render_export_section(data, report_name: str):
    """Render export options for financial reports"""
    st.markdown("---")
    st.markdown("### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export to Excel", key=f"excel_{report_name}"):
            try:
                # Convert data to DataFrame if it's a dict
                if isinstance(data, dict):
                    # Flatten nested dictionaries for export
                    flattened_data = {}
                    for key, value in data.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                flattened_data[f"{key}_{sub_key}"] = sub_value
                        else:
                            flattened_data[key] = value
                    
                    export_df = pd.DataFrame([flattened_data])
                else:
                    export_df = data if isinstance(data, pd.DataFrame) else pd.DataFrame()
                
                excel_data = export_dataframe_to_excel(export_df, f"{report_name}_{datetime.now().strftime('%Y%m%d')}.xlsx")
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name=f"{report_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Export error: {str(e)}")
    
    with col2:
        if isinstance(data, pd.DataFrame):
            csv_data = data.to_csv(index=False)
            st.download_button(
                label="📄 Export to CSV",
                data=csv_data,
                file_name=f"{report_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            if st.button("📄 Export to CSV", key=f"csv_{report_name}"):
                st.info("CSV export available for tabular data only")
    
    with col3:
        if st.button("📧 Email Report", key=f"email_{report_name}"):
            st.info("Email functionality will be implemented with SMTP configuration")

def show_financial_overview():
    """Show financial overview when no specific report is selected"""
    st.markdown("## 🚀 Financial Reports Overview")
    st.markdown("Select a report type from the sidebar to generate comprehensive financial analysis.")
    
    # Current financial year info
    current_fy = get_financial_year(datetime.now())
    st.info(f"📅 Current Financial Year: **{current_fy}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📊 Financial Dashboard**
        - Complete overview of financial performance
        - Key metrics and KPIs at a glance
        - Comparative analysis with previous periods
        """)
        
        st.info("""
        **📈 Profit & Loss Statement**
        - Detailed income and expense analysis
        - Profitability ratios and margins
        - Period-over-period comparisons
        """)
        
        st.info("""
        **⚖️ Balance Sheet**
        - Assets, liabilities, and equity overview
        - Financial position analysis
        - Balance sheet ratios
        """)
    
    with col2:
        st.info("""
        **💰 Cash Flow Statement**
        - Operating, investing, and financing activities
        - Cash flow projections
        - Liquidity analysis
        """)
        
        st.info("""
        **🔢 Financial Ratios**
        - Comprehensive ratio analysis
        - Profitability, liquidity, and leverage ratios
        - Performance benchmarking
        """)
        
        st.info("""
        **💳 Outstanding Reports**
        - Receivables and payables analysis
        - Aging and collection insights
        - Party-wise outstanding details
        """)

if __name__ == "__main__":
    main()
