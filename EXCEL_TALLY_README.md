# Tally Excel Sales Data Importer

🎯 **A powerful, Excel-focused tool to import sales data into Tally ERP - No API required!**

Works directly with Excel files (.xlsx, .xls) and generates Tally-compatible XML files for seamless import.

## ✨ Key Features

- **📊 Excel-Only Solution**: Works directly with Excel files - no web APIs or external services needed
- **🔄 Multi-Sheet Support**: Process different sheets with different formats
- **🧠 Smart Field Detection**: Automatically detects and maps column names to Tally fields
- **📦 Multiple Item Support**: Handles multiple items per invoice (Item_1_Name, Item_2_Name, etc.)
- **✅ Data Validation**: Comprehensive validation with detailed error reporting
- **📈 Excel Reports**: Generates detailed Excel reports with multiple sheets
- **🎨 Pretty XML Output**: Well-formatted, readable XML files for Tally import

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install pandas openpyxl xlrd
```

### 2. Generate Sample Excel File
```bash
python3 tally_excel_importer.py --sample
```

### 3. Process Your Excel File
```bash
python3 tally_excel_importer.py your_sales_data.xlsx
```

## 📋 Excel Format Guidelines

### Basic Invoice Format (Minimum Required)
| Column Name | Description | Example |
|-------------|-------------|---------|
| Invoice Number | Invoice/Bill number | INV001 |
| Date | Invoice date | 2024-01-15 |
| Party Name | Customer name | ABC Company |
| Total Amount | Invoice total | 11800 |

### Detailed Format with Items
| Column | Description | Example |
|--------|-------------|---------|
| Invoice Number | Invoice/Bill number | INV001 |
| Date | Invoice date | 2024-01-15 |
| Party Name | Customer name | ABC Company |
| Party Address | Customer address | 123 Main St, Mumbai |
| Party GSTIN | GST number | 27ABCDE1234F1Z5 |
| Total Amount | Invoice total | 11800 |
| Tax Amount | Tax/GST amount | 1800 |
| Item_1_Name | First item name | Product A |
| Item_1_Quantity | First item quantity | 10 |
| Item_1_Rate | First item rate | 1000 |
| Item_1_Amount | First item amount | 10000 |
| Item_2_Name | Second item name | Product B |
| Item_2_Quantity | Second item quantity | 1 |
| Item_2_Rate | Second item rate | 1000 |
| Item_2_Amount | Second item amount | 1000 |
| Remarks | Notes/Description | Sample invoice |

### 🔄 Alternative Column Names (Auto-Detected)

The tool automatically recognizes these variations:

| Standard Field | Alternative Names |
|---------------|-------------------|
| Invoice Number | Invoice, Bill, Voucher, Inv_No, Bill_No |
| Date | Date, Inv_Date, Bill_Date |
| Party Name | Party, Customer, Client, Buyer, Name |
| Party Address | Address, Add |
| Party GSTIN | GSTIN, GST_No, TIN |
| Total Amount | Total_Amount, Total, Amount, Value, Sum |
| Tax Amount | Tax_Amount, Tax, GST_Amount, GST, VAT |

## 🎯 Usage Examples

### Process Specific Sheet
```bash
python3 tally_excel_importer.py data.xlsx --sheet "Sales Data"
```

### Custom Output Directory
```bash
python3 tally_excel_importer.py data.xlsx -o custom_output
```

### List All Sheets
```bash
python3 tally_excel_importer.py data.xlsx --list-sheets
```

### Process Multiple Formats
```bash
# Detailed format with items
python3 tally_excel_importer.py sales_detailed.xlsx

