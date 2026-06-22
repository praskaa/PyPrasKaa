# -*- coding: utf-8 -*-
"""
Debug helper script to test parameter value assignment
This script creates a sample CSV file and tests the parameter mapping process
"""

import os
import csv
import json

# Create sample CSV data for testing
SAMPLE_CSV_DATA = [
    {
        "Name": "L50x50x5",
        "b": "50",
        "t": "5",
        "h": "50",
        "Weight": "3.77",
        "Area": "4.80",
        "Iy": "11.40",
        "Iz": "11.40"
    },
    {
        "Name": "L60x60x6",
        "b": "60",
        "t": "6",
        "h": "60",
        "Weight": "5.42",
        "Area": "6.91",
        "Iy": "19.90",
        "Iz": "19.90"
    }
]

def create_sample_csv():
    """Create a sample CSV file for testing"""
    csv_path = os.path.join(os.path.dirname(__file__), "sample_angle_profiles.csv")
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ["Name", "b", "t", "h", "Weight", "Area", "Iy", "Iz"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in SAMPLE_CSV_DATA:
            writer.writerow(row)
    
    print("✅ Sample CSV created: {}".format(csv_path))
    return csv_path

def debug_parameter_mapping():
    """Debug the parameter mapping process"""
    from parameter_mapper import ParameterMapper
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file_path = os.path.join(script_dir, 'parameter_mappings.json')
    
    # Load current mappings
    with open(mapping_file_path, 'r') as f:
        mappings = json.load(f)
    
    print("\n🔍 DEBUG: Current parameter mappings")
    print("=" * 50)
    
    for csv_file, mapping in mappings.items():
        print("\n📁 CSV File: {}".format(csv_file))
        for csv_col, revit_param in mapping.items():
            print("   {} -> {}".format(csv_col, revit_param))

if __name__ == "__main__":
    create_sample_csv()
    debug_parameter_mapping()