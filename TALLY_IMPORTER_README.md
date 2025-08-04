# Tally Sales Data Importer

A comprehensive Python tool to process and import sales data into Tally ERP as item invoices. This tool can handle various input formats (CSV, JSON, XML) and generates Tally-compatible XML files for seamless import.

## Features

- **Multiple Input Formats**: Supports CSV, JSON, and XML input files
- **Smart Field Mapping**: Automatically maps common field names to standard invoice format
- **Data Validation**: Validates invoice data and reports issues
- **Tally XML Generation**: Creates Tally-compatible XML files for voucher import
- **Item Master Creation**: Generates item master XML for stock items
- **Flexible Output**: Generates CSV reports and multiple output formats
- **Error Handling**: Comprehensive error handling and validation

## Installation

1. **Clone or download the script:**
   ```bash
   # The script uses only built-in Python libraries
   # No additional installation required for basic functionality
   ```

2. **Optional dependencies** (for enhanced features):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
# Process a CSV file
python tally_sales_importer.py your_sales_data.csv

# Process a JSON file
python tally_sales_importer.py your_sales_data.json

# Specify output directory
python tally_sales_importer.py your_sales_data.csv -o /path/to/output

# Generate sample files for testing
python tally_sales_importer.py --sample
```

### Input File Formats

#### CSV Format
The tool supports flexible CSV formats. Common field names are automatically mapped:

```csv
invoice_number,date,party_name,party_address,party_gstin,total_amount,tax_amount,item_1_name,item_1_quantity,item_1_rate,item_1_amount
INV001,2024-01-15,ABC Company,123 Main St Mumbai,27ABCDE1234F1Z5,11800,1800,Product A,10,1000,10000
INV002,2024-01-16,XYZ Ltd,456 Park Ave Delhi,07XYZAB5678G2H9,5900,900,Product B,5,1000,5000
```

#### JSON Format
```json
[
  {
    "invoice_number": "INV001",
    "date": "2024-01-15",
    "party_name": "ABC Company",
    "party_address": "123 Main St Mumbai",
    "party_gstin": "27ABCDE1234F1Z5",
    "total_amount": "11800",
    "tax_amount": "1800",
    "items": [
      {
        "item_name": "Product A",
        "quantity": "10",
        "rate": "1000",
        "amount": "10000"
      }
    ]
  }
]
```

#### XML Format (Tally Export)
The tool can also read existing Tally XML exports and reprocess them.

### Field Mapping

The tool automatically maps various field names to standard format:

| Standard Field | Alternative Names |
|---------------|-------------------|
| invoice_number | voucher_number, bill_no, invoice_no |
| date | invoice_date, bill_date |
| party_name | customer_name, client_name, buyer_name |
| party_address | customer_address, address |
| party_gstin | customer_gstin, gstin |
| total_amount | amount, total, bill_amount |
| tax_amount | gst_amount, tax |

### Output Files

The tool generates several output files:

1. **`*_tally_import.xml`**: Main voucher import file for Tally
2. **`*_item_master.xml`**: Item master file to create stock items in Tally
3. **`*_report.csv`**: Summary report of processed invoices

## Importing into Tally

### Step 1: Import Item Master (First Time Only)
1. Open Tally ERP
2. Go to Gateway of Tally → Import Data → XML Data Import
3. Select the `*_item_master.xml` file
4. Choose "Accept All" to import all items

### Step 2: Import Vouchers
1. Go to Gateway of Tally → Import Data → XML Data Import
2. Select the `*_tally_import.xml` file
3. Review and accept the vouchers

## Data Validation

The tool performs comprehensive validation:

- **Required Fields**: Checks for invoice number, date, and party name
- **Date Formats**: Supports multiple date formats (YYYY-MM-DD, DD-MM-YYYY, etc.)
- **Amount Validation**: Ensures amounts are numeric
- **Error Reporting**: Provides detailed error messages for invalid data

## Examples

### Example 1: Processing a Simple CSV
```bash
# Generate sample data
python tally_sales_importer.py --sample

# Process the sample CSV
python tally_sales_importer.py sample_sales_data.csv
```

### Example 2: Custom Output Directory
```bash
python tally_sales_importer.py sales_data.csv -o tally_imports
```

### Example 3: Processing Multiple Files
```bash
# Process multiple files
for file in *.csv; do
    python tally_sales_importer.py "$file" -o "output_$(basename "$file" .csv)"
done
```

## Troubleshooting

### Common Issues

1. **"No data found in input file"**
   - Check file format and ensure it's not empty
   - Verify CSV delimiter (comma, semicolon, or tab)

2. **"Invalid date format"**
   - Supported formats: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, YYYY/MM/DD
   - Ensure dates are consistent throughout the file

3. **"Missing required fields"**
   - Ensure invoice_number, date, and party_name are present
   - Check field names match supported variants

4. **Import errors in Tally**
   - Ensure party names exist in Tally or create them first
   - Check that item names don't contain special characters
   - Verify GST setup if using GST fields

### Best Practices

1. **Data Preparation**:
   - Clean data before import (remove empty rows, fix date formats)
   - Ensure party names are consistent
   - Validate amounts and quantities

2. **Testing**:
   - Use sample data first to test the import process
   - Import a small batch before processing large files

3. **Backup**:
   - Always backup your Tally data before importing
   - Test imports on a copy of your data first

## Advanced Features

### Custom Field Mapping
You can modify the `_get_field_value()` method to add custom field mappings for your specific data format.

### Batch Processing
For processing multiple files, create a batch script:

```bash
#!/bin/bash
for file in data/*.csv; do
    echo "Processing $file"
    python tally_sales_importer.py "$file" -o "output/$(basename "$file" .csv)"
done
```

## File Structure

```
tally_sales_importer.py    # Main script
requirements.txt           # Dependencies (optional)
TALLY_IMPORTER_README.md  # This documentation
output/                   # Generated output files
├── *_tally_import.xml    # Voucher import files
├── *_item_master.xml     # Item master files
└── *_report.csv         # Summary reports
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your input data format matches the examples
3. Test with sample data first

## License

This tool is provided as-is for educational and business use. Please test thoroughly before using with production data.