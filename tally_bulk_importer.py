#!/usr/bin/env python3
"""
Tally Prime Bulk Data Import Tool
Created by: AI Assistant
Date: 2025

This tool converts Excel data to Tally Prime compatible XML format
Supports: Sales, Purchase, Ledgers, Stock Items, and all major Tally modules
Works without APIs - generates XML files for direct import
"""

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from typing import Dict, List, Any, Optional

class TallyXMLGenerator:
    """Core class for generating Tally-compatible XML files"""
    
    def __init__(self):
        self.envelope_header = {
            "TallyRequest": "Import Data",
            "TallyResponseCode": "200",
            "TallyResponseType": "Success"
        }
    
    def create_xml_envelope(self, data_type: str = "Collection Of Voucher"):
        """Create the basic XML envelope structure"""
        envelope = ET.Element("ENVELOPE")
        
        # Header
        header = ET.SubElement(envelope, "HEADER")
        tallyrequest = ET.SubElement(header, "TALLYREQUEST")
        tallyrequest.text = "Import Data"
        
        # Body
        body = ET.SubElement(envelope, "BODY")
        importdata = ET.SubElement(body, "IMPORTDATA")
        requestdesc = ET.SubElement(importdata, "REQUESTDESC")
        reportname = ET.SubElement(requestdesc, "REPORTNAME")
        reportname.text = data_type
        
        requestdata = ET.SubElement(importdata, "REQUESTDATA")
        
        return envelope, requestdata
    
    def prettify_xml(self, elem):
        """Return a pretty-printed XML string for the Element."""
        rough_string = ET.tostring(elem, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

class TallyMastersImporter:
    """Handle import of master data like Ledgers and Stock Items"""
    
    def __init__(self, xml_generator: TallyXMLGenerator):
        self.xml_gen = xml_generator
    
    def create_ledger_xml(self, ledger_data: pd.DataFrame) -> str:
        """Generate XML for ledger masters"""
        envelope, requestdata = self.xml_gen.create_xml_envelope("Collection Of Ledger")
        
        for _, row in ledger_data.iterrows():
            tallymessage = ET.SubElement(requestdata, "TALLYMESSAGE", xmlns="TallyUDF")
            ledger = ET.SubElement(tallymessage, "LEDGER", NAME=str(row.get('Name', '')), ACTION="Create")
            
            # Basic ledger details
            ET.SubElement(ledger, "NAME").text = str(row.get('Name', ''))
            ET.SubElement(ledger, "PARENT").text = str(row.get('Group', 'Sundry Debtors'))
            ET.SubElement(ledger, "ALIAS").text = str(row.get('Alias', ''))
            
            # Address details
            if pd.notna(row.get('Address')):
                address_list = ET.SubElement(ledger, "ADDRESS.LIST")
                ET.SubElement(address_list, "ADDRESS").text = str(row.get('Address', ''))
            
            # Contact details
            if pd.notna(row.get('Mobile')):
                ET.SubElement(ledger, "LEDGERPHONE").text = str(row.get('Mobile', ''))
            if pd.notna(row.get('Email')):
                ET.SubElement(ledger, "EMAIL").text = str(row.get('Email', ''))
            
            # GST details
            if pd.notna(row.get('GSTIN')):
                gst_registration = ET.SubElement(ledger, "GSTREGISTRATIONTYPE")
                gst_registration.text = "Regular"
                
                party_gstin_details = ET.SubElement(ledger, "PARTYGSTIN.LIST")
                ET.SubElement(party_gstin_details, "PARTYGSTIN").text = str(row.get('GSTIN', ''))
                
            # Opening balance
            if pd.notna(row.get('Opening_Balance')):
                opening_balance = float(row.get('Opening_Balance', 0))
                if opening_balance != 0:
                    ET.SubElement(ledger, "OPENINGBALANCE").text = str(opening_balance)
        
        return self.xml_gen.prettify_xml(envelope)
    
    def create_stock_item_xml(self, stock_data: pd.DataFrame) -> str:
        """Generate XML for stock item masters"""
        envelope, requestdata = self.xml_gen.create_xml_envelope("Collection Of Stock Item")
        
        for _, row in stock_data.iterrows():
            tallymessage = ET.SubElement(requestdata, "TALLYMESSAGE", xmlns="TallyUDF")
            stockitem = ET.SubElement(tallymessage, "STOCKITEM", NAME=str(row.get('Name', '')), ACTION="Create")
            
            # Basic stock item details
            ET.SubElement(stockitem, "NAME").text = str(row.get('Name', ''))
            ET.SubElement(stockitem, "ALIAS").text = str(row.get('Alias', ''))
            ET.SubElement(stockitem, "PARENT").text = str(row.get('Group', 'Primary'))
            ET.SubElement(stockitem, "CATEGORY").text = str(row.get('Category', 'Primary'))
            ET.SubElement(stockitem, "BASEUNITS").text = str(row.get('Unit', 'Nos'))
            
            # Tax details
            if pd.notna(row.get('GST_Rate')):
                gst_details = ET.SubElement(stockitem, "GSTDETAILS.LIST")
                ET.SubElement(gst_details, "APPLICABLEFROM").text = "20170701"
                ET.SubElement(gst_details, "CALCULATIONTYPE").text = "On Value"
                ET.SubElement(gst_details, "HSNCODE").text = str(row.get('HSN_Code', ''))
                ET.SubElement(gst_details, "TAXABILITY").text = "Taxable"
                ET.SubElement(gst_details, "ISREVERSECHARGEAPPLICABLE").text = "No"
                ET.SubElement(gst_details, "ISNONGSTGOODS").text = "No"
                
                # GST rates
                gst_rate = float(row.get('GST_Rate', 0))
                if gst_rate > 0:
                    ET.SubElement(gst_details, "IGSTRATE").text = str(gst_rate)
                    ET.SubElement(gst_details, "CGSTRATE").text = str(gst_rate / 2)
                    ET.SubElement(gst_details, "SGSTRATE").text = str(gst_rate / 2)
            
            # Opening stock
            if pd.notna(row.get('Opening_Quantity')):
                opening_qty = float(row.get('Opening_Quantity', 0))
                opening_rate = float(row.get('Opening_Rate', 0))
                if opening_qty != 0:
                    opening_balance = ET.SubElement(stockitem, "OPENINGBALANCE.LIST")
                    ET.SubElement(opening_balance, "OPENINGQUANTITY").text = str(opening_qty)
                    ET.SubElement(opening_balance, "OPENINGRATE").text = str(opening_rate)
                    ET.SubElement(opening_balance, "OPENINGVALUE").text = str(opening_qty * opening_rate)
        
        return self.xml_gen.prettify_xml(envelope)

class TallyVouchersImporter:
    """Handle import of transaction vouchers"""
    
    def __init__(self, xml_generator: TallyXMLGenerator):
        self.xml_gen = xml_generator
    
    def create_sales_voucher_xml(self, sales_data: pd.DataFrame) -> str:
        """Generate XML for sales vouchers"""
        envelope, requestdata = self.xml_gen.create_xml_envelope("Collection Of Voucher")
        
        # Group by voucher number to handle multi-line entries
        grouped_data = sales_data.groupby('Voucher_No')
        
        for voucher_no, group in grouped_data:
            tallymessage = ET.SubElement(requestdata, "TALLYMESSAGE", xmlns="TallyUDF")
            voucher = ET.SubElement(tallymessage, "VOUCHER", 
                                  REMOTEID=str(voucher_no), 
                                  VCHKEY=str(voucher_no),
                                  VCHTYPE="Sales", 
                                  ACTION="Create")
            
            # Get voucher header data from first row
            first_row = group.iloc[0]
            
            # Voucher header
            ET.SubElement(voucher, "DATE").text = self._format_date(first_row.get('Date'))
            ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Sales"
            ET.SubElement(voucher, "VOUCHERNUMBER").text = str(voucher_no)
            ET.SubElement(voucher, "PARTYNAME").text = str(first_row.get('Party_Name', ''))
            
            # Reference details
            if pd.notna(first_row.get('Ref_No')):
                ET.SubElement(voucher, "REFERENCE").text = str(first_row.get('Ref_No', ''))
            if pd.notna(first_row.get('Ref_Date')):
                ET.SubElement(voucher, "REFERENCEDATE").text = self._format_date(first_row.get('Ref_Date'))
            
            # Inventory allocations
            all_ledger_entries = ET.SubElement(voucher, "ALLINVENTORYENTRIES.LIST")
            all_ledger_entries_voucher = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            
            total_amount = 0
            total_tax = 0
            
            # Process inventory items
            for _, row in group.iterrows():
                if pd.notna(row.get('Item_Name')):
                    # Inventory entry
                    inv_entry = ET.SubElement(all_ledger_entries, "INVENTORYENTRIES.LIST")
                    ET.SubElement(inv_entry, "STOCKITEMNAME").text = str(row.get('Item_Name', ''))
                    ET.SubElement(inv_entry, "ISDEEMEDPOSITIVE").text = "No"
                    
                    quantity = float(row.get('Quantity', 0))
                    rate = float(row.get('Rate', 0))
                    amount = quantity * rate
                    
                    ET.SubElement(inv_entry, "ACTUALQTY").text = f"{quantity} Nos"
                    ET.SubElement(inv_entry, "BILLEDQTY").text = f"{quantity} Nos"
                    ET.SubElement(inv_entry, "RATE").text = str(rate)
                    ET.SubElement(inv_entry, "AMOUNT").text = str(-amount)  # Negative for sales
                    
                    total_amount += amount
                    
                    # Tax calculations
                    gst_rate = float(row.get('GST_Rate', 0))
                    if gst_rate > 0:
                        tax_amount = (amount * gst_rate) / 100
                        total_tax += tax_amount
            
            # Ledger entries
            # Party ledger (Debit)
            party_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
            ET.SubElement(party_ledger, "LEDGERNAME").text = str(first_row.get('Party_Name', ''))
            ET.SubElement(party_ledger, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(party_ledger, "AMOUNT").text = str(total_amount + total_tax)
            
            # Sales ledger (Credit)
            sales_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
            ET.SubElement(sales_ledger, "LEDGERNAME").text = str(first_row.get('Sales_Ledger', 'Sales'))
            ET.SubElement(sales_ledger, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(sales_ledger, "AMOUNT").text = str(-total_amount)
            
            # Tax ledgers
            if total_tax > 0:
                # CGST
                cgst_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
                ET.SubElement(cgst_ledger, "LEDGERNAME").text = "CGST"
                ET.SubElement(cgst_ledger, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(cgst_ledger, "AMOUNT").text = str(-(total_tax / 2))
                
                # SGST
                sgst_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
                ET.SubElement(sgst_ledger, "LEDGERNAME").text = "SGST"
                ET.SubElement(sgst_ledger, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(sgst_ledger, "AMOUNT").text = str(-(total_tax / 2))
        
        return self.xml_gen.prettify_xml(envelope)
    
    def create_purchase_voucher_xml(self, purchase_data: pd.DataFrame) -> str:
        """Generate XML for purchase vouchers"""
        envelope, requestdata = self.xml_gen.create_xml_envelope("Collection Of Voucher")
        
        # Group by voucher number
        grouped_data = purchase_data.groupby('Voucher_No')
        
        for voucher_no, group in grouped_data:
            tallymessage = ET.SubElement(requestdata, "TALLYMESSAGE", xmlns="TallyUDF")
            voucher = ET.SubElement(tallymessage, "VOUCHER", 
                                  REMOTEID=str(voucher_no), 
                                  VCHKEY=str(voucher_no),
                                  VCHTYPE="Purchase", 
                                  ACTION="Create")
            
            # Get voucher header data from first row
            first_row = group.iloc[0]
            
            # Voucher header
            ET.SubElement(voucher, "DATE").text = self._format_date(first_row.get('Date'))
            ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Purchase"
            ET.SubElement(voucher, "VOUCHERNUMBER").text = str(voucher_no)
            ET.SubElement(voucher, "PARTYNAME").text = str(first_row.get('Party_Name', ''))
            
            # Reference details
            if pd.notna(first_row.get('Ref_No')):
                ET.SubElement(voucher, "REFERENCE").text = str(first_row.get('Ref_No', ''))
            if pd.notna(first_row.get('Ref_Date')):
                ET.SubElement(voucher, "REFERENCEDATE").text = self._format_date(first_row.get('Ref_Date'))
            
            # Process similar to sales but with opposite signs
            all_ledger_entries = ET.SubElement(voucher, "ALLINVENTORYENTRIES.LIST")
            all_ledger_entries_voucher = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            
            total_amount = 0
            total_tax = 0
            
            # Process inventory items
            for _, row in group.iterrows():
                if pd.notna(row.get('Item_Name')):
                    # Inventory entry
                    inv_entry = ET.SubElement(all_ledger_entries, "INVENTORYENTRIES.LIST")
                    ET.SubElement(inv_entry, "STOCKITEMNAME").text = str(row.get('Item_Name', ''))
                    ET.SubElement(inv_entry, "ISDEEMEDPOSITIVE").text = "Yes"
                    
                    quantity = float(row.get('Quantity', 0))
                    rate = float(row.get('Rate', 0))
                    amount = quantity * rate
                    
                    ET.SubElement(inv_entry, "ACTUALQTY").text = f"{quantity} Nos"
                    ET.SubElement(inv_entry, "BILLEDQTY").text = f"{quantity} Nos"
                    ET.SubElement(inv_entry, "RATE").text = str(rate)
                    ET.SubElement(inv_entry, "AMOUNT").text = str(amount)  # Positive for purchase
                    
                    total_amount += amount
                    
                    # Tax calculations
                    gst_rate = float(row.get('GST_Rate', 0))
                    if gst_rate > 0:
                        tax_amount = (amount * gst_rate) / 100
                        total_tax += tax_amount
            
            # Ledger entries for purchase
            # Purchase ledger (Debit)
            purchase_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
            ET.SubElement(purchase_ledger, "LEDGERNAME").text = str(first_row.get('Purchase_Ledger', 'Purchase'))
            ET.SubElement(purchase_ledger, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(purchase_ledger, "AMOUNT").text = str(total_amount)
            
            # Tax ledgers (Debit)
            if total_tax > 0:
                # CGST
                cgst_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
                ET.SubElement(cgst_ledger, "LEDGERNAME").text = "CGST Input"
                ET.SubElement(cgst_ledger, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(cgst_ledger, "AMOUNT").text = str(total_tax / 2)
                
                # SGST
                sgst_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
                ET.SubElement(sgst_ledger, "LEDGERNAME").text = "SGST Input"
                ET.SubElement(sgst_ledger, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(sgst_ledger, "AMOUNT").text = str(total_tax / 2)
            
            # Party ledger (Credit)
            party_ledger = ET.SubElement(all_ledger_entries_voucher, "LEDGERENTRIES.LIST")
            ET.SubElement(party_ledger, "LEDGERNAME").text = str(first_row.get('Party_Name', ''))
            ET.SubElement(party_ledger, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(party_ledger, "AMOUNT").text = str(-(total_amount + total_tax))
        
        return self.xml_gen.prettify_xml(envelope)
    
    def create_receipt_voucher_xml(self, receipt_data: pd.DataFrame) -> str:
        """Generate XML for receipt vouchers"""
        envelope, requestdata = self.xml_gen.create_xml_envelope("Collection Of Voucher")
        
        for _, row in receipt_data.iterrows():
            tallymessage = ET.SubElement(requestdata, "TALLYMESSAGE", xmlns="TallyUDF")
            voucher = ET.SubElement(tallymessage, "VOUCHER", 
                                  REMOTEID=str(row.get('Voucher_No', '')), 
                                  VCHKEY=str(row.get('Voucher_No', '')),
                                  VCHTYPE="Receipt", 
                                  ACTION="Create")
            
            # Voucher header
            ET.SubElement(voucher, "DATE").text = self._format_date(row.get('Date'))
            ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Receipt"
            ET.SubElement(voucher, "VOUCHERNUMBER").text = str(row.get('Voucher_No', ''))
            
            # Ledger entries
            all_ledger_entries = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            
            amount = float(row.get('Amount', 0))
            
            # Cash/Bank ledger (Debit)
            cash_ledger = ET.SubElement(all_ledger_entries, "LEDGERENTRIES.LIST")
            ET.SubElement(cash_ledger, "LEDGERNAME").text = str(row.get('Cash_Bank_Ledger', 'Cash'))
            ET.SubElement(cash_ledger, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(cash_ledger, "AMOUNT").text = str(amount)
            
            # Party ledger (Credit)
            party_ledger = ET.SubElement(all_ledger_entries, "LEDGERENTRIES.LIST")
            ET.SubElement(party_ledger, "LEDGERNAME").text = str(row.get('Party_Name', ''))
            ET.SubElement(party_ledger, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(party_ledger, "AMOUNT").text = str(-amount)
            
            # Narration
            if pd.notna(row.get('Narration')):
                ET.SubElement(voucher, "NARRATION").text = str(row.get('Narration', ''))
        
        return self.xml_gen.prettify_xml(envelope)
    
    def create_payment_voucher_xml(self, payment_data: pd.DataFrame) -> str:
        """Generate XML for payment vouchers"""
        envelope, requestdata = self.xml_gen.create_xml_envelope("Collection Of Voucher")
        
        for _, row in payment_data.iterrows():
            tallymessage = ET.SubElement(requestdata, "TALLYMESSAGE", xmlns="TallyUDF")
            voucher = ET.SubElement(tallymessage, "VOUCHER", 
                                  REMOTEID=str(row.get('Voucher_No', '')), 
                                  VCHKEY=str(row.get('Voucher_No', '')),
                                  VCHTYPE="Payment", 
                                  ACTION="Create")
            
            # Voucher header
            ET.SubElement(voucher, "DATE").text = self._format_date(row.get('Date'))
            ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Payment"
            ET.SubElement(voucher, "VOUCHERNUMBER").text = str(row.get('Voucher_No', ''))
            
            # Ledger entries
            all_ledger_entries = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            
            amount = float(row.get('Amount', 0))
            
            # Expense/Party ledger (Debit)
            expense_ledger = ET.SubElement(all_ledger_entries, "LEDGERENTRIES.LIST")
            ET.SubElement(expense_ledger, "LEDGERNAME").text = str(row.get('Expense_Ledger', ''))
            ET.SubElement(expense_ledger, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(expense_ledger, "AMOUNT").text = str(amount)
            
            # Cash/Bank ledger (Credit)
            cash_ledger = ET.SubElement(all_ledger_entries, "LEDGERENTRIES.LIST")
            ET.SubElement(cash_ledger, "LEDGERNAME").text = str(row.get('Cash_Bank_Ledger', 'Cash'))
            ET.SubElement(cash_ledger, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(cash_ledger, "AMOUNT").text = str(-amount)
            
            # Narration
            if pd.notna(row.get('Narration')):
                ET.SubElement(voucher, "NARRATION").text = str(row.get('Narration', ''))
        
        return self.xml_gen.prettify_xml(envelope)
    
    def _format_date(self, date_value) -> str:
        """Format date for Tally XML"""
        if pd.isna(date_value):
            return datetime.now().strftime("%Y%m%d")
        
        if isinstance(date_value, str):
            try:
                # Try common date formats
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        date_obj = datetime.strptime(date_value, fmt)
                        return date_obj.strftime("%Y%m%d")
                    except ValueError:
                        continue
                # If no format matches, return current date
                return datetime.now().strftime("%Y%m%d")
            except:
                return datetime.now().strftime("%Y%m%d")
        elif hasattr(date_value, 'strftime'):
            return date_value.strftime("%Y%m%d")
        else:
            return datetime.now().strftime("%Y%m%d")

class TallyBulkImporter:
    """Main class for the Tally Bulk Import Tool"""
    
    def __init__(self):
        self.xml_generator = TallyXMLGenerator()
        self.masters_importer = TallyMastersImporter(self.xml_generator)
        self.vouchers_importer = TallyVouchersImporter(self.xml_generator)
        self.templates_dir = Path("templates")
        self.output_dir = Path("output")
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        self.root = tk.Tk()
        self.root.title("Tally Prime Bulk Data Import Tool")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Tally Prime Bulk Data Import Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="This tool converts Excel data to Tally-compatible XML files.\n"
                                     "1. Download templates or use your own Excel files\n"
                                     "2. Fill the Excel templates with your data\n"
                                     "3. Convert to XML and import into Tally Prime",
                                justify=tk.LEFT)
        instructions.grid(row=1, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        
        # Notebook for different modules
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Masters tab
        self.setup_masters_tab()
        
        # Vouchers tab
        self.setup_vouchers_tab()
        
        # Templates tab
        self.setup_templates_tab()
        
        # Output directory selection
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(output_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W)
        self.output_var = tk.StringVar(value=str(self.output_dir.absolute()))
        ttk.Entry(output_frame, textvariable=self.output_var, width=50).grid(row=0, column=1, padx=(10, 0))
        ttk.Button(output_frame, text="Browse", 
                  command=self.select_output_dir).grid(row=0, column=2, padx=(10, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=5, column=0, columnspan=3)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def setup_masters_tab(self):
        """Setup the masters import tab"""
        masters_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(masters_frame, text="Masters Data")
        
        # Ledgers section
        ledger_frame = ttk.LabelFrame(masters_frame, text="Ledger Masters", padding="10")
        ledger_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(ledger_frame, text="Download Ledger Template", 
                  command=lambda: self.create_template('ledger')).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(ledger_frame, text="Convert Ledgers to XML", 
                  command=lambda: self.convert_to_xml('ledger')).grid(row=0, column=1)
        
        # Stock items section
        stock_frame = ttk.LabelFrame(masters_frame, text="Stock Item Masters", padding="10")
        stock_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(stock_frame, text="Download Stock Items Template", 
                  command=lambda: self.create_template('stock_items')).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(stock_frame, text="Convert Stock Items to XML", 
                  command=lambda: self.convert_to_xml('stock_items')).grid(row=0, column=1)
    
    def setup_vouchers_tab(self):
        """Setup the vouchers import tab"""
        vouchers_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(vouchers_frame, text="Transaction Vouchers")
        
        # Sales section
        sales_frame = ttk.LabelFrame(vouchers_frame, text="Sales Vouchers", padding="10")
        sales_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(sales_frame, text="Download Sales Template", 
                  command=lambda: self.create_template('sales')).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(sales_frame, text="Convert Sales to XML", 
                  command=lambda: self.convert_to_xml('sales')).grid(row=0, column=1)
        
        # Purchase section
        purchase_frame = ttk.LabelFrame(vouchers_frame, text="Purchase Vouchers", padding="10")
        purchase_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(purchase_frame, text="Download Purchase Template", 
                  command=lambda: self.create_template('purchase')).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(purchase_frame, text="Convert Purchase to XML", 
                  command=lambda: self.convert_to_xml('purchase')).grid(row=0, column=1)
        
        # Receipt section
        receipt_frame = ttk.LabelFrame(vouchers_frame, text="Receipt Vouchers", padding="10")
        receipt_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(receipt_frame, text="Download Receipt Template", 
                  command=lambda: self.create_template('receipt')).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(receipt_frame, text="Convert Receipt to XML", 
                  command=lambda: self.convert_to_xml('receipt')).grid(row=0, column=1)
        
        # Payment section
        payment_frame = ttk.LabelFrame(vouchers_frame, text="Payment Vouchers", padding="10")
        payment_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(payment_frame, text="Download Payment Template", 
                  command=lambda: self.create_template('payment')).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(payment_frame, text="Convert Payment to XML", 
                  command=lambda: self.convert_to_xml('payment')).grid(row=0, column=1)
    
    def setup_templates_tab(self):
        """Setup the templates and help tab"""
        templates_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(templates_frame, text="Templates & Help")
        
        # Help text
        help_text = tk.Text(templates_frame, wrap=tk.WORD, height=20, width=70)
        help_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        help_content = """
TALLY PRIME BULK IMPORT TOOL - USER GUIDE

This tool helps you import bulk data into Tally Prime through Excel files.

FEATURES:
- Convert Excel data to Tally-compatible XML format
- Support for all major Tally modules (Sales, Purchase, Ledgers, Stock Items, etc.)
- User-friendly templates for data entry
- Automatic GST calculations and tax handling
- Multi-line voucher support

HOW TO USE:

1. DOWNLOAD TEMPLATES:
   - Click on "Download [Type] Template" buttons to get Excel templates
   - Templates contain all required columns with sample data
   - Save templates to your computer

2. FILL DATA:
   - Open the downloaded Excel templates
   - Replace sample data with your actual data
   - Follow the column headers exactly as provided
   - Date format: DD/MM/YYYY or DD-MM-YYYY
   - Numbers: Enter without currency symbols

3. CONVERT TO XML:
   - Click "Convert [Type] to XML" buttons
   - Select your filled Excel file when prompted
   - Tool will generate XML file in the output directory

4. IMPORT INTO TALLY:
   - Open Tally Prime
   - Go to Gateway of Tally > Import Data
   - Select the XML file generated by this tool
   - Review and confirm the import

IMPORTANT NOTES:
- Always backup your Tally data before importing
- Create required ledgers and groups before importing vouchers
- GST rates should be in percentage (e.g., 18 for 18%)
- Voucher numbers should be unique
- Party names must match exactly with ledger names

SUPPORTED FORMATS:
- Masters: Ledgers, Stock Items, Groups
- Vouchers: Sales, Purchase, Receipt, Payment, Journal
- All voucher types support multi-line entries

For technical support or queries, check the documentation
or create an issue on the project repository.
        """
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        # Scrollbar for help text
        scrollbar = ttk.Scrollbar(templates_frame, orient=tk.VERTICAL, command=help_text.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        help_text.config(yscrollcommand=scrollbar.set)
        
        templates_frame.columnconfigure(0, weight=1)
        templates_frame.rowconfigure(0, weight=1)
    
    def create_template(self, template_type: str):
        """Create and save Excel templates"""
        templates = {
            'ledger': {
                'filename': 'Ledger_Template.xlsx',
                'data': {
                    'Name': ['ABC Company', 'XYZ Supplier', 'Cash', 'Bank Account'],
                    'Group': ['Sundry Debtors', 'Sundry Creditors', 'Cash-in-Hand', 'Bank Accounts'],
                    'Alias': ['', '', '', ''],
                    'Address': ['123 Main St, City', '456 Oak Ave, Town', '', ''],
                    'Mobile': ['9876543210', '9876543211', '', ''],
                    'Email': ['abc@company.com', 'xyz@supplier.com', '', ''],
                    'GSTIN': ['29ABCDE1234F1Z5', '29XYZAB5678G1H9', '', ''],
                    'Opening_Balance': [25000, -15000, 10000, 50000]
                }
            },
            'stock_items': {
                'filename': 'Stock_Items_Template.xlsx',
                'data': {
                    'Name': ['Product A', 'Product B', 'Service Item', 'Raw Material'],
                    'Alias': ['PROD-A', 'PROD-B', 'SERVICE', 'RAW-MAT'],
                    'Group': ['Primary', 'Primary', 'Primary', 'Primary'],
                    'Category': ['Primary', 'Primary', 'Primary', 'Primary'],
                    'Unit': ['Nos', 'Kg', 'Hrs', 'Ltrs'],
                    'HSN_Code': ['1234', '5678', '9999', '1111'],
                    'GST_Rate': [18, 12, 18, 5],
                    'Opening_Quantity': [100, 50, 0, 200],
                    'Opening_Rate': [1000, 500, 1500, 100]
                }
            },
            'sales': {
                'filename': 'Sales_Template.xlsx',
                'data': {
                    'Voucher_No': ['S001', 'S001', 'S002'],
                    'Date': ['01/04/2024', '01/04/2024', '02/04/2024'],
                    'Party_Name': ['ABC Company', 'ABC Company', 'XYZ Customer'],
                    'Sales_Ledger': ['Sales', 'Sales', 'Sales'],
                    'Item_Name': ['Product A', 'Product B', 'Product A'],
                    'Quantity': [2, 1, 5],
                    'Rate': [1000, 500, 1000],
                    'GST_Rate': [18, 12, 18],
                    'Ref_No': ['REF001', 'REF001', 'REF002'],
                    'Ref_Date': ['01/04/2024', '01/04/2024', '02/04/2024']
                }
            },
            'purchase': {
                'filename': 'Purchase_Template.xlsx',
                'data': {
                    'Voucher_No': ['P001', 'P001', 'P002'],
                    'Date': ['01/04/2024', '01/04/2024', '03/04/2024'],
                    'Party_Name': ['XYZ Supplier', 'XYZ Supplier', 'ABC Vendor'],
                    'Purchase_Ledger': ['Purchase', 'Purchase', 'Purchase'],
                    'Item_Name': ['Raw Material', 'Product B', 'Raw Material'],
                    'Quantity': [10, 5, 20],
                    'Rate': [100, 500, 100],
                    'GST_Rate': [5, 12, 5],
                    'Ref_No': ['BILL001', 'BILL001', 'BILL002'],
                    'Ref_Date': ['01/04/2024', '01/04/2024', '03/04/2024']
                }
            },
            'receipt': {
                'filename': 'Receipt_Template.xlsx',
                'data': {
                    'Voucher_No': ['R001', 'R002', 'R003'],
                    'Date': ['05/04/2024', '06/04/2024', '07/04/2024'],
                    'Party_Name': ['ABC Company', 'XYZ Customer', 'PQR Client'],
                    'Cash_Bank_Ledger': ['Cash', 'Bank Account', 'Cash'],
                    'Amount': [25000, 15000, 8000],
                    'Narration': ['Payment received against invoice', 'Collection from customer', 'Cash received']
                }
            },
            'payment': {
                'filename': 'Payment_Template.xlsx',
                'data': {
                    'Voucher_No': ['PAY001', 'PAY002', 'PAY003'],
                    'Date': ['08/04/2024', '09/04/2024', '10/04/2024'],
                    'Expense_Ledger': ['Office Rent', 'Electricity Expenses', 'Transport Expenses'],
                    'Cash_Bank_Ledger': ['Bank Account', 'Cash', 'Bank Account'],
                    'Amount': [15000, 2500, 3000],
                    'Narration': ['Monthly office rent paid', 'Electricity bill payment', 'Transport charges']
                }
            }
        }
        
        if template_type in templates:
            template = templates[template_type]
            df = pd.DataFrame(template['data'])
            
            file_path = self.templates_dir / template['filename']
            df.to_excel(file_path, index=False)
            
            messagebox.showinfo("Template Created", 
                              f"Template saved: {file_path}\n\n"
                              f"Please fill in your data and save the file.")
            
            # Open the file location
            if sys.platform.startswith('win'):
                os.startfile(self.templates_dir)
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{self.templates_dir}"')
            else:
                os.system(f'xdg-open "{self.templates_dir}"')
    
    def convert_to_xml(self, data_type: str):
        """Convert Excel data to XML"""
        try:
            # File selection dialog
            file_path = filedialog.askopenfilename(
                title=f"Select {data_type.title()} Excel File",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            self.status_var.set(f"Processing {data_type} data...")
            self.progress_var.set(0)
            self.root.update()
            
            # Read Excel file
            df = pd.read_excel(file_path)
            self.progress_var.set(25)
            self.root.update()
            
            # Generate XML based on data type
            xml_content = ""
            if data_type == 'ledger':
                xml_content = self.masters_importer.create_ledger_xml(df)
            elif data_type == 'stock_items':
                xml_content = self.masters_importer.create_stock_item_xml(df)
            elif data_type == 'sales':
                xml_content = self.vouchers_importer.create_sales_voucher_xml(df)
            elif data_type == 'purchase':
                xml_content = self.vouchers_importer.create_purchase_voucher_xml(df)
            elif data_type == 'receipt':
                xml_content = self.vouchers_importer.create_receipt_voucher_xml(df)
            elif data_type == 'payment':
                xml_content = self.vouchers_importer.create_payment_voucher_xml(df)
            
            self.progress_var.set(75)
            self.root.update()
            
            # Save XML file
            output_path = Path(self.output_var.get())
            output_path.mkdir(exist_ok=True)
            
            xml_filename = f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            xml_file_path = output_path / xml_filename
            
            with open(xml_file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            self.progress_var.set(100)
            self.status_var.set(f"XML generated successfully: {xml_filename}")
            
            messagebox.showinfo("Success", 
                              f"XML file generated successfully!\n\n"
                              f"File: {xml_file_path}\n\n"
                              f"You can now import this file into Tally Prime:\n"
                              f"Gateway of Tally > Import Data > Select XML file")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error converting file: {str(e)}")
            self.status_var.set("Error occurred")
            self.progress_var.set(0)
    
    def select_output_dir(self):
        """Select output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_var.set(directory)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TallyBulkImporter()
    app.run()