#!/usr/bin/env python3
"""
Launcher script for Tally Prime Bulk Data Import Tool
This script checks dependencies and launches the main application
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'pandas': 'pandas',
        'openpyxl': 'openpyxl', 
        'tkinter': 'tkinter',
        'xml.etree.ElementTree': 'xml.etree.ElementTree',
        'xml.dom.minidom': 'xml.dom.minidom'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    return missing_packages

def install_dependencies(missing_packages):
    """Install missing dependencies"""
    if not missing_packages:
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
    
    try:
        # Install packages from requirements.txt if it exists
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            print("Installing from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # Install individual packages
            for package in missing_packages:
                if package == 'tkinter':
                    print("Note: tkinter is usually included with Python. If missing, install python3-tk package.")
                    continue
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print("✅ All dependencies installed successfully!")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("\nPlease install manually using:")
        print("pip install pandas openpyxl xlsxwriter lxml")
        return False

def main():
    """Main launcher function"""
    print("🚀 Tally Prime Bulk Data Import Tool Launcher")
    print("=" * 50)
    
    # Check Python version
    print("\n🐍 Checking Python version...")
    if not check_python_version():
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        
        install_choice = input("\nWould you like to install missing packages? (y/n): ").lower().strip()
        if install_choice in ['y', 'yes']:
            if not install_dependencies(missing_packages):
                return
        else:
            print("Please install the missing packages manually and try again.")
            return
    
    # Launch the main application
    print("\n🎯 Launching Tally Prime Bulk Import Tool...")
    
    try:
        from tally_bulk_importer import TallyBulkImporter
        app = TallyBulkImporter()
        app.run()
    except ImportError as e:
        print(f"❌ Error importing main application: {e}")
        print("Make sure tally_bulk_importer.py is in the same directory")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        print("Check the error message above and try again")

if __name__ == "__main__":
    main()