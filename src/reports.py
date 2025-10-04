import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any
from src.tally_api import TallyAPIClient
from src.auth import check_permission, require_permission
import io
import base64

class ReportGenerator:
    """Generate various business reports from Tally data"""
    
    def __init__(self, tally_client: TallyAPIClient):
        self.tally_client = tally_client
    
    def generate_sales_report(self, from_date: str, to_date: str, 
                            group_by: str = 'daily') -> Dict:
        """Generate comprehensive sales report"""
        sales_data = self.tally_client.get_sales_data(from_date, to_date)
        
        if sales_data.empty:
            return {'error': 'No sales data found for the selected period'}
        
        # Convert date column
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        
        report = {
            'summary': {
                'total_sales': sales_data['amount'].sum(),
                'total_transactions': len(sales_data),
                'average_transaction': sales_data['amount'].mean(),
                'period_from': from_date,
                'period_to': to_date
            },
            'data': sales_data
        }
        
        # Group data based on selection
        if group_by == 'daily':
            grouped_data = sales_data.groupby(sales_data['date'].dt.date)['amount'].agg(['sum', 'count']).reset_index()
            grouped_data.columns = ['date', 'total_amount', 'transaction_count']
        elif group_by == 'monthly':
            grouped_data = sales_data.groupby(sales_data['date'].dt.to_period('M'))['amount'].agg(['sum', 'count']).reset_index()
            grouped_data.columns = ['period', 'total_amount', 'transaction_count']
        elif group_by == 'customer':
            grouped_data = sales_data.groupby('party_name')['amount'].agg(['sum', 'count']).reset_index()
            grouped_data.columns = ['customer', 'total_amount', 'transaction_count']
        
        report['grouped_data'] = grouped_data
        
        # Top customers
        if 'party_name' in sales_data.columns:
            top_customers = sales_data.groupby('party_name')['amount'].sum().nlargest(10).reset_index()
            report['top_customers'] = top_customers
        
        return report
    
    def generate_purchase_report(self, from_date: str, to_date: str) -> Dict:
        """Generate purchase analysis report"""
        purchase_data = self.tally_client.get_purchase_data(from_date, to_date)
        
        if purchase_data.empty:
            return {'error': 'No purchase data found for the selected period'}
        
        purchase_data['date'] = pd.to_datetime(purchase_data['date'])
        
        report = {
            'summary': {
                'total_purchases': purchase_data['amount'].sum(),
                'total_orders': len(purchase_data),
                'average_order_value': purchase_data['amount'].mean(),
                'period_from': from_date,
                'period_to': to_date
            },
            'data': purchase_data
        }
        
        # Top suppliers
        if 'party_name' in purchase_data.columns:
            top_suppliers = purchase_data.groupby('party_name')['amount'].sum().nlargest(10).reset_index()
            report['top_suppliers'] = top_suppliers
        
        # Monthly trend
        monthly_purchases = purchase_data.groupby(purchase_data['date'].dt.to_period('M'))['amount'].sum().reset_index()
        report['monthly_trend'] = monthly_purchases
        
        return report
    
    def generate_inventory_report(self) -> Dict:
        """Generate inventory status report"""
        inventory_data = self.tally_client.get_inventory_data()
        
        if inventory_data.empty:
            return {'error': 'No inventory data found'}
        
        # Calculate metrics
        total_items = len(inventory_data)
        total_value = inventory_data['closing_value'].sum()
        zero_stock_items = len(inventory_data[inventory_data['closing_balance'] <= 0])
        
        # Low stock analysis
        inventory_data['is_low_stock'] = (
            inventory_data['closing_balance'] <= inventory_data['reorder_level']
        )
        low_stock_items = inventory_data[inventory_data['is_low_stock']]
        
        # Stock aging (simplified - would need more data in real scenario)
        inventory_data['stock_category'] = inventory_data['closing_balance'].apply(
            lambda x: 'High Stock' if x > 100 else ('Medium Stock' if x > 50 else 'Low Stock')
        )
        
        report = {
            'summary': {
                'total_items': total_items,
                'total_value': total_value,
                'zero_stock_items': zero_stock_items,
                'low_stock_items': len(low_stock_items),
                'stock_health': ((total_items - len(low_stock_items)) / total_items) * 100 if total_items > 0 else 0
            },
            'data': inventory_data,
            'low_stock_items': low_stock_items,
            'category_distribution': inventory_data['stock_category'].value_counts().to_dict()
        }
        
        return report
    
    def generate_outstanding_report(self) -> Dict:
        """Generate outstanding receivables/payables report"""
        outstanding_data = self.tally_client.get_outstanding_data()
        
        if outstanding_data.empty:
            return {'error': 'No outstanding data found'}
        
        # Separate receivables and payables
        receivables = outstanding_data[outstanding_data['closing_balance'] > 0]
        payables = outstanding_data[outstanding_data['closing_balance'] < 0]
        
        # Aging analysis (simplified)
        def categorize_aging(amount):
            if abs(amount) > 100000:
                return 'High Value'
            elif abs(amount) > 50000:
                return 'Medium Value'
            else:
                return 'Low Value'
        
        outstanding_data['aging_category'] = outstanding_data['closing_balance'].apply(categorize_aging)
        
        report = {
            'summary': {
                'total_receivables': receivables['closing_balance'].sum(),
                'total_payables': abs(payables['closing_balance'].sum()),
                'net_position': outstanding_data['closing_balance'].sum(),
                'receivable_parties': len(receivables),
                'payable_parties': len(payables)
            },
            'receivables': receivables,
            'payables': payables.copy(),  # Make copy to avoid warning
            'aging_analysis': outstanding_data['aging_category'].value_counts().to_dict()
        }
        
        # Make amounts positive for payables display
        if not report['payables'].empty:
            report['payables']['closing_balance'] = report['payables']['closing_balance'].abs()
        
        return report
    
    def generate_financial_summary(self, from_date: str, to_date: str) -> Dict:
        """Generate financial summary report"""
        try:
            # Get P&L data
            pl_data = self.tally_client.get_profit_loss_data(from_date, to_date)
            
            # Get Balance Sheet data  
            balance_sheet_data = self.tally_client.get_balance_sheet_data(to_date)
            
            # Calculate financial ratios
            ratios = {}
            if balance_sheet_data['assets']['total'] > 0 and balance_sheet_data['liabilities']['total'] > 0:
                ratios['current_ratio'] = (
                    balance_sheet_data['assets']['current'] / balance_sheet_data['liabilities']['current']
                    if balance_sheet_data['liabilities']['current'] > 0 else 0
                )
                ratios['debt_equity_ratio'] = (
                    balance_sheet_data['liabilities']['total'] / balance_sheet_data['equity']
                    if balance_sheet_data['equity'] > 0 else 0
                )
                ratios['asset_turnover'] = (
                    pl_data['revenue'] / balance_sheet_data['assets']['total']
                    if balance_sheet_data['assets']['total'] > 0 else 0
                )
                ratios['profit_margin'] = (
                    (pl_data['net_profit'] / pl_data['revenue']) * 100
                    if pl_data['revenue'] > 0 else 0
                )
            
            report = {
                'profit_loss': pl_data,
                'balance_sheet': balance_sheet_data,
                'financial_ratios': ratios,
                'period': {'from': from_date, 'to': to_date}
            }
            
            return report
            
        except Exception as e:
            return {'error': f'Error generating financial summary: {str(e)}'}

