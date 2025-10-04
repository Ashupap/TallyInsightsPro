import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

class AlertType(Enum):
    """Alert type enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"

class AlertPriority(Enum):
    """Alert priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    message: str
    alert_type: AlertType
    priority: AlertPriority
    timestamp: datetime
    source: str
    data: Optional[Dict] = None
    acknowledged: bool = False
    resolved: bool = False
    auto_resolve: bool = True
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'alert_type': self.alert_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved,
            'auto_resolve': self.auto_resolve
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Alert':
        """Create alert from dictionary"""
        return cls(
            id=data['id'],
            title=data['title'],
            message=data['message'],
            alert_type=AlertType(data['alert_type']),
            priority=AlertPriority(data['priority']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            data=data.get('data'),
            acknowledged=data.get('acknowledged', False),
            resolved=data.get('resolved', False),
            auto_resolve=data.get('auto_resolve', True)
        )

class AlertManager:
    """Manages business alerts and notifications"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict] = self._get_default_alert_rules()
        self._load_alerts()
    
    def _get_default_alert_rules(self) -> Dict[str, Dict]:
        """Get default alert rules"""
        return {
            'low_stock': {
                'enabled': True,
                'threshold': 10,
                'check_interval': 300,  # 5 minutes
                'alert_type': AlertType.WARNING,
                'priority': AlertPriority.MEDIUM
            },
            'zero_stock': {
                'enabled': True,
                'threshold': 0,
                'check_interval': 300,
                'alert_type': AlertType.ERROR,
                'priority': AlertPriority.HIGH
            },
            'high_receivables': {
                'enabled': True,
                'threshold': 100000,
                'check_interval': 3600,  # 1 hour
                'alert_type': AlertType.WARNING,
                'priority': AlertPriority.MEDIUM
            },
            'overdue_payments': {
                'enabled': True,
                'threshold_days': 30,
                'check_interval': 3600,
                'alert_type': AlertType.ERROR,
                'priority': AlertPriority.HIGH
            },
            'cash_flow_negative': {
                'enabled': True,
                'threshold': 0,
                'check_interval': 3600,
                'alert_type': AlertType.CRITICAL,
                'priority': AlertPriority.CRITICAL
            },
            'sales_drop': {
                'enabled': True,
                'threshold_percentage': 20,
                'comparison_days': 7,
                'check_interval': 3600,
                'alert_type': AlertType.WARNING,
                'priority': AlertPriority.MEDIUM
            }
        }
    
    def _load_alerts(self):
        """Load alerts from session state"""
        if 'alerts' in st.session_state:
            try:
                alert_data = st.session_state.alerts
                self.alerts = [Alert.from_dict(alert) for alert in alert_data]
            except Exception as e:
                st.error(f"Error loading alerts: {str(e)}")
                self.alerts = []
    
    def _save_alerts(self):
        """Save alerts to session state"""
        try:
            st.session_state.alerts = [alert.to_dict() for alert in self.alerts]
        except Exception as e:
            st.error(f"Error saving alerts: {str(e)}")
    
    def add_alert(self, title: str, message: str, alert_type: AlertType,
                  priority: AlertPriority, source: str, data: Optional[Dict] = None) -> str:
        """Add a new alert"""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts)}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            alert_type=alert_type,
            priority=priority,
            timestamp=datetime.now(),
            source=source,
            data=data
        )
        
        self.alerts.append(alert)
        self._save_alerts()
        return alert_id
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self._save_alerts()
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                self._save_alerts()
                return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alerts_by_priority(self, priority: AlertPriority) -> List[Alert]:
        """Get alerts by priority"""
        return [alert for alert in self.alerts if alert.priority == priority and not alert.resolved]
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Get alerts by type"""
        return [alert for alert in self.alerts if alert.alert_type == alert_type and not alert.resolved]
    
    def clear_resolved_alerts(self):
        """Clear all resolved alerts"""
        self.alerts = [alert for alert in self.alerts if not alert.resolved]
        self._save_alerts()
    
    def check_inventory_alerts(self, inventory_data: pd.DataFrame):
        """Check for inventory-related alerts"""
        if inventory_data.empty:
            return
        
        try:
            # Low stock alerts
            if self.alert_rules['low_stock']['enabled']:
                threshold = self.alert_rules['low_stock']['threshold']
                low_stock_items = inventory_data[
                    inventory_data['closing_balance'] <= threshold
                ]
                
                if not low_stock_items.empty:
                    for _, item in low_stock_items.iterrows():
                        # Check if alert already exists for this item
                        existing_alert = any(
                            alert.source == 'inventory' and 
                            alert.data and 
                            alert.data.get('item_name') == item['name'] and
                            not alert.resolved
                            for alert in self.alerts
                        )
                        
                        if not existing_alert:
                            self.add_alert(
                                title="Low Stock Alert",
                                message=f"Item '{item['name']}' has low stock: {item['closing_balance']} {item['base_unit']}",
                                alert_type=AlertType.WARNING,
                                priority=AlertPriority.MEDIUM,
                                source="inventory",
                                data={
                                    'item_name': item['name'],
                                    'current_stock': item['closing_balance'],
                                    'unit': item['base_unit'],
                                    'reorder_level': item.get('reorder_level', 0)
                                }
                            )
            
            # Zero stock alerts
            if self.alert_rules['zero_stock']['enabled']:
                zero_stock_items = inventory_data[
                    inventory_data['closing_balance'] <= 0
                ]
                
                if not zero_stock_items.empty:
                    for _, item in zero_stock_items.iterrows():
                        existing_alert = any(
                            alert.source == 'inventory' and 
                            alert.data and 
                            alert.data.get('item_name') == item['name'] and
                            'zero stock' in alert.title.lower() and
                            not alert.resolved
                            for alert in self.alerts
                        )
                        
                        if not existing_alert:
                            self.add_alert(
                                title="Zero Stock Critical",
                                message=f"Item '{item['name']}' is out of stock",
                                alert_type=AlertType.ERROR,
                                priority=AlertPriority.HIGH,
                                source="inventory",
                                data={
                                    'item_name': item['name'],
                                    'current_stock': item['closing_balance'],
                                    'unit': item['base_unit']
                                }
                            )
                            
        except Exception as e:
            st.error(f"Error checking inventory alerts: {str(e)}")
    
    def check_receivables_alerts(self, outstanding_data: pd.DataFrame):
        """Check for outstanding receivables alerts"""
        if outstanding_data.empty:
            return
        
        try:
            # High receivables alert
            if self.alert_rules['high_receivables']['enabled']:
                threshold = self.alert_rules['high_receivables']['threshold']
                high_receivables = outstanding_data[
                    outstanding_data['closing_balance'] > threshold
                ]
                
                if not high_receivables.empty:
                    total_high_receivables = high_receivables['closing_balance'].sum()
                    count_parties = len(high_receivables)
                    
                    existing_alert = any(
                        alert.source == 'receivables' and 
                        'high receivables' in alert.title.lower() and
                        not alert.resolved
                        for alert in self.alerts
                    )
                    
                    if not existing_alert:
                        self.add_alert(
                            title="High Receivables Alert",
                            message=f"High receivables detected: ₹{total_high_receivables:,.0f} from {count_parties} parties",
                            alert_type=AlertType.WARNING,
                            priority=AlertPriority.MEDIUM,
                            source="receivables",
                            data={
                                'total_amount': total_high_receivables,
                                'party_count': count_parties,
                                'threshold': threshold
                            }
                        )
                        
        except Exception as e:
            st.error(f"Error checking receivables alerts: {str(e)}")
    
    def check_sales_alerts(self, sales_data: pd.DataFrame):
        """Check for sales-related alerts"""
        if sales_data.empty:
            return
        
        try:
            # Sales drop alert
            if self.alert_rules['sales_drop']['enabled']:
                sales_data['date'] = pd.to_datetime(sales_data['date'])
                current_date = datetime.now()
                comparison_days = self.alert_rules['sales_drop']['comparison_days']
                threshold_pct = self.alert_rules['sales_drop']['threshold_percentage']
                
                # Calculate current period sales
                current_start = current_date - timedelta(days=comparison_days)
                current_sales = sales_data[
                    sales_data['date'] >= current_start
                ]['amount'].sum()
                
                # Calculate previous period sales
                previous_start = current_start - timedelta(days=comparison_days)
                previous_end = current_start
                previous_sales = sales_data[
                    (sales_data['date'] >= previous_start) & 
                    (sales_data['date'] < previous_end)
                ]['amount'].sum()
                
                if previous_sales > 0:
                    drop_percentage = ((previous_sales - current_sales) / previous_sales) * 100
                    
                    if drop_percentage >= threshold_pct:
                        existing_alert = any(
                            alert.source == 'sales' and 
                            'sales drop' in alert.title.lower() and
                            not alert.resolved
                            for alert in self.alerts
                        )
                        
                        if not existing_alert:
                            self.add_alert(
                                title="Sales Drop Alert",
                                message=f"Sales dropped by {drop_percentage:.1f}% compared to previous {comparison_days} days",
                                alert_type=AlertType.WARNING,
                                priority=AlertPriority.MEDIUM,
                                source="sales",
                                data={
                                    'drop_percentage': drop_percentage,
                                    'current_sales': current_sales,
                                    'previous_sales': previous_sales,
                                    'comparison_days': comparison_days
                                }
                            )
                            
        except Exception as e:
            st.error(f"Error checking sales alerts: {str(e)}")

def render_alerts_panel():
    """Render alerts panel in sidebar or main area"""
    alert_manager = AlertManager()
    
    # Load current alerts
    alert_manager._load_alerts()
    
    active_alerts = alert_manager.get_active_alerts()
    critical_alerts = [a for a in active_alerts if a.priority == AlertPriority.CRITICAL]
    high_alerts = [a for a in active_alerts if a.priority == AlertPriority.HIGH]
    
    if active_alerts:
        st.markdown("### 🔔 Active Alerts")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts", len(active_alerts))
        with col2:
            st.metric("Critical", len(critical_alerts))
        with col3:
            st.metric("High Priority", len(high_alerts))
        
        # Display alerts by priority
        for alert in sorted(active_alerts, key=lambda x: (x.priority.value, x.timestamp), reverse=True):
            with st.container():
                # Alert header with priority indicator
                priority_emoji = {
                    AlertPriority.CRITICAL: "🚨",
                    AlertPriority.HIGH: "⚠️",
                    AlertPriority.MEDIUM: "📢",
                    AlertPriority.LOW: "ℹ️"
                }
                
                type_color = {
                    AlertType.CRITICAL: "error",
                    AlertType.ERROR: "error", 
                    AlertType.WARNING: "warning",
                    AlertType.INFO: "info",
                    AlertType.SUCCESS: "success"
                }
                
                # Use appropriate Streamlit alert type
                alert_func = getattr(st, type_color.get(alert.alert_type, 'info'))
                
                with st.expander(f"{priority_emoji[alert.priority]} {alert.title}"):
                    st.write(alert.message)
                    st.caption(f"Source: {alert.source} | Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Alert actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Acknowledge", key=f"ack_{alert.id}"):
                            alert_manager.acknowledge_alert(alert.id)
                            st.success("Alert acknowledged")
                            st.rerun()
                    
                    with col2:
                        if st.button("Resolve", key=f"resolve_{alert.id}"):
                            alert_manager.resolve_alert(alert.id)
                            st.success("Alert resolved")
                            st.rerun()
                    
                    # Show additional data if available
                    if alert.data:
                        with st.expander("Details"):
                            st.json(alert.data)
    else:
        st.success("✅ No active alerts")

def render_alert_settings():
    """Render alert configuration settings"""
    st.markdown("### ⚙️ Alert Settings")
    
    alert_manager = AlertManager()
    
    st.markdown("#### Alert Rules Configuration")
    
    for rule_name, rule_config in alert_manager.alert_rules.items():
        with st.expander(f"{rule_name.replace('_', ' ').title()} Alert"):
            col1, col2 = st.columns(2)
            
            with col1:
                enabled = st.checkbox(
                    "Enabled", 
                    value=rule_config['enabled'],
                    key=f"enabled_{rule_name}"
                )
                
                alert_type = st.selectbox(
                    "Alert Type",
                    [t.value for t in AlertType],
                    index=[t.value for t in AlertType].index(rule_config['alert_type'].value),
                    key=f"type_{rule_name}"
                )
                
                priority = st.selectbox(
                    "Priority",
                    [p.value for p in AlertPriority], 
                    index=[p.value for p in AlertPriority].index(rule_config['priority'].value),
                    key=f"priority_{rule_name}"
                )
            
            with col2:
                check_interval = st.number_input(
                    "Check Interval (seconds)",
                    min_value=60,
                    value=rule_config['check_interval'],
                    key=f"interval_{rule_name}"
                )
                
                # Rule-specific settings
                if 'threshold' in rule_config:
                    threshold = st.number_input(
                        "Threshold",
                        min_value=0.0,
                        value=float(rule_config['threshold']),
                        key=f"threshold_{rule_name}"
                    )
                
                if 'threshold_percentage' in rule_config:
                    threshold_pct = st.number_input(
                        "Threshold Percentage",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(rule_config['threshold_percentage']),
                        key=f"threshold_pct_{rule_name}"
                    )
                
                if 'threshold_days' in rule_config:
                    threshold_days = st.number_input(
                        "Threshold Days",
                        min_value=1,
                        value=rule_config['threshold_days'],
                        key=f"threshold_days_{rule_name}"
                    )
    
    # Save configuration
    if st.button("Save Alert Settings"):
        # Update alert rules based on form inputs
        for rule_name in alert_manager.alert_rules.keys():
            alert_manager.alert_rules[rule_name]['enabled'] = st.session_state.get(f"enabled_{rule_name}")
            alert_manager.alert_rules[rule_name]['alert_type'] = AlertType(st.session_state.get(f"type_{rule_name}"))
            alert_manager.alert_rules[rule_name]['priority'] = AlertPriority(st.session_state.get(f"priority_{rule_name}"))
            alert_manager.alert_rules[rule_name]['check_interval'] = st.session_state.get(f"interval_{rule_name}")
            
            if f"threshold_{rule_name}" in st.session_state:
                alert_manager.alert_rules[rule_name]['threshold'] = st.session_state.get(f"threshold_{rule_name}")
            
            if f"threshold_pct_{rule_name}" in st.session_state:
                alert_manager.alert_rules[rule_name]['threshold_percentage'] = st.session_state.get(f"threshold_pct_{rule_name}")
            
            if f"threshold_days_{rule_name}" in st.session_state:
                alert_manager.alert_rules[rule_name]['threshold_days'] = st.session_state.get(f"threshold_days_{rule_name}")
        
        st.success("Alert settings saved!")
    
    # Clear resolved alerts
    if st.button("Clear Resolved Alerts"):
        alert_manager.clear_resolved_alerts()
        st.success("Resolved alerts cleared!")
        st.rerun()

def check_business_alerts(sales_data: pd.DataFrame = None, 
                         inventory_data: pd.DataFrame = None,
                         outstanding_data: pd.DataFrame = None):
    """Check all business alerts based on current data"""
    alert_manager = AlertManager()
    
    try:
        if inventory_data is not None and not inventory_data.empty:
            alert_manager.check_inventory_alerts(inventory_data)
        
        if outstanding_data is not None and not outstanding_data.empty:
            alert_manager.check_receivables_alerts(outstanding_data)
        
        if sales_data is not None and not sales_data.empty:
            alert_manager.check_sales_alerts(sales_data)
            
    except Exception as e:
        st.error(f"Error checking business alerts: {str(e)}")

