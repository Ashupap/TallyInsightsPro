import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
import json

class TallyAPIClient:
    """Client for connecting to Tally Prime XML API"""
    
    def __init__(self, server_url: str = "http://localhost:9000"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def test_connection(self) -> bool:
        """Test connection to Tally server"""
        try:
            response = self._send_xml_request("<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>PING</TALLYREQUEST></HEADER></ENVELOPE>")
            return response is not None
        except Exception as e:
            st.error(f"Connection test failed: {str(e)}")
            return False
    
    def _send_xml_request(self, xml_data: str) -> Optional[ET.Element]:
        """Send XML request to Tally server"""
        try:
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'Content-Length': str(len(xml_data))
            }
            
            response = self.session.post(
                self.server_url,
                data=xml_data,
                headers=headers
            )
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            return root
            
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")
            return None
        except ET.ParseError as e:
            st.error(f"XML parsing failed: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def get_company_list(self) -> List[Dict[str, str]]:
        """Get list of companies from Tally"""
        xml_request = """
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>Companies</ID>
            </HEADER>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        companies = []
        
        if response is not None:
            try:
                for company in response.findall('.//COMPANY'):
                    name = company.find('NAME')
                    if name is not None:
                        companies.append({
                            'name': name.text,
                            'guid': company.get('GUID', ''),
                        })
            except Exception as e:
                st.error(f"Error parsing company list: {str(e)}")
        
        return companies
    
    def get_sales_data(self, from_date: str, to_date: str, company: str = None) -> pd.DataFrame:
        """Fetch sales data from Tally"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>Sales Vouchers</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVFROMDATE>{from_date}</SVFROMDATE>
                        <SVTODATE>{to_date}</SVTODATE>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </DESC>
            </BODY>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        sales_data = []
        
        if response is not None:
            try:
                for voucher in response.findall('.//VOUCHER'):
                    voucher_data = {
                        'date': self._get_element_text(voucher, 'DATE'),
                        'voucher_number': self._get_element_text(voucher, 'VOUCHERNUMBER'),
                        'party_name': self._get_element_text(voucher, 'PARTYLEDGERNAME'),
                        'amount': self._parse_amount(self._get_element_text(voucher, 'AMOUNT')),
                        'voucher_type': self._get_element_text(voucher, 'VOUCHERTYPE')
                    }
                    sales_data.append(voucher_data)
            except Exception as e:
                st.error(f"Error parsing sales data: {str(e)}")
        
        return pd.DataFrame(sales_data)
    
    def get_purchase_data(self, from_date: str, to_date: str, company: str = None) -> pd.DataFrame:
        """Fetch purchase data from Tally"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>Purchase Vouchers</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVFROMDATE>{from_date}</SVFROMDATE>
                        <SVTODATE>{to_date}</SVTODATE>
                    </STATICVARIABLES>
                </DESC>
            </BODY>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        purchase_data = []
        
        if response is not None:
            try:
                for voucher in response.findall('.//VOUCHER'):
                    voucher_data = {
                        'date': self._get_element_text(voucher, 'DATE'),
                        'voucher_number': self._get_element_text(voucher, 'VOUCHERNUMBER'),
                        'party_name': self._get_element_text(voucher, 'PARTYLEDGERNAME'),
                        'amount': self._parse_amount(self._get_element_text(voucher, 'AMOUNT')),
                        'voucher_type': self._get_element_text(voucher, 'VOUCHERTYPE')
                    }
                    purchase_data.append(voucher_data)
            except Exception as e:
                st.error(f"Error parsing purchase data: {str(e)}")
        
        return pd.DataFrame(purchase_data)
    
    def get_inventory_data(self, company: str = None) -> pd.DataFrame:
        """Fetch inventory/stock data from Tally"""
        xml_request = """
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>Stock Items</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </DESC>
            </BODY>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        inventory_data = []
        
        if response is not None:
            try:
                for item in response.findall('.//STOCKITEM'):
                    item_data = {
                        'name': self._get_element_text(item, 'NAME'),
                        'closing_balance': self._parse_quantity(self._get_element_text(item, 'CLOSINGBALANCE')),
                        'closing_value': self._parse_amount(self._get_element_text(item, 'CLOSINGVALUE')),
                        'base_unit': self._get_element_text(item, 'BASEUNITS'),
                        'category': self._get_element_text(item, 'CATEGORY'),
                        'reorder_level': self._parse_quantity(self._get_element_text(item, 'REORDERBASE'))
                    }
                    inventory_data.append(item_data)
            except Exception as e:
                st.error(f"Error parsing inventory data: {str(e)}")
        
        return pd.DataFrame(inventory_data)
    
    def get_outstanding_data(self, company: str = None) -> pd.DataFrame:
        """Fetch outstanding receivables and payables"""
        xml_request = """
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>Outstanding</ID>
            </HEADER>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        outstanding_data = []
        
        if response is not None:
            try:
                for item in response.findall('.//LEDGER'):
                    item_data = {
                        'party_name': self._get_element_text(item, 'NAME'),
                        'opening_balance': self._parse_amount(self._get_element_text(item, 'OPENINGBALANCE')),
                        'closing_balance': self._parse_amount(self._get_element_text(item, 'CLOSINGBALANCE')),
                        'bill_wise_details': []
                    }
                    
                    # Get bill-wise details if available
                    for bill in item.findall('.//BILLALLOCATIONS'):
                        bill_data = {
                            'bill_date': self._get_element_text(bill, 'DATE'),
                            'amount': self._parse_amount(self._get_element_text(bill, 'AMOUNT')),
                            'bill_name': self._get_element_text(bill, 'NAME')
                        }
                        item_data['bill_wise_details'].append(bill_data)
                    
                    outstanding_data.append(item_data)
            except Exception as e:
                st.error(f"Error parsing outstanding data: {str(e)}")
        
        return pd.DataFrame(outstanding_data)
    
    def get_balance_sheet_data(self, date: str, company: str = None) -> Dict[str, Any]:
        """Fetch balance sheet data"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Report</TYPE>
                <ID>Balance Sheet</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVFROMDATE>01-Apr-{datetime.strptime(date, '%Y-%m-%d').year}</SVFROMDATE>
                        <SVTODATE>{date}</SVTODATE>
                    </STATICVARIABLES>
                </DESC>
            </BODY>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        balance_sheet = {
            'assets': {'current': 0, 'fixed': 0, 'total': 0},
            'liabilities': {'current': 0, 'long_term': 0, 'total': 0},
            'equity': 0
        }
        
        if response is not None:
            try:
                # Parse balance sheet structure
                # This is a simplified parsing - actual implementation would need
                # to handle Tally's complex balance sheet structure
                for group in response.findall('.//GROUP'):
                    group_name = self._get_element_text(group, 'NAME')
                    amount = self._parse_amount(self._get_element_text(group, 'CLOSINGBALANCE'))
                    
                    # Categorize based on group names (simplified)
                    if 'current assets' in group_name.lower():
                        balance_sheet['assets']['current'] += amount
                    elif 'fixed assets' in group_name.lower():
                        balance_sheet['assets']['fixed'] += amount
                    elif 'current liabilities' in group_name.lower():
                        balance_sheet['liabilities']['current'] += amount
                    elif 'loan' in group_name.lower() or 'long term' in group_name.lower():
                        balance_sheet['liabilities']['long_term'] += amount
                    elif 'capital' in group_name.lower() or 'equity' in group_name.lower():
                        balance_sheet['equity'] += amount
                
                balance_sheet['assets']['total'] = balance_sheet['assets']['current'] + balance_sheet['assets']['fixed']
                balance_sheet['liabilities']['total'] = balance_sheet['liabilities']['current'] + balance_sheet['liabilities']['long_term']
                
            except Exception as e:
                st.error(f"Error parsing balance sheet: {str(e)}")
        
        return balance_sheet
    
    def get_profit_loss_data(self, from_date: str, to_date: str, company: str = None) -> Dict[str, Any]:
        """Fetch profit and loss data"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Report</TYPE>
                <ID>Profit Loss</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVFROMDATE>{from_date}</SVFROMDATE>
                        <SVTODATE>{to_date}</SVTODATE>
                    </STATICVARIABLES>
                </DESC>
            </BODY>
        </ENVELOPE>
        """
        
        response = self._send_xml_request(xml_request)
        profit_loss = {
            'revenue': 0,
            'cost_of_goods_sold': 0,
            'gross_profit': 0,
            'expenses': 0,
            'net_profit': 0,
            'detailed_breakdown': {}
        }
        
        if response is not None:
            try:
                for group in response.findall('.//GROUP'):
                    group_name = self._get_element_text(group, 'NAME')
                    amount = self._parse_amount(self._get_element_text(group, 'CLOSINGBALANCE'))
                    
                    # Categorize P&L items
                    if 'sales' in group_name.lower() or 'income' in group_name.lower():
                        profit_loss['revenue'] += amount
                    elif 'purchase' in group_name.lower() or 'cost' in group_name.lower():
                        profit_loss['cost_of_goods_sold'] += amount
                    elif 'expense' in group_name.lower():
                        profit_loss['expenses'] += amount
                    
                    profit_loss['detailed_breakdown'][group_name] = amount
                
                profit_loss['gross_profit'] = profit_loss['revenue'] - profit_loss['cost_of_goods_sold']
                profit_loss['net_profit'] = profit_loss['gross_profit'] - profit_loss['expenses']
                
            except Exception as e:
                st.error(f"Error parsing P&L data: {str(e)}")
        
        return profit_loss
    
    def _get_element_text(self, element: ET.Element, tag: str) -> str:
        """Safely get text from XML element"""
        if element is None:
            return ""
        
        child = element.find(tag)
        return child.text if child is not None and child.text is not None else ""
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        
        try:
            # Remove currency symbols and commas
            cleaned = amount_str.replace('₹', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_quantity(self, qty_str: str) -> float:
        """Parse quantity string to float"""
        if not qty_str:
            return 0.0
        
        try:
            # Extract numeric part from quantity strings like "100 Nos"
            import re
            numbers = re.findall(r'-?\d+\.?\d*', qty_str)
            return float(numbers[0]) if numbers else 0.0
        except (ValueError, TypeError, IndexError):
            return 0.0

# Cached data fetching functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_cached_sales_data(server_url: str, from_date: str, to_date: str):
    """Cached version of sales data fetching"""
    client = TallyAPIClient(server_url)
    return client.get_sales_data(from_date, to_date)

@st.cache_data(ttl=300)
def fetch_cached_purchase_data(server_url: str, from_date: str, to_date: str):
    """Cached version of purchase data fetching"""
    client = TallyAPIClient(server_url)
    return client.get_purchase_data(from_date, to_date)

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_cached_inventory_data(server_url: str):
    """Cached version of inventory data fetching"""
    client = TallyAPIClient(server_url)
    return client.get_inventory_data()
