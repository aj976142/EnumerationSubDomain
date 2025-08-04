#!/usr/bin/env python3
"""
Tally Excel Sales Data Importer
A tool to process Excel files containing sales data and generate Tally-compatible XML files
Works with .xlsx and .xls files directly - No API required!
"""

import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import argparse
import os
import sys
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class TallyExcelImporter:
    """Excel-based Tally sales data importer"""
    
    def __init__(self):
        self.invoices = []
        self.items = []
        self.errors = []
        
    def read_excel_file(self, file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """Read data from Excel file (.xlsx or .xls)"""
        try:
            # Auto-detect sheet if not specified
            if sheet_name is None:
                # Read first sheet
                df = pd.read_excel(file_path, sheet_name=0)
                print(f"Reading first sheet from {file_path}")
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"Reading sheet '{sheet_name}' from {file_path}")
            
            # Get basic info
            print(f"Found {len(df)} rows and {len(df.columns)} columns")
            print(f"Columns: {list(df.columns)}")
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            print(f"After removing empty rows: {len(df)} records")
            
            return df
            
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return pd.DataFrame()
    
    def list_excel_sheets(self, file_path: str) -> List[str]:
        """List all sheet names in Excel file"""
        try:
            xl_file = pd.ExcelFile(file_path)
            return xl_file.sheet_names
        except Exception as e:
            print(f"Error reading Excel sheets: {e}")
            return []
    
    def detect_data_structure(self, df: pd.DataFrame) -> Dict:
        """Automatically detect the data structure in Excel"""
        structure = {
            'format_type': 'unknown',
            'has_items_columns': False,
            'item_columns': [],
            'invoice_columns': [],
            'suggested_mappings': {}
        }
        
        columns = [col.lower() for col in df.columns]
        
        # Check for item columns (multiple items per row)
        item_patterns = ['item_', 'product_', 'stock_']
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in item_patterns):
                structure['item_columns'].append(col)
                structure['has_items_columns'] = True
        
        # Map common column names
        mapping_rules = {
            'invoice_number': ['invoice', 'bill', 'voucher', 'inv_no', 'bill_no'],
            'date': ['date', 'inv_date', 'bill_date'],
            'party_name': ['party', 'customer', 'client', 'buyer', 'name'],
            'party_address': ['address', 'add'],
            'party_gstin': ['gstin', 'gst_no', 'tin'],
            'total_amount': ['total_amount', 'total', 'amount', 'value', 'sum'],
            'tax_amount': ['tax_amount', 'tax', 'gst_amount', 'gst', 'vat'],
            'remarks': ['remarks', 'notes', 'description']
        }
        
        for standard_field, patterns in mapping_rules.items():
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in patterns):
                    structure['suggested_mappings'][standard_field] = col
                    break
        
        # Determine format type
        if structure['has_items_columns']:
            structure['format_type'] = 'flat_with_items'
        elif len(df.columns) <= 10:
            structure['format_type'] = 'simple_invoice'
        else:
            structure['format_type'] = 'detailed_invoice'
        
        return structure
    
    def normalize_excel_data(self, df: pd.DataFrame) -> List[Dict]:
        """Convert Excel DataFrame to normalized invoice format"""
        structure = self.detect_data_structure(df)
        invoices = []
        
        print(f"Detected format: {structure['format_type']}")
        print(f"Suggested mappings: {structure['suggested_mappings']}")
        
        for index, row in df.iterrows():
            try:
                # Create basic invoice structure
                invoice = {
                    'invoice_number': self._get_excel_value(row, structure['suggested_mappings'].get('invoice_number')),
                    'date': self._format_excel_date(row, structure['suggested_mappings'].get('date')),
                    'party_name': self._get_excel_value(row, structure['suggested_mappings'].get('party_name')),
                    'party_address': self._get_excel_value(row, structure['suggested_mappings'].get('party_address')),
                    'party_gstin': self._get_excel_value(row, structure['suggested_mappings'].get('party_gstin')),
                    'total_amount': self._get_excel_amount(row, structure['suggested_mappings'].get('total_amount')),
                    'tax_amount': self._get_excel_amount(row, structure['suggested_mappings'].get('tax_amount')),
                    'remarks': self._get_excel_value(row, structure['suggested_mappings'].get('remarks')),
                    'items': []
                }
                
                # Extract items based on structure
                if structure['has_items_columns']:
                    invoice['items'] = self._extract_items_from_excel_row(row, structure['item_columns'])
                else:
                    # Create single item from invoice data
                    item = {
                        'item_name': invoice.get('party_name', 'Sales Item'),
                        'quantity': '1',
                        'rate': invoice.get('total_amount', '0'),
                        'amount': invoice.get('total_amount', '0'),
                        'unit': 'Nos'
                    }
                    invoice['items'] = [item]
                
                # Skip rows without essential data
                if invoice['invoice_number'] and invoice['party_name']:
                    invoices.append(invoice)
                else:
                    self.errors.append(f"Row {index + 2}: Missing invoice number or party name")
                    
            except Exception as e:
                self.errors.append(f"Row {index + 2}: Error processing data - {str(e)}")
        
        return invoices
    
    def _get_excel_value(self, row, column_name):
        """Get value from Excel row, handling various data types"""
        if not column_name or column_name not in row:
            return ''
        
        value = row[column_name]
        if pd.isna(value):
            return ''
        
        return str(value).strip()
    
    def _get_excel_amount(self, row, column_name):
        """Get numeric amount from Excel row"""
        if not column_name or column_name not in row:
            return '0'
        
        value = row[column_name]
        if pd.isna(value):
            return '0'
        
        try:
            # Handle Excel number formats
            if isinstance(value, (int, float)):
                return str(abs(float(value)))  # Use absolute value
            else:
                # Remove currency symbols and commas
                clean_value = str(value).replace(',', '').replace('₹', '').replace('$', '').strip()
                return str(abs(float(clean_value)))
        except:
            return '0'
    
    def _format_excel_date(self, row, column_name):
        """Format date from Excel row"""
        if not column_name or column_name not in row:
            return datetime.now().strftime('%Y-%m-%d')
        
        value = row[column_name]
        if pd.isna(value):
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Handle Excel datetime
            if isinstance(value, pd.Timestamp):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            else:
                # Try to parse string date
                date_str = str(value)
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        return date_obj.strftime('%Y-%m-%d')
                    except:
                        continue
                return datetime.now().strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_items_from_excel_row(self, row, item_columns):
        """Extract item details from Excel row with item columns"""
        items = []
        
        # Group item columns by number (item_1_name, item_1_qty, etc.)
        item_groups = {}
        for col in item_columns:
            col_lower = col.lower()
            
            # Extract item number
            parts = col_lower.split('_')
            item_num = '1'  # default
            
            for i, part in enumerate(parts):
                if part.isdigit():
                    item_num = part
                    break
                elif part in ['1st', 'first']:
                    item_num = '1'
                elif part in ['2nd', 'second']:
                    item_num = '2'
                elif part in ['3rd', 'third']:
                    item_num = '3'
            
            if item_num not in item_groups:
                item_groups[item_num] = {}
            
            # Determine field type
            if 'name' in col_lower or 'item' in col_lower or 'product' in col_lower:
                item_groups[item_num]['name'] = col
            elif 'qty' in col_lower or 'quantity' in col_lower:
                item_groups[item_num]['quantity'] = col
            elif 'rate' in col_lower or 'price' in col_lower:
                item_groups[item_num]['rate'] = col
            elif 'amount' in col_lower or 'value' in col_lower:
                item_groups[item_num]['amount'] = col
            elif 'unit' in col_lower:
                item_groups[item_num]['unit'] = col
            elif 'hsn' in col_lower:
                item_groups[item_num]['hsn'] = col
        
        # Create items from groups
        for item_num, fields in item_groups.items():
            item_name = self._get_excel_value(row, fields.get('name'))
            
            if item_name:  # Only add items with names
                item = {
                    'item_name': item_name,
                    'quantity': self._get_excel_amount(row, fields.get('quantity')) or '1',
                    'rate': self._get_excel_amount(row, fields.get('rate')) or '0',
                    'amount': self._get_excel_amount(row, fields.get('amount')) or '0',
                    'unit': self._get_excel_value(row, fields.get('unit')) or 'Nos',
                    'hsn_code': self._get_excel_value(row, fields.get('hsn'))
                }
                
                # Calculate missing values
                if item['amount'] == '0' and item['rate'] != '0' and item['quantity'] != '0':
                    item['amount'] = str(float(item['rate']) * float(item['quantity']))
                elif item['rate'] == '0' and item['amount'] != '0' and item['quantity'] != '0':
                    item['rate'] = str(float(item['amount']) / float(item['quantity']))
                
                items.append(item)
        
        return items
    
    def validate_invoices(self, invoices: List[Dict]) -> List[Dict]:
        """Validate invoice data specifically for Excel input"""
        valid_invoices = []
        
        for i, invoice in enumerate(invoices):
            invoice_errors = []
            
            # Check required fields
            if not invoice.get('invoice_number'):
                invoice_errors.append("Missing invoice number")
            
            if not invoice.get('party_name'):
                invoice_errors.append("Missing party name")
            
            # Validate amounts
            try:
                total_amount = float(invoice.get('total_amount', '0'))
                if total_amount <= 0:
                    invoice_errors.append("Invalid or zero total amount")
            except ValueError:
                invoice_errors.append(f"Invalid total amount: {invoice.get('total_amount')}")
            
            # Validate items
            if not invoice.get('items'):
                invoice_errors.append("No items found")
            else:
                for j, item in enumerate(invoice['items']):
                    if not item.get('item_name'):
                        invoice_errors.append(f"Item {j+1}: Missing item name")
            
            if invoice_errors:
                self.errors.extend([f"Invoice {invoice.get('invoice_number', i+1)}: {error}" for error in invoice_errors])
            else:
                valid_invoices.append(invoice)
        
        print(f"Validated {len(valid_invoices)} out of {len(invoices)} invoices")
        if self.errors:
            print(f"Found {len(self.errors)} validation errors")
        
        return valid_invoices
    
    def generate_tally_xml(self, invoices: List[Dict], output_file: str):
        """Generate Tally XML import file"""
        try:
            root = ET.Element("ENVELOPE")
            header = ET.SubElement(root, "HEADER")
            ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
            
            body = ET.SubElement(root, "BODY")
            import_data = ET.SubElement(body, "IMPORTDATA")
            request_desc = ET.SubElement(import_data, "REQUESTDESC")
            ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
            
            request_data = ET.SubElement(import_data, "REQUESTDATA")
            
            for invoice in invoices:
                tallymessage = ET.SubElement(request_data, "TALLYMESSAGE")
                voucher = ET.SubElement(tallymessage, "VOUCHER", 
                                      REMOTEID=invoice.get('invoice_number', ''),
                                      VCHTYPE="Sales",
                                      ACTION="Create")
                
                # Voucher details
                ET.SubElement(voucher, "DATE").text = self._format_tally_date(invoice.get('date', ''))
                ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Sales"
                ET.SubElement(voucher, "VOUCHERNUMBER").text = invoice.get('invoice_number', '')
                ET.SubElement(voucher, "PARTYNAME").text = invoice.get('party_name', '')
                
                if invoice.get('remarks'):
                    ET.SubElement(voucher, "NARRATION").text = invoice.get('remarks', '')
                
                # Party ledger entry (Debit)
                party_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(party_entry, "LEDGERNAME").text = invoice.get('party_name', '')
                ET.SubElement(party_entry, "GSTCLASS").text = ""
                ET.SubElement(party_entry, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(party_entry, "AMOUNT").text = invoice.get('total_amount', '0')
                
                # Sales ledger entry (Credit)
                sales_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(sales_entry, "LEDGERNAME").text = "Sales"
                ET.SubElement(sales_entry, "GSTCLASS").text = ""
                ET.SubElement(sales_entry, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(sales_entry, "AMOUNT").text = f"-{invoice.get('total_amount', '0')}"
                
                # Inventory entries
                for item in invoice.get('items', []):
                    inventory_entry = ET.SubElement(voucher, "ALLINVENTORYENTRIES.LIST")
                    ET.SubElement(inventory_entry, "STOCKITEMNAME").text = item.get('item_name', '')
                    ET.SubElement(inventory_entry, "ISDEEMEDPOSITIVE").text = "No"
                    ET.SubElement(inventory_entry, "ACTUALQTY").text = f"-{item.get('quantity', '0')} {item.get('unit', 'Nos')}"
                    ET.SubElement(inventory_entry, "BILLEDQTY").text = f"-{item.get('quantity', '0')} {item.get('unit', 'Nos')}"
                    ET.SubElement(inventory_entry, "AMOUNT").text = f"-{item.get('amount', '0')}"
                    ET.SubElement(inventory_entry, "RATE").text = f"{item.get('rate', '0')}/{item.get('unit', 'Nos')}"
            
            # Format XML nicely
            self._indent_xml(root)
            tree = ET.ElementTree(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"Tally XML file generated: {output_file}")
            
        except Exception as e:
            print(f"Error generating Tally XML: {e}")
    
    def _format_tally_date(self, date_str: str) -> str:
        """Format date for Tally XML (YYYYMMDD)"""
        try:
            if date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime("%Y%m%d")
        except:
            pass
        return datetime.now().strftime("%Y%m%d")
    
    def _indent_xml(self, elem, level=0):
        """Add proper indentation to XML for readability"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def generate_item_master(self, invoices: List[Dict], output_file: str):
        """Generate item master XML for Tally"""
        try:
            items_set = set()
            for invoice in invoices:
                for item in invoice.get('items', []):
                    if item.get('item_name'):
                        items_set.add((item['item_name'], item.get('unit', 'Nos')))
            
            root = ET.Element("ENVELOPE")
            header = ET.SubElement(root, "HEADER")
            ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
            
            body = ET.SubElement(root, "BODY")
            import_data = ET.SubElement(body, "IMPORTDATA")
            request_desc = ET.SubElement(import_data, "REQUESTDESC")
            ET.SubElement(request_desc, "REPORTNAME").text = "Stock Items"
            
            request_data = ET.SubElement(import_data, "REQUESTDATA")
            
            for item_name, unit in sorted(items_set):
                tallymessage = ET.SubElement(request_data, "TALLYMESSAGE")
                stockitem = ET.SubElement(tallymessage, "STOCKITEM", 
                                        REMOTEID=item_name,
                                        ACTION="Create")
                
                ET.SubElement(stockitem, "NAME").text = item_name
                ET.SubElement(stockitem, "PARENT").text = "Primary"
                ET.SubElement(stockitem, "CATEGORY").text = "Primary"
                ET.SubElement(stockitem, "TAXCLASSIFICATIONNAME").text = ""
                ET.SubElement(stockitem, "BASEUNITS").text = unit
                ET.SubElement(stockitem, "ADDITIONALUNITS").text = unit
                ET.SubElement(stockitem, "GSTAPPLICABLE").text = "Applicable"
            
            self._indent_xml(root)
            tree = ET.ElementTree(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"Item master XML generated: {output_file}")
            
        except Exception as e:
            print(f"Error generating item master: {e}")
    
    def generate_excel_report(self, invoices: List[Dict], output_file: str):
        """Generate Excel report of processed invoices"""
        try:
            # Prepare data for Excel
            report_data = []
            for invoice in invoices:
                report_data.append({
                    'Invoice Number': invoice.get('invoice_number', ''),
                    'Date': invoice.get('date', ''),
                    'Party Name': invoice.get('party_name', ''),
                    'Party Address': invoice.get('party_address', ''),
                    'Party GSTIN': invoice.get('party_gstin', ''),
                    'Total Amount': invoice.get('total_amount', '0'),
                    'Tax Amount': invoice.get('tax_amount', '0'),
                    'Item Count': len(invoice.get('items', [])),
                    'Remarks': invoice.get('remarks', '')
                })
            
            # Create Excel file
            df = pd.DataFrame(report_data)
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Summary sheet
                df.to_excel(writer, sheet_name='Invoice Summary', index=False)
                
                # Detailed items sheet
                item_data = []
                for invoice in invoices:
                    for item in invoice.get('items', []):
                        item_data.append({
                            'Invoice Number': invoice.get('invoice_number', ''),
                            'Party Name': invoice.get('party_name', ''),
                            'Item Name': item.get('item_name', ''),
                            'Quantity': item.get('quantity', '0'),
                            'Unit': item.get('unit', 'Nos'),
                            'Rate': item.get('rate', '0'),
                            'Amount': item.get('amount', '0'),
                            'HSN Code': item.get('hsn_code', '')
                        })
                
                if item_data:
                    df_items = pd.DataFrame(item_data)
                    df_items.to_excel(writer, sheet_name='Item Details', index=False)
                
                # Errors sheet if any
                if self.errors:
                    df_errors = pd.DataFrame({'Errors': self.errors})
                    df_errors.to_excel(writer, sheet_name='Validation Errors', index=False)
            
            print(f"Excel report generated: {output_file}")
            
        except Exception as e:
            print(f"Error generating Excel report: {e}")
    
    def process_excel_file(self, input_file: str, output_dir: str = "output", sheet_name: str = None):
        """Main method to process Excel file"""
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Check file extension
        file_ext = os.path.splitext(input_file)[1].lower()
        if file_ext not in ['.xlsx', '.xls']:
            print(f"Error: Unsupported file format '{file_ext}'. Please use .xlsx or .xls files.")
            return
        
        # List sheets if no specific sheet provided
        if sheet_name is None:
            sheets = self.list_excel_sheets(input_file)
            if len(sheets) > 1:
                print(f"Multiple sheets found: {sheets}")
                print(f"Using first sheet: '{sheets[0]}'")
                print(f"To specify a sheet, use: --sheet 'SheetName'")
            sheet_name = sheets[0] if sheets else 0
        
        # Read Excel data
        df = self.read_excel_file(input_file, sheet_name)
        if df.empty:
            print("No data found in Excel file")
            return
        
        # Process data
        invoices = self.normalize_excel_data(df)
        if not invoices:
            print("No invoices could be processed from Excel data")
            return
        
        valid_invoices = self.validate_invoices(invoices)
        if not valid_invoices:
            print("No valid invoices found after validation")
            if self.errors:
                print("Errors found:")
                for error in self.errors[:10]:  # Show first 10 errors
                    print(f"  - {error}")
            return
        
        # Generate output files
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Generate Tally XML
        tally_xml_file = os.path.join(output_dir, f"{base_name}_tally_import.xml")
        self.generate_tally_xml(valid_invoices, tally_xml_file)
        
        # Generate item master
        item_master_file = os.path.join(output_dir, f"{base_name}_item_master.xml")
        self.generate_item_master(valid_invoices, item_master_file)
        
        # Generate Excel report
        excel_report_file = os.path.join(output_dir, f"{base_name}_report.xlsx")
        self.generate_excel_report(valid_invoices, excel_report_file)
        
        print(f"\n" + "="*50)
        print(f"✅ Processing completed successfully!")
        print(f"📊 Processed {len(valid_invoices)} invoices from Excel")
        print(f"📁 Output files saved in: {output_dir}")
        print(f"📝 Files generated:")
        print(f"   • {base_name}_tally_import.xml (Import to Tally)")
        print(f"   • {base_name}_item_master.xml (Import items first)")
        print(f"   • {base_name}_report.xlsx (Summary report)")
        
        if self.errors:
            print(f"⚠️  Found {len(self.errors)} validation errors (see report for details)")


def main():
    parser = argparse.ArgumentParser(description="Tally Excel Sales Data Importer")
    parser.add_argument("input_file", nargs='?', help="Input Excel file (.xlsx or .xls)")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("-s", "--sheet", help="Excel sheet name (default: first sheet)")
    parser.add_argument("--list-sheets", action="store_true", help="List all sheets in Excel file")
    parser.add_argument("--sample", action="store_true", help="Generate sample Excel file")
    
    args = parser.parse_args()
    
    importer = TallyExcelImporter()
    
    if args.sample:
        generate_sample_excel()
    elif args.list_sheets and args.input_file:
        sheets = importer.list_excel_sheets(args.input_file)
        print(f"Sheets in {args.input_file}:")
        for i, sheet in enumerate(sheets, 1):
            print(f"  {i}. {sheet}")
    elif args.input_file:
        importer.process_excel_file(args.input_file, args.output, args.sheet)
    else:
        parser.print_help()


def generate_sample_excel():
    """Generate sample Excel files for testing"""
    try:
        # Sample data with multiple items per invoice
        sample_data = [
            {
                'Invoice Number': 'INV001',
                'Date': '2024-01-15',
                'Party Name': 'ABC Company',
                'Party Address': '123 Main St, Mumbai',
                'Party GSTIN': '27ABCDE1234F1Z5',
                'Total Amount': 11800,
                'Tax Amount': 1800,
                'Item_1_Name': 'Product A',
                'Item_1_Quantity': 10,
                'Item_1_Rate': 1000,
                'Item_1_Amount': 10000,
                'Item_2_Name': 'Product B',
                'Item_2_Quantity': 1,
                'Item_2_Rate': 1000,
                'Item_2_Amount': 1000,
                'Remarks': 'Sample invoice 1'
            },
            {
                'Invoice Number': 'INV002',
                'Date': '2024-01-16',
                'Party Name': 'XYZ Ltd',
                'Party Address': '456 Park Ave, Delhi',
                'Party GSTIN': '07XYZAB5678G2H9',
                'Total Amount': 5900,
                'Tax Amount': 900,
                'Item_1_Name': 'Product C',
                'Item_1_Quantity': 5,
                'Item_1_Rate': 1000,
                'Item_1_Amount': 5000,
                'Item_2_Name': '',
                'Item_2_Quantity': '',
                'Item_2_Rate': '',
                'Item_2_Amount': '',
                'Remarks': 'Sample invoice 2'
            },
            {
                'Invoice Number': 'INV003',
                'Date': '2024-01-17',
                'Party Name': 'PQR Industries',
                'Party Address': '789 Business St, Chennai',
                'Party GSTIN': '33PQRCD9012I3J4',
                'Total Amount': 23600,
                'Tax Amount': 3600,
                'Item_1_Name': 'Product D',
                'Item_1_Quantity': 20,
                'Item_1_Rate': 1000,
                'Item_1_Amount': 20000,
                'Item_2_Name': '',
                'Item_2_Quantity': '',
                'Item_2_Rate': '',
                'Item_2_Amount': '',
                'Remarks': 'Bulk order'
            }
        ]
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(sample_data)
        
        with pd.ExcelWriter('sample_sales_data.xlsx', engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sales Data', index=False)
            
            # Add a second sheet with different format
            simple_data = [
                {'Invoice': 'S001', 'Customer': 'Simple Corp', 'Amount': 5000, 'Date': '2024-01-20'},
                {'Invoice': 'S002', 'Customer': 'Easy Ltd', 'Amount': 7500, 'Date': '2024-01-21'},
            ]
            df_simple = pd.DataFrame(simple_data)
            df_simple.to_excel(writer, sheet_name='Simple Format', index=False)
        
        print("✅ Sample Excel file generated: sample_sales_data.xlsx")
        print("📊 Contains 2 sheets:")
        print("   • Sales Data (detailed format with items)")
        print("   • Simple Format (basic format)")
        print("\n🚀 To process the sample file, run:")
        print("   python3 tally_excel_importer.py sample_sales_data.xlsx")
        print("   python3 tally_excel_importer.py sample_sales_data.xlsx --sheet 'Simple Format'")
        
    except Exception as e:
        print(f"Error generating sample Excel file: {e}")
        print("Make sure you have pandas and openpyxl installed:")
        print("pip install pandas openpyxl")


if __name__ == "__main__":
    main()