# Simple format (auto-creates single item per invoice)
python3 tally_excel_importer.py sales_simple.xlsx --sheet "Simple"
```

## 📊 Excel File Preparation Tips

### 1. Column Headers
- Use the first row for column headers
- Column names are case-insensitive
- Use consistent naming throughout the file

### 2. Data Format
- **Dates**: Use Excel date format or YYYY-MM-DD, DD-MM-YYYY
- **Numbers**: Use numeric format (commas are automatically removed)
- **Text**: Keep party names consistent (they become ledger names in Tally)

### 3. Multiple Items Per Invoice
- Use pattern: `Item_1_Name`, `Item_1_Quantity`, `Item_1_Rate`, `Item_1_Amount`
- Continue with `Item_2_Name`, `Item_2_Quantity`, etc.
- Leave empty cells for unused item columns

### 4. Multiple Sheets
- Different sheets can have different formats
- Specify sheet name with `--sheet` parameter
- First sheet is used by default

## 📁 Output Files

The tool generates three types of files:

### 1. `*_tally_import.xml`
**Main file for Tally import**
- Contains all sales vouchers
- Import this into Tally after importing items

### 2. `*_item_master.xml`
**Item master for stock items**
- Contains all unique items found in invoices
- Import this FIRST into Tally to create stock items

### 3. `*_report.xlsx`
**Detailed Excel report with multiple sheets:**
- **Invoice Summary**: Overview of all processed invoices
- **Item Details**: Line-by-line item breakdown
- **Validation Errors**: Any issues found during processing

## 🔧 Importing into Tally ERP

### Step 1: Import Item Master (First Time Only)
1. Open Tally ERP
2. Go to **Gateway of Tally → Import Data → XML Data Import**
3. Select the `*_item_master.xml` file
4. Choose **"Accept All"** to import all items
5. Verify items are created in **Masters → Inventory Info → Stock Items**

### Step 2: Import Sales Vouchers
1. Go to **Gateway of Tally → Import Data → XML Data Import**
2. Select the `*_tally_import.xml` file
3. Review the vouchers in the preview
4. Choose **"Accept All"** to import vouchers
5. Verify vouchers in **Display → Account Books → Sales Register**

## 🛠️ Advanced Features

### Programmatic Usage
```python
from tally_excel_importer import TallyExcelImporter

# Initialize importer
importer = TallyExcelImporter()

# Process Excel file
importer.process_excel_file('sales_data.xlsx', 'output_folder')

# Access processed data
for invoice in importer.invoices:
    print(f"Invoice: {invoice['invoice_number']}")
```

### Batch Processing
```bash
# Process multiple Excel files
for file in *.xlsx; do
    echo "Processing $file"
    python3 tally_excel_importer.py "$file" -o "output_$(basename "$file" .xlsx)"
done
```

## ⚠️ Troubleshooting

### Common Issues

1. **"No data found in Excel file"**
   - Check if the Excel file has data in the first sheet
   - Ensure column headers are in the first row
   - Try specifying a different sheet with `--sheet`

2. **"Missing invoice number or party name"**
   - Ensure these columns exist and have data
   - Check column names match supported variants
   - Look for empty rows mixed with data

3. **"Invalid or zero total amount"**
   - Check amount columns contain numeric values
   - Remove currency symbols if any (₹, $, etc.)
   - Ensure amounts are positive numbers

4. **Import errors in Tally**
   - Import item master XML first
   - Ensure party names don't contain special characters
   - Check that item names are consistent
   - Verify date formats are valid

### Best Practices

1. **Data Cleanup**
   - Remove completely empty rows
   - Ensure consistent party naming
   - Validate amounts are numeric
   - Check date formats

2. **Testing**
   - Use sample data first: `python3 tally_excel_importer.py --sample`
   - Process a small batch before bulk import
   - Review the Excel report for validation errors

3. **Backup**
   - Always backup Tally data before importing
   - Test on a copy of your Tally company first

## 📝 Excel Template

Here's a template you can copy to Excel:

| Invoice Number | Date | Party Name | Party Address | Party GSTIN | Total Amount | Tax Amount | Item_1_Name | Item_1_Quantity | Item_1_Rate | Item_1_Amount | Remarks |
|----------------|------|------------|---------------|-------------|--------------|------------|-------------|-----------------|-------------|---------------|---------|
| INV001 | 2024-01-15 | ABC Company | 123 Main St | 27ABC1234F1 | 11800 | 1800 | Product A | 10 | 1000 | 10000 | Sample |
| INV002 | 2024-01-16 | XYZ Ltd | 456 Park Ave | 07XYZ5678G2 | 5900 | 900 | Product B | 5 | 1000 | 5000 | Test |

## 🔍 Data Validation

The tool performs comprehensive validation:

- ✅ Required fields (Invoice Number, Party Name)
- ✅ Date format validation
- ✅ Numeric amount validation
- ✅ Item name validation
- ✅ Data consistency checks

All validation errors are reported in the Excel report for easy review and correction.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the sample Excel file format
3. Check the validation errors in the generated Excel report
4. Ensure your Excel file follows the format guidelines

## 📜 License

This tool is provided for business use with Excel files. Test thoroughly before using with production data.

---

🎉 **Ready to get started?** Run `python3 tally_excel_importer.py --sample` to generate a sample Excel file and see the tool in action!