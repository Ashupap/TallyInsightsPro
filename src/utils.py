import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import io
from typing import Dict, List, Any, Optional, Tuple
import json
import os

def load_custom_css():
    """Load custom CSS for Tally-inspired styling"""
    css = """
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom metric styling */
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007BFF;
        margin-bottom: 1rem;
    }
    
    /* Alert styling */
    .alert-critical {
        border-left: 4px solid #dc3545;
        background-color: #f8d7da;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .alert-warning {
        border-left: 4px solid #ffc107;
        background-color: #fff3cd;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .alert-success {
        border-left: 4px solid #28a745;
        background-color: #d4edda;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    /* Dashboard tile styling */
    .dashboard-tile {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
        transition: box-shadow 0.3s ease;
    }
    
    .dashboard-tile:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* KPI card styling */
    .kpi-card {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Navigation styling */
    .nav-link {
        display: block;
        padding: 0.5rem 1rem;
        text-decoration: none;
        color: #495057;
        border-radius: 4px;
        margin: 0.25rem 0;
        transition: all 0.3s ease;
    }
    
    .nav-link:hover {
        background-color: #e9ecef;
        color: #007BFF;
        text-decoration: none;
    }
    
    .nav-link.active {
        background-color: #007BFF;
        color: white;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Custom progress bars */
    .progress-bar {
        width: 100%;
        height: 20px;
        background-color: #e9ecef;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%);
        transition: width 0.5s ease;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def format_currency(amount: float, currency: str = "₹") -> str:
    """Format amount as currency"""
    if pd.isna(amount) or amount is None:
        return f"{currency}0"
    
    if abs(amount) >= 10000000:  # 1 Crore
        return f"{currency}{amount/10000000:.1f}Cr"
    elif abs(amount) >= 100000:  # 1 Lakh
        return f"{currency}{amount/100000:.1f}L"
    elif abs(amount) >= 1000:  # 1 Thousand
        return f"{currency}{amount/1000:.1f}K"
    else:
        return f"{currency}{amount:,.0f}"

def format_number(number: float, precision: int = 0) -> str:
    """Format number with appropriate suffixes"""
    if pd.isna(number) or number is None:
        return "0"
    
    if abs(number) >= 1000000:
        return f"{number/1000000:.{precision}f}M"
    elif abs(number) >= 1000:
        return f"{number/1000:.{precision}f}K"
    else:
        return f"{number:,.{precision}f}"

def calculate_percentage_change(current: float, previous: float) -> Tuple[float, str]:
    """Calculate percentage change and return with appropriate formatting"""
    if previous == 0:
        return 0.0, "0%"
    
    change = ((current - previous) / previous) * 100
    formatted = f"{change:+.1f}%"
    return change, formatted

def get_date_range_options() -> Dict[str, Tuple[datetime, datetime]]:
    """Get predefined date range options"""
    today = datetime.now()
    
    return {
        "Today": (today, today),
        "Yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        "Last 7 Days": (today - timedelta(days=7), today),
        "Last 30 Days": (today - timedelta(days=30), today),
        "This Month": (today.replace(day=1), today),
        "Last Month": (
            (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            today.replace(day=1) - timedelta(days=1)
        ),
        "This Quarter": (get_quarter_start(today), today),
        "Last Quarter": (
            get_quarter_start(get_quarter_start(today) - timedelta(days=1)),
            get_quarter_start(today) - timedelta(days=1)
        ),
        "This Year": (today.replace(month=1, day=1), today),
        "Last Year": (
            today.replace(year=today.year-1, month=1, day=1),
            today.replace(year=today.year-1, month=12, day=31)
        )
    }

def get_quarter_start(date: datetime) -> datetime:
    """Get the start date of the quarter for given date"""
    quarter_start_month = [1, 4, 7, 10]
    quarter = (date.month - 1) // 3
    return date.replace(month=quarter_start_month[quarter], day=1)

def create_kpi_card(title: str, value: str, delta: str = None, help_text: str = None):
    """Create a KPI card component"""
    delta_color = ""
    if delta:
        if "+" in delta:
            delta_color = "color: #28a745;"
        elif "-" in delta:
            delta_color = "color: #dc3545;"
    
    help_icon = f'<span title="{help_text}">ⓘ</span>' if help_text else ""
    
    kpi_html = f"""
    <div class="kpi-card">
        <div class="kpi-label">{title} {help_icon}</div>
        <div class="kpi-value">{value}</div>
        {f'<div style="{delta_color} font-size: 0.9rem;">{delta}</div>' if delta else ''}
    </div>
    """
    
    st.markdown(kpi_html, unsafe_allow_html=True)

def create_progress_bar(value: float, max_value: float, label: str = ""):
    """Create a custom progress bar"""
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    
    progress_html = f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {percentage}%;"></div>
    </div>
    <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem;">
        {label}: {value:,.0f} / {max_value:,.0f} ({percentage:.1f}%)
    </div>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)

def export_dataframe_to_excel(df: pd.DataFrame, filename: str = None) -> bytes:
    """Export DataFrame to Excel format"""
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Data']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output.getvalue()

def create_download_button(data: bytes, filename: str, mime_type: str, label: str):
    """Create a download button for files"""
    b64_data = base64.b64encode(data).decode()
    
    download_html = f"""
    <a href="data:{mime_type};base64,{b64_data}" 
       download="{filename}" 
       style="text-decoration: none;">
        <button style="
            background-color: #007BFF;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        ">
            {label}
        </button>
    </a>
    """
    
    st.markdown(download_html, unsafe_allow_html=True)

def validate_date_range(from_date: datetime, to_date: datetime) -> bool:
    """Validate date range"""
    if from_date > to_date:
        st.error("From date cannot be later than To date")
        return False
    
    if (to_date - from_date).days > 365:
        st.warning("Date range is longer than 1 year. This may affect performance.")
    
    return True

def get_financial_year(date: datetime) -> str:
    """Get financial year for given date (April to March)"""
    if date.month >= 4:
        return f"FY {date.year}-{str(date.year + 1)[2:]}"
    else:
        return f"FY {date.year - 1}-{str(date.year)[2:]}"

def calculate_growth_rate(current_value: float, previous_value: float, periods: int = 1) -> float:
    """Calculate compound annual growth rate"""
    if previous_value <= 0 or current_value <= 0:
        return 0.0
    
    return ((current_value / previous_value) ** (1/periods) - 1) * 100

def create_comparison_chart(data: Dict[str, float], title: str = "Comparison"):
    """Create a simple comparison bar chart"""
    fig = go.Figure(data=[
        go.Bar(
            x=list(data.keys()),
            y=list(data.values()),
            marker_color='#007BFF'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Categories",
        yaxis_title="Values",
        height=400,
        margin=dict(t=40, b=40, l=40, r=40)
    )
    
    return fig

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def clean_currency_string(value: str) -> float:
    """Clean currency string and convert to float"""
    if not value or pd.isna(value):
        return 0.0
    
    # Remove currency symbols and commas
    cleaned = str(value).replace('₹', '').replace(',', '').replace('Rs.', '').strip()
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

def get_business_days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate business days between two dates"""
    return pd.bdate_range(start_date, end_date).size

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def create_alert_message(message: str, alert_type: str = "info"):
    """Create formatted alert message"""
    alert_colors = {
        "success": "#d4edda",
        "info": "#d1ecf1", 
        "warning": "#fff3cd",
        "error": "#f8d7da"
    }
    
    border_colors = {
        "success": "#28a745",
        "info": "#17a2b8",
        "warning": "#ffc107", 
        "error": "#dc3545"
    }
    
    alert_html = f"""
    <div class="alert-{alert_type}" style="
        background-color: {alert_colors.get(alert_type, alert_colors['info'])};
        border-left: 4px solid {border_colors.get(alert_type, border_colors['info'])};
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    ">
        {message}
    </div>
    """
    
    st.markdown(alert_html, unsafe_allow_html=True)