def render_sales_report_page():
    """Render sales reports page"""
    st.title("📈 Sales Reports")
    
    # Date range selection
    col1, col2, col3 = st.columns(3)
    with col1:
        from_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
    with col2:
        to_date = st.date_input("To Date", datetime.now())
    with col3:
        group_by = st.selectbox("Group By", ["daily", "monthly", "customer"])
    
    if st.button("Generate Sales Report"):
        tally_client = TallyAPIClient(st.session_state.get('tally_server'))
        report_generator = ReportGenerator(tally_client)
        
        with st.spinner("Generating sales report..."):
            report = report_generator.generate_sales_report(
                from_date.strftime('%d-%b-%Y'),
                to_date.strftime('%d-%b-%Y'),
                group_by
            )
        
        if 'error' not in report:
            # Display summary metrics
            summary = report['summary']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Sales", f"₹{summary['total_sales']:,.0f}")
            with col2:
                st.metric("Transactions", f"{summary['total_transactions']:,}")
            with col3:
                st.metric("Avg Transaction", f"₹{summary['average_transaction']:,.0f}")
            
            # Sales trend chart
            st.markdown("### Sales Trend")
            grouped_data = report['grouped_data']
            
            if group_by == 'daily':
                fig = px.line(grouped_data, x='date', y='total_amount', 
                            title='Daily Sales Trend')
            elif group_by == 'monthly':
                fig = px.bar(grouped_data, x='period', y='total_amount',
                           title='Monthly Sales')
            else:  # customer
                fig = px.bar(grouped_data.head(10), x='total_amount', y='customer',
                           orientation='h', title='Top 10 Customers')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Top customers table
            if 'top_customers' in report:
                st.markdown("### Top Customers")
                st.dataframe(report['top_customers'], use_container_width=True)
            
            # Detailed data
            with st.expander("View Detailed Data"):
                st.dataframe(report['data'], use_container_width=True)
            
            # Export options
            render_export_options(report, "sales_report")
            
        else:
            st.error(report['error'])

