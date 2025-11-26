"""
Parameter Mapper Utility for Family Profile Updater
Handles flexible parameter mapping between CSV columns and Revit family parameters with unit conversion support
"""

import csv
import json
import os
from collections import OrderedDict
from unit_converter import UnitConverter

class ParameterMapper:
    """Handles parameter mapping between CSV columns and Revit family parameters with unit conversion"""
    
    def __init__(self, mapping_file_path):
        """Initialize with mapping file"""
        self.mapping_file_path = mapping_file_path
        self.mappings = {}
        self.unit_converter = UnitConverter()
        self.load_mappings()
    
    def load_mappings(self):
        """Load parameter mappings from JSON file"""
        if os.path.exists(self.mapping_file_path):
            try:
                with open(self.mapping_file_path, 'r') as f:
                    self.mappings = json.load(f)
                print("Loaded parameter mappings from {}".format(self.mapping_file_path))
            except Exception as e:
                print("Error loading mappings: {}".format(e))
                self.mappings = {}
        else:
            print("No existing mappings found. Creating new mapping file.")
            self.mappings = {}
    
    def save_mappings(self):
        """Save parameter mappings to config file"""
        try:
            with open(self.mapping_file_path, 'w') as f:
                json.dump(self.mappings, f, indent=2, sort_keys=True)
            print("Saved parameter mappings to {}".format(self.mapping_file_path))
        except Exception as e:
            print("Error saving mappings: {}".format(e))
    
    def get_profile_mappings(self, profile_type):
        """Get parameter mappings for specific profile type"""
        return self.mappings.get('profiles', {}).get(profile_type, {})
    
    def get_all_mappings(self):
        """Get all parameter mappings"""
        return self.mappings
    
    def parse_parameter_with_conversion(self, csv_value, parameter_key):
        """
        Parse parameter key and convert value based on unit type
        
        Args:
            csv_value (str): Value from CSV file
            parameter_key (str): Parameter key in format "UNIT_TYPE:parameter_name"
            
        Returns:
            tuple: (converted_value, revit_parameter_name, unit_type)
        """
        unit_type, param_name = self.unit_converter.parse_parameter_key(parameter_key)
        
        try:
            # Convert string to float
            value = float(csv_value)
            
            # Convert based on unit type
            converted_value = self.unit_converter.convert_value(value, unit_type)
            
            return converted_value, param_name, unit_type
            
        except (ValueError, TypeError):
            # Return original value if conversion fails
            return csv_value, param_name, unit_type
    
    def get_parameter_info(self, profile_type, csv_header):
        """Get parameter info including unit type and Revit parameter name"""
        profile_mappings = self.get_profile_mappings(profile_type)
        
        if csv_header in profile_mappings:
            parameter_key = profile_mappings[csv_header]
            unit_type, param_name = self.unit_converter.parse_parameter_key(parameter_key)
            
            return {
                'revit_parameter': param_name,
                'unit_type': unit_type,
                'unit_label': self.unit_converter.get_unit_label(unit_type),
                'parameter_key': parameter_key
            }
        
        # Fallback to no conversion if no mapping found
        return {
            'revit_parameter': csv_header,
            'unit_type': 'NONE',
            'unit_label': '',
            'parameter_key': csv_header
        }
    
    def validate_mappings(self, profile_type, csv_headers):
        """Validate that all CSV headers have valid mappings"""
        profile_mappings = self.get_profile_mappings(profile_type)
        missing_mappings = []
        
        for header in csv_headers:
            if header not in profile_mappings:
                missing_mappings.append(header)
        
        if missing_mappings:
            print("Warning: Missing mappings for: {}".format(", ".join(missing_mappings)))
        
        return len(missing_mappings) == 0
    
    def get_conversion_summary(self, profile_type):
        """Get summary of unit conversions for a profile type"""
        profile_mappings = self.get_profile_mappings(profile_type)
        summary = {}
        
        for csv_header, parameter_key in profile_mappings.items():
            unit_type, param_name = self.unit_converter.parse_parameter_key(parameter_key)
            summary[csv_header] = {
                'unit_type': unit_type,
                'factor': self.unit_converter.CONVERSION_FACTORS.get(unit_type, 1.0),
                'revit_parameter': param_name
            }
        
        return summary
    
    def get_mapped_parameter(self, csv_column_name, profile_type=None):
        """
        Get the mapped Revit parameter name for a given CSV column name
        
        Args:
            csv_column_name (str): The CSV column header name
            profile_type (str): Optional profile type to narrow search
            
        Returns:
            str: The corresponding Revit parameter name, or the original column name if no mapping exists
        """
        # First, try to find mapping in the loaded mappings
        if profile_type and profile_type in self.mappings.get('profiles', {}):
            profile_mappings = self.mappings['profiles'][profile_type]
            if csv_column_name in profile_mappings:
                parameter_key = profile_mappings[csv_column_name]
                unit_type, param_name = self.unit_converter.parse_parameter_key(parameter_key)
                return param_name
        
        # If no profile type specified or no specific mapping found, check all profiles
        for profile_type_key, profile_mappings in self.mappings.get('profiles', {}).items():
            if csv_column_name in profile_mappings:
                parameter_key = profile_mappings[csv_column_name]
                unit_type, param_name = self.unit_converter.parse_parameter_key(parameter_key)
                return param_name
        
        # Return the original column name if no mapping found
        return csv_column_name
    
    def create_mapping_interactive(self, csv_file=None, doc=None):
        """
        Interactive method to create parameter mappings for CSV columns
        
        Args:
            csv_file (str): Path to the CSV file
            doc: Revit document (optional)
            
        Returns:
            bool: True if mapping was created successfully, False otherwise
        """
        try:
            if not csv_file or not os.path.exists(csv_file):
                print("Error: CSV file not provided or doesn't exist")
                return False
            
            # Read CSV headers
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
            
            if not headers:
                print("Error: No headers found in CSV file")
                return False
            
            print("\n" + "="*60)
            print("Creating parameter mappings")
            print("="*60)
            print("CSV Headers found:")
            for i, header in enumerate(headers, 1):
                print("  {}. {}".format(i, header))
            print()
            
            # Create mappings for each header
            profile_type = os.path.splitext(os.path.basename(csv_file))[0]
            
            if profile_type not in self.mappings.get('profiles', {}):
                self.mappings.setdefault('profiles', {})[profile_type] = {}
            
            for header in headers:
                if header.lower() == 'name':
                    continue  # Skip 'Name' column as it's used for type names
                    
                # Suggest a parameter name based on the header
                suggested_param = self.get_mapped_parameter(header)
                
                # For now, use the suggested parameter with LENGTH prefix as default
                parameter_key = "LENGTH:{}".format(suggested_param)
                
                # Allow user to modify if running interactively
                print("Mapping: '{}' -> '{}'".format(header, parameter_key))
                
                self.mappings['profiles'][profile_type][header] = parameter_key
            
            # Save the mappings
            self.save_mappings()
            print("\nParameter mappings created successfully!")
            return True
            
        except Exception as e:
            print("Error creating parameter mappings: {}".format(str(e)))
            return False
    
    def get_csv_headers(self, csv_file):
        """Get headers from CSV file"""
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                return reader.fieldnames or []
        except Exception as e:
            print("Error reading CSV headers: {}".format(str(e)))
            return []