def load_sample_data() -> Dict[str, pd.DataFrame]:
    """Load sample data for demonstration (only when no real data is available)"""
    # This should only be used when explicitly requested or for demo purposes
    return {}

def check_data_freshness(data_timestamp: datetime, max_age_minutes: int = 30) -> bool:
    """Check if data is fresh within the specified age limit"""
    if not data_timestamp:
        return False
    
    age = datetime.now() - data_timestamp
    return age.total_seconds() / 60 <= max_age_minutes

def create_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Create a data quality report for a DataFrame"""
    if df.empty:
        return {"error": "Empty dataset"}
    
    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "duplicate_rows": df.duplicated().sum(),
        "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
        "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
        "date_columns": df.select_dtypes(include=['datetime']).columns.tolist()
    }
    
    # Calculate completeness percentage
    total_cells = len(df) * len(df.columns)
    missing_cells = df.isnull().sum().sum()
    report["completeness_percentage"] = ((total_cells - missing_cells) / total_cells) * 100
    
    return report

def handle_api_error(error: Exception, context: str = "API call") -> str:
    """Handle API errors with appropriate user messages"""
    error_messages = {
        "ConnectionError": "Unable to connect to Tally server. Please check if Tally Prime is running and the server URL is correct.",
        "TimeoutError": "Request timed out. The server may be busy or unresponsive.",
        "HTTPError": "Server returned an error. Please check your request parameters.",
        "ParseError": "Unable to parse server response. The data format may be invalid."
    }
    
    error_type = type(error).__name__
    default_message = f"An error occurred during {context}: {str(error)}"
    
    return error_messages.get(error_type, default_message)

def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    import hashlib
    
    # Create a string representation of all arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = "|".join(key_parts)
    
    # Return hash of the key string
    return hashlib.md5(key_string.encode()).hexdigest()

