#!/usr/bin/env python3
"""
Usage Example for Tally Sales Data Importer
This script demonstrates how to use the TallySalesImporter class programmatically
"""

from tally_sales_importer import TallySalesImporter
import json

# Example 1: Processing data programmatically
def example_programmatic_usage():
    print("=== Example 1: Programmatic Usage ===")
    
    # Create sample data
    sample_data = [
        {
            "invoice_number": "INV100",
            "date": "2024-01-20",
            "party_name": "Sample Customer Ltd",
            "party_address": "123 Business Street, Mumbai",
            "party_gstin": "27SAMPLE1234G1Z5",
            "total_amount": "11800",
            "tax_amount": "1800",
            "items": [
                {
                    "item_name": "Widget A",
                    "quantity": "5",
                    "rate": "2000",
                    "amount": "10000"
                },
                {
                    "item_name": "Widget B", 
                    "quantity": "2",
                    "rate": "500",
                    "amount": "1000"
                }
            ]
        }
    ]
    
    # Initialize the importer
    importer = TallySalesImporter()
    
    # Normalize and validate the data
    normalized_invoices = importer.normalize_data(sample_data)
    valid_invoices = importer.validate_invoices(normalized_invoices)
    
    # Generate output files
    if valid_invoices:
        importer.generate_tally_xml(valid_invoices, "example_tally_import.xml")
        importer.generate_item_master(valid_invoices, "example_item_master.xml")
        importer.generate_csv_report(valid_invoices, "example_report.csv")
        print(f"Generated files for {len(valid_invoices)} invoices")

# Example 2: Creating custom data format
def example_custom_format():
    print("\n=== Example 2: Custom Data Format ===")
    
    # Example of custom field names that the tool will map automatically
    custom_data = [
        {
            "bill_no": "BILL001",  # Maps to invoice_number
            "bill_date": "2024-01-21",  # Maps to date
            "customer_name": "Custom Corp",  # Maps to party_name
            "customer_address": "456 Custom Ave, Delhi",  # Maps to party_address
            "gstin": "07CUSTOM5678H2I9",  # Maps to party_gstin
            "bill_amount": "5900",  # Maps to total_amount
            "gst_amount": "900",  # Maps to tax_amount
            "item_1_name": "Custom Product",
            "item_1_quantity": "3",
            "item_1_rate": "1500",
            "item_1_amount": "4500"
        }
    ]
    
    importer = TallySalesImporter()
    normalized_invoices = importer.normalize_data(custom_data)
    
    print("Original data field names:")
    for key in custom_data[0].keys():
        print(f"  - {key}")
    
    print("\nNormalized invoice fields:")
    for key, value in normalized_invoices[0].items():
        if value:  # Only show fields with values
            print(f"  - {key}: {value}")

# Example 3: Batch processing
def example_batch_processing():
    print("\n=== Example 3: Batch Processing ===")
    
    # Simulate multiple data sources
    batch_data = [
        {
            "invoice_number": "BATCH001",
            "date": "2024-01-22",
            "party_name": "Batch Customer 1",
            "total_amount": "10000",
            "item_1_name": "Batch Product 1",
            "item_1_quantity": "10",
            "item_1_rate": "1000",
            "item_1_amount": "10000"
        },
        {
            "invoice_number": "BATCH002", 
            "date": "2024-01-23",
            "party_name": "Batch Customer 2",
            "total_amount": "15000",
            "item_1_name": "Batch Product 2",
            "item_1_quantity": "15",
            "item_1_rate": "1000", 
            "item_1_amount": "15000"
        }
    ]
    
    importer = TallySalesImporter()
    
    # Process in batch
    all_invoices = []
    for data_source in [batch_data]:  # You could have multiple data sources
        normalized = importer.normalize_data(data_source)
        validated = importer.validate_invoices(normalized)
        all_invoices.extend(validated)
    
    print(f"Processed {len(all_invoices)} invoices in batch")
    
    # Generate combined output
    if all_invoices:
        importer.generate_tally_xml(all_invoices, "batch_tally_import.xml")
        importer.generate_csv_report(all_invoices, "batch_report.csv")

if __name__ == "__main__":
    print("Tally Sales Data Importer - Usage Examples")
    print("=" * 50)
    
    try:
        example_programmatic_usage()
        example_custom_format()
        example_batch_processing()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("Check the generated files:")
        print("  - example_tally_import.xml")
        print("  - example_item_master.xml") 
        print("  - example_report.csv")
        print("  - batch_tally_import.xml")
        print("  - batch_report.csv")
        
    except Exception as e:
        print(f"Error running examples: {e}")