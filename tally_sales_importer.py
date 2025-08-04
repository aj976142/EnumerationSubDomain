#!/usr/bin/env python3
"""
Tally Sales Data Importer
A tool to process and import Tally sales data as item invoices
"""

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Union
import argparse
import os
import sys

class TallySalesImporter:
    """Main class for processing Tally sales data"""
    
    def __init__(self):
        self.invoices = []
        self.items = []
        self.parties = []
        self.company_info = {}
        
    def read_csv_data(self, file_path: str) -> List[Dict]:
        """Read sales data from CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                
                delimiter = ','
                if '\t' in sample:
                    delimiter = '\t'
                elif ';' in sample:
                    delimiter = ';'
                
                reader = csv.DictReader(file, delimiter=delimiter)
                data = list(reader)
                print(f"Successfully read {len(data)} records from {file_path}")
                return data
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []
    
    def read_xml_data(self, file_path: str) -> List[Dict]:
        """Read sales data from XML file (Tally XML format)"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = []
            
            # Process Tally XML structure
            for voucher in root.findall('.//VOUCHER'):
                invoice_data = {
                    'voucher_type': voucher.find('VOUCHERTYPENAME').text if voucher.find('VOUCHERTYPENAME') is not None else '',
                    'voucher_number': voucher.find('VOUCHERNUMBER').text if voucher.find('VOUCHERNUMBER') is not None else '',
                    'date': voucher.find('DATE').text if voucher.find('DATE') is not None else '',
                    'party_name': voucher.find('PARTYNAME').text if voucher.find('PARTYNAME') is not None else '',
                    'amount': voucher.find('AMOUNT').text if voucher.find('AMOUNT') is not None else '0',
                    'items': []
                }
                
                # Extract line items
                for item in voucher.findall('.//ALLINVENTORYENTRIES.LIST'):
                    item_name = item.find('STOCKITEMNAME').text if item.find('STOCKITEMNAME') is not None else ''
                    quantity = item.find('ACTUALQTY').text if item.find('ACTUALQTY') is not None else '0'
                    rate = item.find('RATE').text if item.find('RATE') is not None else '0'
                    amount = item.find('AMOUNT').text if item.find('AMOUNT') is not None else '0'
                    
                    invoice_data['items'].append({
                        'item_name': item_name,
                        'quantity': quantity,
                        'rate': rate,
                        'amount': amount
                    })
                
                data.append(invoice_data)
            
            print(f"Successfully read {len(data)} vouchers from {file_path}")
            return data
        except Exception as e:
            print(f"Error reading XML file: {e}")
            return []
    
    def read_json_data(self, file_path: str) -> List[Dict]:
        """Read sales data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    data = [data]
                print(f"Successfully read {len(data)} records from {file_path}")
                return data
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return []
    
    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Normalize different data formats into standard invoice format"""
        normalized_invoices = []
        
        for record in raw_data:
            # Try to map common field names to standard format
            invoice = {
                'invoice_number': self._get_field_value(record, ['invoice_number', 'voucher_number', 'bill_no', 'invoice_no']),
                'date': self._get_field_value(record, ['date', 'invoice_date', 'bill_date']),
                'party_name': self._get_field_value(record, ['party_name', 'customer_name', 'client_name', 'buyer_name']),
                'party_address': self._get_field_value(record, ['party_address', 'customer_address', 'address']),
                'party_gstin': self._get_field_value(record, ['party_gstin', 'customer_gstin', 'gstin']),
                'total_amount': self._get_field_value(record, ['total_amount', 'amount', 'total', 'bill_amount']),
                'tax_amount': self._get_field_value(record, ['tax_amount', 'gst_amount', 'tax']),
                'items': record.get('items', [])
            }
            
            # If items are not in nested format, try to extract from flat structure
            if not invoice['items'] and any(key.startswith('item') for key in record.keys()):
                invoice['items'] = self._extract_items_from_flat(record)
            
            normalized_invoices.append(invoice)
        
        return normalized_invoices
    
    def _get_field_value(self, record: Dict, field_names: List[str]) -> str:
        """Get field value from record using multiple possible field names"""
        for field_name in field_names:
            if field_name in record and record[field_name]:
                return str(record[field_name])
        return ''
    
    def _extract_items_from_flat(self, record: Dict) -> List[Dict]:
        """Extract items from flat record structure"""
        items = []
        item_fields = {}
        
        # Group item-related fields
        for key, value in record.items():
            if key.startswith('item'):
                parts = key.split('_')
                if len(parts) >= 2:
                    item_index = parts[1] if parts[1].isdigit() else '1'
                    field_name = '_'.join(parts[2:]) if len(parts) > 2 else parts[0]
                    
                    if item_index not in item_fields:
                        item_fields[item_index] = {}
                    item_fields[item_index][field_name] = value
        
        # Convert to items list
        for item_data in item_fields.values():
            item = {
                'item_name': item_data.get('name', ''),
                'quantity': item_data.get('quantity', '0'),
                'rate': item_data.get('rate', '0'),
                'amount': item_data.get('amount', '0'),
                'unit': item_data.get('unit', 'Nos'),
                'hsn_code': item_data.get('hsn', '')
            }
            items.append(item)
        
        return items
    
    def validate_invoices(self, invoices: List[Dict]) -> List[Dict]:
        """Validate invoice data and report issues"""
        valid_invoices = []
        errors = []
        
        for i, invoice in enumerate(invoices):
            invoice_errors = []
            
            # Check required fields
            if not invoice.get('invoice_number'):
                invoice_errors.append("Missing invoice number")
            
            if not invoice.get('date'):
                invoice_errors.append("Missing date")
            
            if not invoice.get('party_name'):
                invoice_errors.append("Missing party name")
            
            # Validate date format
            if invoice.get('date'):
                try:
                    datetime.strptime(invoice['date'], '%Y-%m-%d')
                except ValueError:
                    try:
                        datetime.strptime(invoice['date'], '%d-%m-%Y')
                    except ValueError:
                        invoice_errors.append(f"Invalid date format: {invoice['date']}")
            
            # Validate amounts
            try:
                float(invoice.get('total_amount', '0'))
            except ValueError:
                invoice_errors.append(f"Invalid total amount: {invoice.get('total_amount')}")
            
            if invoice_errors:
                errors.append(f"Invoice {i+1}: {', '.join(invoice_errors)}")
            else:
                valid_invoices.append(invoice)
        
        if errors:
            print("Validation errors found:")
            for error in errors:
                print(f"  - {error}")
        
        print(f"Validated {len(valid_invoices)} out of {len(invoices)} invoices")
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
                
                # Add party ledger entry
                ledger_entries = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(ledger_entries, "LEDGERNAME").text = invoice.get('party_name', '')
                ET.SubElement(ledger_entries, "GSTCLASS").text = ""
                ET.SubElement(ledger_entries, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(ledger_entries, "AMOUNT").text = invoice.get('total_amount', '0')
                
                # Add sales ledger entry
                sales_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(sales_entry, "LEDGERNAME").text = "Sales"
                ET.SubElement(sales_entry, "GSTCLASS").text = ""
                ET.SubElement(sales_entry, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(sales_entry, "AMOUNT").text = f"-{invoice.get('total_amount', '0')}"
                
                # Add inventory entries
                for item in invoice.get('items', []):
                    inventory_entry = ET.SubElement(voucher, "ALLINVENTORYENTRIES.LIST")
                    ET.SubElement(inventory_entry, "STOCKITEMNAME").text = item.get('item_name', '')
                    ET.SubElement(inventory_entry, "ISDEEMEDPOSITIVE").text = "No"
                    ET.SubElement(inventory_entry, "ACTUALQTY").text = f"-{item.get('quantity', '0')} Nos"
                    ET.SubElement(inventory_entry, "BILLEDQTY").text = f"-{item.get('quantity', '0')} Nos"
                    ET.SubElement(inventory_entry, "AMOUNT").text = f"-{item.get('amount', '0')}"
                    ET.SubElement(inventory_entry, "RATE").text = item.get('rate', '0')
            
            # Write to file
            tree = ET.ElementTree(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"Tally XML file generated: {output_file}")
            
        except Exception as e:
            print(f"Error generating Tally XML: {e}")
    
    def _format_tally_date(self, date_str: str) -> str:
        """Format date for Tally XML"""
        if not date_str:
            return datetime.now().strftime("%Y%m%d")
        
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%Y%m%d")
                except ValueError:
                    continue
        except:
            pass
        
        return datetime.now().strftime("%Y%m%d")
    
    def generate_csv_report(self, invoices: List[Dict], output_file: str):
        """Generate CSV report of processed invoices"""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['invoice_number', 'date', 'party_name', 'party_address', 
                             'party_gstin', 'total_amount', 'tax_amount', 'item_count']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for invoice in invoices:
                    row = {
                        'invoice_number': invoice.get('invoice_number', ''),
                        'date': invoice.get('date', ''),
                        'party_name': invoice.get('party_name', ''),
                        'party_address': invoice.get('party_address', ''),
                        'party_gstin': invoice.get('party_gstin', ''),
                        'total_amount': invoice.get('total_amount', '0'),
                        'tax_amount': invoice.get('tax_amount', '0'),
                        'item_count': len(invoice.get('items', []))
                    }
                    writer.writerow(row)
            
            print(f"CSV report generated: {output_file}")
        except Exception as e:
            print(f"Error generating CSV report: {e}")
    
    def generate_item_master(self, invoices: List[Dict], output_file: str):
        """Generate item master XML for Tally"""
        try:
            items_set = set()
            for invoice in invoices:
                for item in invoice.get('items', []):
                    if item.get('item_name'):
                        items_set.add(item['item_name'])
            
            root = ET.Element("ENVELOPE")
            header = ET.SubElement(root, "HEADER")
            ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
            
            body = ET.SubElement(root, "BODY")
            import_data = ET.SubElement(body, "IMPORTDATA")
            request_desc = ET.SubElement(import_data, "REQUESTDESC")
            ET.SubElement(request_desc, "REPORTNAME").text = "Stock Items"
            
            request_data = ET.SubElement(import_data, "REQUESTDATA")
            
            for item_name in sorted(items_set):
                tallymessage = ET.SubElement(request_data, "TALLYMESSAGE")
                stockitem = ET.SubElement(tallymessage, "STOCKITEM", 
                                        REMOTEID=item_name,
                                        ACTION="Create")
                
                name_element = ET.SubElement(stockitem, "NAME")
                name_element.text = item_name
                ET.SubElement(stockitem, "PARENT").text = "Primary"
                ET.SubElement(stockitem, "CATEGORY").text = "Primary"
                ET.SubElement(stockitem, "TAXCLASSIFICATIONNAME").text = ""
                ET.SubElement(stockitem, "BASEUNITS").text = "Nos"
                ET.SubElement(stockitem, "ADDITIONALUNITS").text = "Nos"
                ET.SubElement(stockitem, "GSTAPPLICABLE").text = "Applicable"
            
            tree = ET.ElementTree(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"Item master XML generated: {output_file}")
            
        except Exception as e:
            print(f"Error generating item master: {e}")
    
    def process_file(self, input_file: str, output_dir: str = "output"):
        """Main method to process sales data file"""
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine file type and read data
        file_ext = os.path.splitext(input_file)[1].lower()
        
        if file_ext == '.csv':
            raw_data = self.read_csv_data(input_file)
        elif file_ext == '.xml':
            raw_data = self.read_xml_data(input_file)
        elif file_ext == '.json':
            raw_data = self.read_json_data(input_file)
        else:
            print(f"Unsupported file format: {file_ext}")
            return
        
        if not raw_data:
            print("No data found in input file")
            return
        
        # Normalize and validate data
        invoices = self.normalize_data(raw_data)
        valid_invoices = self.validate_invoices(invoices)
        
        if not valid_invoices:
            print("No valid invoices found after validation")
            return
        
        # Generate output files
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Generate Tally XML
        tally_xml_file = os.path.join(output_dir, f"{base_name}_tally_import.xml")
        self.generate_tally_xml(valid_invoices, tally_xml_file)
        
        # Generate item master
        item_master_file = os.path.join(output_dir, f"{base_name}_item_master.xml")
        self.generate_item_master(valid_invoices, item_master_file)
        
        # Generate CSV report
        csv_report_file = os.path.join(output_dir, f"{base_name}_report.csv")
        self.generate_csv_report(valid_invoices, csv_report_file)
        
        print(f"\nProcessing completed successfully!")
        print(f"Processed {len(valid_invoices)} invoices")
        print(f"Output files saved in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Tally Sales Data Importer")
    parser.add_argument("input_file", nargs='?', help="Input file (CSV, XML, or JSON)")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("--sample", action="store_true", help="Generate sample input files")
    
    args = parser.parse_args()
    
    importer = TallySalesImporter()
    
    if args.sample:
        generate_sample_files()
    elif args.input_file:
        importer.process_file(args.input_file, args.output)
    else:
        parser.print_help()


def generate_sample_files():
    """Generate sample input files for testing"""
    
    # Sample CSV data
    csv_data = """invoice_number,date,party_name,party_address,party_gstin,total_amount,tax_amount,item_1_name,item_1_quantity,item_1_rate,item_1_amount
INV001,2024-01-15,ABC Company,123 Main St Mumbai,27ABCDE1234F1Z5,11800,1800,Product A,10,1000,10000
INV002,2024-01-16,XYZ Ltd,456 Park Ave Delhi,07XYZAB5678G2H9,5900,900,Product B,5,1000,5000
INV003,2024-01-17,PQR Industries,789 Business St Chennai,33PQRCD9012I3J4,23600,3600,Product C,20,1000,20000"""
    
    with open("sample_sales_data.csv", "w", encoding="utf-8") as f:
        f.write(csv_data)
    
    # Sample JSON data
    json_data = [
        {
            "invoice_number": "INV004",
            "date": "2024-01-18",
            "party_name": "LMN Corporation",
            "party_address": "321 Tech Park Bangalore",
            "party_gstin": "29LMNEF3456K7L8",
            "total_amount": "8850",
            "tax_amount": "1350",
            "items": [
                {
                    "item_name": "Product D",
                    "quantity": "3",
                    "rate": "2500",
                    "amount": "7500"
                }
            ]
        }
    ]
    
    with open("sample_sales_data.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    
    print("Sample files generated:")
    print("- sample_sales_data.csv")
    print("- sample_sales_data.json")
    print("\nTo process these files, run:")
    print("python tally_sales_importer.py sample_sales_data.csv")
    print("python tally_sales_importer.py sample_sales_data.json")


if __name__ == "__main__":
    main()