def render_purchase_report_page():
    """Render purchase reports page"""
    st.title("📦 Purchase Reports")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", datetime.now() - timedelta(days=30), key="purchase_from")
    with col2:
        to_date = st.date_input("To Date", datetime.now(), key="purchase_to")
    
    if st.button("Generate Purchase Report"):
        tally_client = TallyAPIClient(st.session_state.get('tally_server'))
        report_generator = ReportGenerator(tally_client)
        
        with st.spinner("Generating purchase report..."):
            report = report_generator.generate_purchase_report(
                from_date.strftime('%d-%b-%Y'),
                to_date.strftime('%d-%b-%Y')
            )
        
        if 'error' not in report:
            # Display summary
            summary = report['summary']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Purchases", f"₹{summary['total_purchases']:,.0f}")
            with col2:
                st.metric("Orders", f"{summary['total_orders']:,}")
            with col3:
                st.metric("Avg Order Value", f"₹{summary['average_order_value']:,.0f}")
            
            # Purchase trend
            if 'monthly_trend' in report:
                st.markdown("### Monthly Purchase Trend")
                fig = px.line(report['monthly_trend'], x='period', y='amount',
                            title='Monthly Purchases')
                st.plotly_chart(fig, use_container_width=True)
            
            # Top suppliers
            if 'top_suppliers' in report:
                st.markdown("### Top Suppliers")
                fig = px.bar(report['top_suppliers'], x='amount', y='party_name',
                           orientation='h', title='Top 10 Suppliers')
                st.plotly_chart(fig, use_container_width=True)
            
            # Export options
            render_export_options(report, "purchase_report")
            
        else:
            st.error(report['error'])

def render_inventory_report_page():
    """Render inventory reports page"""
    st.title("📦 Inventory Reports")
    
    if st.button("Generate Inventory Report"):
        tally_client = TallyAPIClient(st.session_state.get('tally_server'))
        report_generator = ReportGenerator(tally_client)
        
        with st.spinner("Generating inventory report..."):
            report = report_generator.generate_inventory_report()
        
        if 'error' not in report:
            # Summary metrics
            summary = report['summary']
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Items", f"{summary['total_items']:,}")
            with col2:
                st.metric("Total Value", f"₹{summary['total_value']:,.0f}")
            with col3:
                st.metric("Zero Stock", f"{summary['zero_stock_items']:,}")
            with col4:
                st.metric("Stock Health", f"{summary['stock_health']:.1f}%")
            
            # Stock distribution
            st.markdown("### Stock Distribution")
            category_dist = report['category_distribution']
            fig = px.pie(values=list(category_dist.values()), 
                        names=list(category_dist.keys()),
                        title='Stock Categories')
            st.plotly_chart(fig, use_container_width=True)
            
            # Low stock alerts
            if not report['low_stock_items'].empty:
                st.markdown("### ⚠️ Low Stock Items")
                st.dataframe(report['low_stock_items'][['name', 'closing_balance', 'reorder_level']], 
                           use_container_width=True)
            
            # Detailed inventory
            with st.expander("View Complete Inventory"):
                st.dataframe(report['data'], use_container_width=True)
            
            # Export options
            render_export_options(report, "inventory_report")
            
        else:
            st.error(report['error'])

def render_outstanding_report_page():
    """Render outstanding receivables/payables report"""
    st.title("💰 Outstanding Reports")
    
    if st.button("Generate Outstanding Report"):
        tally_client = TallyAPIClient(st.session_state.get('tally_server'))
        report_generator = ReportGenerator(tally_client)
        
        with st.spinner("Generating outstanding report..."):
            report = report_generator.generate_outstanding_report()
        
        if 'error' not in report:
            # Summary metrics
            summary = report['summary']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Receivables", f"₹{summary['total_receivables']:,.0f}")
            with col2:
                st.metric("Total Payables", f"₹{summary['total_payables']:,.0f}")
            with col3:
                st.metric("Net Position", f"₹{summary['net_position']:,.0f}")
            
            # Receivables vs Payables chart
            fig = go.Figure(data=[
                go.Bar(name='Receivables', x=['Amount'], y=[summary['total_receivables']]),
                go.Bar(name='Payables', x=['Amount'], y=[summary['total_payables']])
            ])
            fig.update_layout(title='Receivables vs Payables')
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed tables
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Top Receivables")
                if not report['receivables'].empty:
                    top_receivables = report['receivables'].nlargest(10, 'closing_balance')
                    st.dataframe(top_receivables[['party_name', 'closing_balance']], 
                               use_container_width=True)
            
            with col2:
                st.markdown("### Top Payables")
                if not report['payables'].empty:
                    top_payables = report['payables'].nlargest(10, 'closing_balance')
                    st.dataframe(top_payables[['party_name', 'closing_balance']], 
                               use_container_width=True)
            
            # Export options
            render_export_options(report, "outstanding_report")
            
        else:
            st.error(report['error'])

