#!/usr/bin/env python3
"""
Demo Script for Tally Excel Sales Data Importer
Demonstrates different usage scenarios with Excel files
"""

import os
from tally_excel_importer import TallyExcelImporter

def demo_excel_processing():
    """Demonstrate Excel processing capabilities"""
    
    print("🎯 Tally Excel Sales Data Importer - Demo")
    print("=" * 50)
    
    # Initialize importer
    importer = TallyExcelImporter()
    
    # Check if sample Excel file exists
    if not os.path.exists('sample_sales_data.xlsx'):
        print("📊 Generating sample Excel file...")
        from tally_excel_importer import generate_sample_excel
        generate_sample_excel()
        print()
    
    print("🔍 Demo 1: List Excel Sheets")
    print("-" * 30)
    sheets = importer.list_excel_sheets('sample_sales_data.xlsx')
    for i, sheet in enumerate(sheets, 1):
        print(f"  {i}. {sheet}")
    print()
    
    print("📈 Demo 2: Process Detailed Sales Data")
    print("-" * 40)
    importer.process_excel_file('sample_sales_data.xlsx', 'demo_output_detailed', 'Sales Data')
    print()
    
    print("📊 Demo 3: Process Simple Format")
    print("-" * 35)
    importer.process_excel_file('sample_sales_data.xlsx', 'demo_output_simple', 'Simple Format')
    print()
    
    print("📋 Demo 4: Show Generated Files")
    print("-" * 32)
    
    # Show what was generated
    for output_dir in ['demo_output_detailed', 'demo_output_simple']:
        if os.path.exists(output_dir):
            print(f"\n📁 Files in {output_dir}:")
            files = os.listdir(output_dir)
            for file in sorted(files):
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"   • {file} ({size:,} bytes)")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed successfully!")
    print("\n🎯 Key Benefits of Excel-Based Approach:")
    print("   • No API dependencies - works offline")
    print("   • Direct Excel file processing")
    print("   • Smart column detection and mapping")  
    print("   • Multiple items per invoice support")
    print("   • Comprehensive Excel reports")
    print("   • Ready-to-import Tally XML files")
    
    print("\n🚀 Next Steps:")
    print("   1. Review generated XML files")
    print("   2. Import item master XML into Tally first")
    print("   3. Import sales voucher XML into Tally")
    print("   4. Check Excel reports for any validation issues")

def create_custom_excel_demo():
    """Create a custom Excel file to demonstrate flexibility"""
    try:
        import pandas as pd
        
        print("\n📝 Creating Custom Excel Demo...")
        
        # Custom format with different column names
        custom_data = [
            {
                'Bill_No': 'CUSTOM001',
                'Bill_Date': '2024-01-25',
                'Customer_Name': 'Demo Customer Ltd',
                'Customer_Address': '999 Demo Street, Test City',
                'GSTIN': '27DEMO1234G1Z5',
                'Bill_Amount': 25000,
                'GST_Amount': 4500,
                'Product_1_Name': 'Demo Product X',
                'Product_1_Qty': 25,
                'Product_1_Price': 800,
                'Product_1_Value': 20000,
                'Product_2_Name': 'Demo Product Y',
                'Product_2_Qty': 10,
                'Product_2_Price': 500,
                'Product_2_Value': 5000,
                'Notes': 'Custom format demo'
            },
            {
                'Bill_No': 'CUSTOM002',
                'Bill_Date': '2024-01-26', 
                'Customer_Name': 'Another Demo Corp',
                'Customer_Address': '888 Another St, Demo Town',
                'GSTIN': '07DEMO5678H2I9',
                'Bill_Amount': 15000,
                'GST_Amount': 2700,
                'Product_1_Name': 'Demo Product Z',
                'Product_1_Qty': 15,
                'Product_1_Price': 800,
                'Product_1_Value': 12000,
                'Product_2_Name': '',
                'Product_2_Qty': '',
                'Product_2_Price': '',
                'Product_2_Value': '',
                'Notes': 'Single item demo'
            }
        ]
        
        # Create Excel file
        df = pd.DataFrame(custom_data)
        df.to_excel('custom_demo_sales.xlsx', sheet_name='Custom Format', index=False)
        
        print("✅ Custom Excel file created: custom_demo_sales.xlsx")
        
        # Process it
        print("\n🔄 Processing custom format...")
        importer = TallyExcelImporter()
        importer.process_excel_file('custom_demo_sales.xlsx', 'demo_output_custom')
        
        print("✅ Custom format processed successfully!")
        
    except ImportError:
        print("⚠️  pandas not available for custom demo")

if __name__ == "__main__":
    demo_excel_processing()
    create_custom_excel_demo()