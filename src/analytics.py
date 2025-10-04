import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AdvancedAnalytics:
    """Advanced analytics and ML capabilities"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def sales_forecasting(self, sales_data: pd.DataFrame, forecast_days: int = 30) -> Dict:
        """AI-powered sales forecasting"""
        if sales_data.empty or 'date' not in sales_data.columns:
            return {'error': 'Insufficient data for forecasting'}
        
        try:
            # Prepare data
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            daily_sales = sales_data.groupby(sales_data['date'].dt.date)['amount'].sum().reset_index()
            daily_sales['date'] = pd.to_datetime(daily_sales['date'])
            daily_sales = daily_sales.sort_values('date')
            
            if len(daily_sales) < 7:
                return {'error': 'Need at least 7 days of data for forecasting'}
            
            # Feature engineering
            daily_sales['day_num'] = (daily_sales['date'] - daily_sales['date'].min()).dt.days
            daily_sales['day_of_week'] = daily_sales['date'].dt.dayofweek
            daily_sales['month'] = daily_sales['date'].dt.month
            daily_sales['is_weekend'] = daily_sales['day_of_week'].isin([5, 6]).astype(int)
            
            # Prepare features
            features = ['day_num', 'day_of_week', 'month', 'is_weekend']
            X = daily_sales[features].values
            y = daily_sales['amount'].values
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Generate forecast
            last_date = daily_sales['date'].max()
            forecast_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
            
            forecast_features = []
            for date in forecast_dates:
                day_num = (date - daily_sales['date'].min()).days
                day_of_week = date.dayofweek
                month = date.month
                is_weekend = int(date.dayofweek in [5, 6])
                forecast_features.append([day_num, day_of_week, month, is_weekend])
            
            forecast_values = model.predict(forecast_features)
            
            # Calculate confidence intervals (simplified)
            residuals = y - model.predict(X)
            std_residual = np.std(residuals)
            confidence_upper = forecast_values + 1.96 * std_residual
            confidence_lower = forecast_values - 1.96 * std_residual
            
            return {
                'forecast_dates': forecast_dates,
                'forecast_values': forecast_values.tolist(),
                'confidence_upper': confidence_upper.tolist(),
                'confidence_lower': confidence_lower.tolist(),
                'historical_data': daily_sales,
                'model_accuracy': model.score(X, y)
            }
            
        except Exception as e:
            return {'error': f'Forecasting error: {str(e)}'}
    
    def customer_segmentation(self, sales_data: pd.DataFrame) -> Dict:
        """RFM-based customer segmentation"""
        if sales_data.empty or 'party_name' not in sales_data.columns:
            return {'error': 'Insufficient customer data'}
        
        try:
            # Calculate RFM metrics
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            current_date = sales_data['date'].max()
            
            rfm = sales_data.groupby('party_name').agg({
                'date': lambda x: (current_date - x.max()).days,  # Recency
                'voucher_number': 'nunique',  # Frequency
                'amount': 'sum'  # Monetary
            }).reset_index()
            
            rfm.columns = ['customer', 'recency', 'frequency', 'monetary']
            
            # Handle edge cases
            if len(rfm) < 3:
                return {'error': 'Need at least 3 customers for segmentation'}
            
            # Normalize RFM values
            rfm_normalized = rfm[['recency', 'frequency', 'monetary']].copy()
            rfm_normalized['recency'] = 1 / (rfm_normalized['recency'] + 1)  # Invert recency
            rfm_normalized = self.scaler.fit_transform(rfm_normalized)
            
            # Perform clustering
            n_clusters = min(4, len(rfm))  # Max 4 clusters
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            rfm['segment'] = kmeans.fit_predict(rfm_normalized)
            
            # Label segments
            segment_labels = {
                0: 'Champions',
                1: 'Loyal Customers', 
                2: 'Potential Loyalists',
                3: 'At Risk'
            }
            
            rfm['segment_name'] = rfm['segment'].map(lambda x: segment_labels.get(x, f'Segment {x}'))
            
            # Calculate segment statistics
            segment_stats = rfm.groupby('segment_name').agg({
                'recency': 'mean',
                'frequency': 'mean',
                'monetary': 'mean',
                'customer': 'count'
            }).round(2)
            
            return {
                'rfm_data': rfm,
                'segment_stats': segment_stats,
                'cluster_centers': kmeans.cluster_centers_
            }
            
        except Exception as e:
            return {'error': f'Segmentation error: {str(e)}'}
    
    def product_trend_analysis(self, sales_data: pd.DataFrame) -> Dict:
        """Analyze product trends and identify fast/slow movers"""
        if sales_data.empty:
            return {'error': 'No sales data available'}
        
        try:
            # Group by product and calculate metrics
            if 'stock_item' not in sales_data.columns:
                # If no stock item info, use a placeholder analysis
                product_analysis = {
                    'error': 'Stock item information not available in sales data'
                }
                return product_analysis
            
            product_sales = sales_data.groupby('stock_item').agg({
                'amount': ['sum', 'count', 'mean'],
                'date': ['min', 'max']
            }).reset_index()
            
            product_sales.columns = ['product', 'total_sales', 'transaction_count', 'avg_sale', 'first_sale', 'last_sale']
            
            # Calculate velocity metrics
            product_sales['sales_velocity'] = product_sales['total_sales'] / product_sales['transaction_count']
            product_sales['sales_frequency'] = product_sales['transaction_count']
            
            # Categorize products
            velocity_threshold = product_sales['sales_velocity'].quantile(0.7)
            frequency_threshold = product_sales['sales_frequency'].quantile(0.7)
            
            def categorize_product(row):
                if row['sales_velocity'] >= velocity_threshold and row['sales_frequency'] >= frequency_threshold:
                    return 'Fast Mover'
                elif row['sales_velocity'] >= velocity_threshold:
                    return 'High Value'
                elif row['sales_frequency'] >= frequency_threshold:
                    return 'Frequent Seller'
                else:
                    return 'Slow Mover'
            
            product_sales['category'] = product_sales.apply(categorize_product, axis=1)
            
            # Seasonal analysis
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            sales_data['month'] = sales_data['date'].dt.month
            monthly_trends = sales_data.groupby(['stock_item', 'month'])['amount'].sum().reset_index()
            
            return {
                'product_analysis': product_sales,
                'monthly_trends': monthly_trends,
                'fast_movers': product_sales[product_sales['category'] == 'Fast Mover'],
                'slow_movers': product_sales[product_sales['category'] == 'Slow Mover']
            }
            
        except Exception as e:
            return {'error': f'Product analysis error: {str(e)}'}
    
    def seasonal_pattern_analysis(self, sales_data: pd.DataFrame) -> Dict:
        """Analyze seasonal patterns in sales"""
        if sales_data.empty:
            return {'error': 'No sales data available'}
        
        try:
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            sales_data['month'] = sales_data['date'].dt.month
            sales_data['quarter'] = sales_data['date'].dt.quarter
            sales_data['day_of_week'] = sales_data['date'].dt.dayofweek
            sales_data['week_of_year'] = sales_data['date'].dt.isocalendar().week
            
            # Monthly patterns
            monthly_sales = sales_data.groupby('month')['amount'].sum().reset_index()
            monthly_sales['month_name'] = monthly_sales['month'].apply(
                lambda x: datetime(2023, x, 1).strftime('%B')
            )
            
            # Weekly patterns
            weekly_sales = sales_data.groupby('day_of_week')['amount'].sum().reset_index()
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_sales['day_name'] = weekly_sales['day_of_week'].apply(lambda x: day_names[x])
            
            # Quarterly patterns
            quarterly_sales = sales_data.groupby('quarter')['amount'].sum().reset_index()
            
            return {
                'monthly_patterns': monthly_sales,
                'weekly_patterns': weekly_sales,
                'quarterly_patterns': quarterly_sales,
                'peak_month': monthly_sales.loc[monthly_sales['amount'].idxmax(), 'month_name'],
                'peak_day': weekly_sales.loc[weekly_sales['amount'].idxmax(), 'day_name']
            }
            
        except Exception as e:
            return {'error': f'Seasonal analysis error: {str(e)}'}

def render_sales_forecasting(analytics: AdvancedAnalytics, sales_data: pd.DataFrame):
    """Render sales forecasting dashboard"""
    st.markdown("### 🔮 Sales Forecasting")
    
    # Forecast parameters
    col1, col2 = st.columns(2)
    with col1:
        forecast_days = st.slider("Forecast Period (days)", 7, 90, 30)
    with col2:
        if st.button("Generate Forecast"):
            st.session_state.generate_forecast = True
    
    if st.session_state.get('generate_forecast', False) and not sales_data.empty:
        with st.spinner("Generating AI-powered forecast..."):
            forecast_result = analytics.sales_forecasting(sales_data, forecast_days)
        
        if 'error' not in forecast_result:
            # Plot forecast
            fig = go.Figure()
            
            # Historical data
            historical = forecast_result['historical_data']
            fig.add_trace(go.Scatter(
                x=historical['date'],
                y=historical['amount'],
                mode='lines+markers',
                name='Historical Sales',
                line=dict(color='blue')
            ))
            
            # Forecast
            fig.add_trace(go.Scatter(
                x=forecast_result['forecast_dates'],
                y=forecast_result['forecast_values'],
                mode='lines+markers',
                name='Forecast',
                line=dict(color='red', dash='dash')
            ))
            
            # Confidence intervals
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
            
            fig.update_layout(
                title='Sales Forecast with Confidence Intervals',
                xaxis_title='Date',
                yaxis_title='Sales Amount (₹)',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_forecast = sum(forecast_result['forecast_values'])
                st.metric("Forecasted Sales", f"₹{total_forecast:,.0f}")
            with col2:
                avg_daily = total_forecast / forecast_days
                st.metric("Avg Daily Sales", f"₹{avg_daily:,.0f}")
            with col3:
                accuracy = forecast_result.get('model_accuracy', 0) * 100
                st.metric("Model Accuracy", f"{accuracy:.1f}%")
        else:
            st.error(forecast_result['error'])

def render_customer_segmentation(analytics: AdvancedAnalytics, sales_data: pd.DataFrame):
    """Render customer segmentation analysis"""
    st.markdown("### 👥 Customer Segmentation")
    
    if not sales_data.empty:
        with st.spinner("Performing RFM analysis..."):
            segmentation_result = analytics.customer_segmentation(sales_data)
        
        if 'error' not in segmentation_result:
            rfm_data = segmentation_result['rfm_data']
            segment_stats = segmentation_result['segment_stats']
            
            # Segment distribution
            col1, col2 = st.columns(2)
            
            with col1:
                segment_counts = rfm_data['segment_name'].value_counts()
                fig = px.pie(values=segment_counts.values, names=segment_counts.index,
                           title='Customer Segment Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # RFM scatter plot
                fig = px.scatter_3d(rfm_data, x='recency', y='frequency', z='monetary',
                                  color='segment_name', title='RFM 3D Analysis',
                                  hover_data=['customer'])
                st.plotly_chart(fig, use_container_width=True)
            
            # Segment statistics
            st.markdown("#### Segment Statistics")
            st.dataframe(segment_stats, use_container_width=True)
            
            # Top customers by segment
            st.markdown("#### Segment Details")
            selected_segment = st.selectbox("Select Segment", rfm_data['segment_name'].unique())
            
            segment_customers = rfm_data[rfm_data['segment_name'] == selected_segment].sort_values('monetary', ascending=False)
            st.dataframe(segment_customers, use_container_width=True)
            
        else:
            st.error(segmentation_result['error'])
    else:
        st.info("No sales data available for customer segmentation")

def render_seasonal_analysis(analytics: AdvancedAnalytics, sales_data: pd.DataFrame):
    """Render seasonal pattern analysis"""
    st.markdown("### 📅 Seasonal Pattern Analysis")
    
    if not sales_data.empty:
        with st.spinner("Analyzing seasonal patterns..."):
            seasonal_result = analytics.seasonal_pattern_analysis(sales_data)
        
        if 'error' not in seasonal_result:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Monthly Patterns', 'Weekly Patterns', 
                              'Quarterly Patterns', 'Sales Heatmap'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Monthly patterns
            monthly = seasonal_result['monthly_patterns']
            fig.add_trace(
                go.Bar(x=monthly['month_name'], y=monthly['amount'], name='Monthly Sales'),
                row=1, col=1
            )
            
            # Weekly patterns
            weekly = seasonal_result['weekly_patterns']
            fig.add_trace(
                go.Bar(x=weekly['day_name'], y=weekly['amount'], name='Weekly Sales'),
                row=1, col=2
            )
            
            # Quarterly patterns
            quarterly = seasonal_result['quarterly_patterns']
            fig.add_trace(
                go.Bar(x=[f'Q{q}' for q in quarterly['quarter']], y=quarterly['amount'], name='Quarterly Sales'),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insights
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peak Month", seasonal_result['peak_month'])
            with col2:
                st.metric("Peak Day", seasonal_result['peak_day'])
            with col3:
                best_quarter = quarterly.loc[quarterly['amount'].idxmax(), 'quarter']
                st.metric("Best Quarter", f"Q{best_quarter}")
                
        else:
            st.error(seasonal_result['error'])
    else:
        st.info("No sales data available for seasonal analysis")

def render_root_cause_analysis(sales_data: pd.DataFrame, inventory_data: pd.DataFrame):
    """Render root cause analysis for business insights"""
    st.markdown("### 🔍 Root Cause Analysis")
    
    # Sales variance analysis
    if not sales_data.empty:
        st.markdown("#### Sales Performance Analysis")
        
        # Calculate period-over-period variance
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        sales_data['month_year'] = sales_data['date'].dt.to_period('M')
        
        monthly_sales = sales_data.groupby('month_year')['amount'].sum()
        
        if len(monthly_sales) >= 2:
            current_month = monthly_sales.iloc[-1]
            previous_month = monthly_sales.iloc[-2]
            variance = ((current_month - previous_month) / previous_month) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Month", f"₹{current_month:,.0f}")
            with col2:
                st.metric("Previous Month", f"₹{previous_month:,.0f}")
            with col3:
                st.metric("Variance", f"{variance:.1f}%")
            
            # Analyze reasons for variance
            reasons = []
            if abs(variance) > 10:
                if variance > 0:
                    reasons.append("📈 Sales increased - possible reasons: seasonal demand, successful campaigns, new products")
                else:
                    reasons.append("📉 Sales decreased - possible reasons: market conditions, inventory issues, competition")
            
            if not inventory_data.empty:
                low_stock_items = len(inventory_data[inventory_data['closing_balance'] <= inventory_data['reorder_level']])
                if low_stock_items > 0:
                    reasons.append(f"📦 {low_stock_items} items are below reorder level - may impact sales")
            
            if reasons:
                st.markdown("#### Potential Impact Factors:")
                for reason in reasons:
                    st.info(reason)
        else:
            st.info("Need at least 2 months of data for variance analysis")

# Analytics utility functions
def calculate_kpis(sales_data: pd.DataFrame, inventory_data: pd.DataFrame, outstanding_data: pd.DataFrame) -> Dict:
    """Calculate key performance indicators"""
    kpis = {}
    
    if not sales_data.empty:
        kpis['total_sales'] = sales_data['amount'].sum()
        kpis['avg_transaction_value'] = sales_data['amount'].mean()
        kpis['sales_count'] = len(sales_data)
    
    if not inventory_data.empty:
        kpis['total_inventory_value'] = inventory_data['closing_value'].sum()
        kpis['inventory_items'] = len(inventory_data)
        kpis['low_stock_items'] = len(inventory_data[inventory_data['closing_balance'] <= inventory_data['reorder_level']])
    
    if not outstanding_data.empty:
        kpis['total_receivables'] = outstanding_data['closing_balance'].sum()
        kpis['overdue_customers'] = len(outstanding_data[outstanding_data['closing_balance'] > 0])
    
    return kpis

def export_analysis_report(analysis_data: Dict, report_type: str) -> bytes:
    """Export analysis report to various formats"""
    # This would implement actual export functionality
    # For now, return a placeholder
    import json
    report_json = json.dumps(analysis_data, indent=2, default=str)
    return report_json.encode('utf-8')