def render_financial_summary_page():
    """Render financial summary report"""
    st.title("📊 Financial Summary")
    
    # Date range for financial reports
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", datetime.now() - timedelta(days=90), key="fin_from")
    with col2:
        to_date = st.date_input("To Date", datetime.now(), key="fin_to")
    
    if st.button("Generate Financial Summary"):
        tally_client = TallyAPIClient(st.session_state.get('tally_server'))
        report_generator = ReportGenerator(tally_client)
        
        with st.spinner("Generating financial summary..."):
            report = report_generator.generate_financial_summary(
                from_date.strftime('%d-%b-%Y'),
                to_date.strftime('%d-%b-%Y')
            )
        
        if 'error' not in report:
            # P&L Summary
            st.markdown("### Profit & Loss Summary")
            pl_data = report['profit_loss']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Revenue", f"₹{pl_data['revenue']:,.0f}")
            with col2:
                st.metric("Gross Profit", f"₹{pl_data['gross_profit']:,.0f}")
            with col3:
                st.metric("Total Expenses", f"₹{pl_data['expenses']:,.0f}")
            with col4:
                st.metric("Net Profit", f"₹{pl_data['net_profit']:,.0f}")
            
            # Balance Sheet Summary
            st.markdown("### Balance Sheet Summary")
            bs_data = report['balance_sheet']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Assets", f"₹{bs_data['assets']['total']:,.0f}")
            with col2:
                st.metric("Total Liabilities", f"₹{bs_data['liabilities']['total']:,.0f}")
            with col3:
                st.metric("Equity", f"₹{bs_data['equity']:,.0f}")
            
            # Financial Ratios
            if report['financial_ratios']:
                st.markdown("### Key Financial Ratios")
                ratios = report['financial_ratios']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Ratio", f"{ratios.get('current_ratio', 0):.2f}")
                with col2:
                    st.metric("Debt-Equity Ratio", f"{ratios.get('debt_equity_ratio', 0):.2f}")
                with col3:
                    st.metric("Asset Turnover", f"{ratios.get('asset_turnover', 0):.2f}")
                with col4:
                    st.metric("Profit Margin", f"{ratios.get('profit_margin', 0):.1f}%")
            
            # Export options
            render_export_options(report, "financial_summary")
            
        else:
            st.error(report['error'])

def render_export_options(report_data: Dict, report_type: str):
    """Render export options for reports"""
    st.markdown("---")
    st.markdown("### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export to PDF", key=f"pdf_{report_type}"):
            # PDF export functionality would be implemented here
            st.info("PDF export functionality will be implemented")
    
    with col2:
        if st.button("📊 Export to Excel", key=f"excel_{report_type}"):
            # Excel export functionality
            try:
                excel_buffer = create_excel_export(report_data, report_type)
                st.download_button(
                    label="Download Excel File",
                    data=excel_buffer,
                    file_name=f"{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Excel export error: {str(e)}")
    
    with col3:
        if st.button("📧 Email Report", key=f"email_{report_type}"):
            st.info("Email functionality will be implemented")

def create_excel_export(report_data: Dict, report_type: str) -> bytes:
    """Create Excel export of report data"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write summary data
        if 'summary' in report_data:
            summary_df = pd.DataFrame([report_data['summary']])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Write detailed data
        if 'data' in report_data and isinstance(report_data['data'], pd.DataFrame):
            report_data['data'].to_excel(writer, sheet_name='Details', index=False)
        
        # Write additional sheets based on report type
        if report_type == 'sales_report' and 'top_customers' in report_data:
            report_data['top_customers'].to_excel(writer, sheet_name='Top Customers', index=False)
        
        elif report_type == 'inventory_report' and 'low_stock_items' in report_data:
            if not report_data['low_stock_items'].empty:
                report_data['low_stock_items'].to_excel(writer, sheet_name='Low Stock', index=False)
    
    output.seek(0)
    return output.getvalue()

# Report scheduling functionality (placeholder)
def schedule_report(report_type: str, frequency: str, recipients: List[str]):
    """Schedule automatic report generation and distribution"""
    # This would implement actual scheduling functionality
    # For now, just store the configuration
    if 'scheduled_reports' not in st.session_state:
        st.session_state.scheduled_reports = []
    
    schedule_config = {
        'report_type': report_type,
        'frequency': frequency,
        'recipients': recipients,
        'created_at': datetime.now(),
        'active': True
    }
    
    st.session_state.scheduled_reports.append(schedule_config)
    return schedule_config
