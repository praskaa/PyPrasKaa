# -*- coding: utf-8 -*-
"""
Enhanced pyRevit Tool for Batch Creating Revit Family Types from CSV
Supports multiple profile types with sophisticated UI and console fallback
"""

__title__ = "Update Family Profiles"
__author__ = "PrasKaa"
__doc__ = """Batch create/update Revit family types from CSV data with enhanced UI"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')

from System.Windows.Forms import OpenFileDialog, DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon
from System.Drawing import Color
import os
import csv
import json
from collections import OrderedDict
import sys
import os

# Import pyRevit modules
from pyrevit import forms
from pyrevit import script
from pyrevit import revit, DB
from pyrevit.revit import doc, uidoc

# Import parameter mapper and unit converter
from parameter_mapper import ParameterMapper
from unit_converter import UnitConverter

# Import specific Revit classes
from Autodesk.Revit.DB import (
    Transaction, TransactionGroup, FilteredElementCollector,
    ElementId, BuiltInParameter, UnitTypeId,
    ForgeTypeId, UnitUtils, FamilySymbol, FamilyManager,
    FamilyType
)

# Profile configurations (DEPRECATED - now handled by parameter_mapper.py)
PROFILE_CONFIGS = {}

def get_family_document():
    """Get the current family document"""
    if doc.IsFamilyDocument:
        return doc
    else:
        forms.alert("Please open a family document to use this tool.")
        return None

def create_family_type(family_doc, type_name, parameters, parameter_mappings=None):
    """Create a new family type with given parameters, with robust error handling and unit conversion."""
    
    try:
        family_manager = family_doc.FamilyManager
        unit_converter = UnitConverter()
        
        # Debug: Print all parameters being processed
        print("\n🔍 DEBUG: Processing parameters for type '{}'".format(type_name))
        print("   Parameters to set: {}".format(parameters))
        
        # Ensure type_name is a string before passing to Revit API
        safe_type_name = str(type_name)
        
        # Check if type already exists
        existing_types = [ft.Name for ft in family_manager.Types]
        if safe_type_name in existing_types:
            return {"success": False, "message": "Type '{}' already exists".format(safe_type_name)}
        
        # Create new type with the safe string name
        new_type = family_manager.NewType(safe_type_name)

        # Set the new type as the current one before changing parameters
        family_manager.CurrentType = new_type
        
        # Debug: Print all available parameters in the family
        print("🔍 DEBUG: Available parameters in family:")
        for param in family_manager.Parameters:
            print("   - {} (Type: {})".format(param.Definition.Name, param.StorageType))
        
        # Set parameters
        for param_name, param_info in parameters.items():
            if param_info:
                # Handle both old format (direct value) and new format (with unit info)
                if isinstance(param_info, dict):
                    param_value = param_info.get('value')
                    unit_type = param_info.get('unit_type', 'LENGTH')
                else:
                    param_value = param_info
                    unit_type = 'LENGTH'  # Default to LENGTH for backward compatibility
                
                # Ensure param_name is a string
                safe_param_name = str(param_name)
                
                param = family_manager.get_Parameter(safe_param_name)
                
                print("🔍 DEBUG: Processing parameter '{}' with value '{}' (unit_type: {})".format(
                    safe_param_name, param_value, unit_type))
                
                if param:
                    print("   ✅ Parameter found: {} (StorageType: {})".format(safe_param_name, param.StorageType))
                    try:
                        value_str = str(param_value).strip()
                        
                        # Check parameter type and handle accordingly
                        if param.StorageType == DB.StorageType.Double:
                            # Convert value using unit converter
                            numeric_value = float(value_str)
                            converted_value = unit_converter.convert_value(numeric_value, unit_type)
                            
                            print("   📊 DEBUG: Converting {} {} to {} (Revit internal units)".format(
                                numeric_value, unit_type, converted_value))
                            
                            family_manager.Set(param, converted_value)
                            print("   ✅ Successfully set parameter '{}' to {}".format(safe_param_name, converted_value))
                            
                        elif param.StorageType == DB.StorageType.Integer:
                            int_value = int(float(value_str))
                            family_manager.Set(param, int_value)
                            print("   ✅ Successfully set parameter '{}' to {}".format(safe_param_name, int_value))
                            
                        elif param.StorageType == DB.StorageType.String:
                            family_manager.Set(param, value_str)
                            print("   ✅ Successfully set parameter '{}' to {}".format(safe_param_name, value_str))
                        else:
                            print("   ⚠️ Unsupported parameter type: {}".format(param.StorageType))

                    except ValueError as ve:
                        print("⚠️ Could not convert value '{}' to number for parameter '{}': {}".format(
                            param_value, safe_param_name, str(ve)))
                    except Exception as e_set:
                        print("⚠️ Error setting parameter '{}': {}".format(safe_param_name, str(e_set)))
                else:
                    print("   ❌ Parameter '{}' not found in family".format(safe_param_name))
        
        return {"success": True, "message": "Type '{}' created successfully".format(type_name)}
        
    except Exception as e:
        import traceback
        print("--- ERROR in create_family_type ---")
        print("Error message: {}".format(str(e)))
        print("Error type: {}".format(type(e)))
        print("Traceback:")
        traceback.print_exc()
        print("------------------------------------")
        return {"success": False, "message": "Error processing type '{}': {}".format(type_name, str(e))}

def process_csv_file(csv_path):
    """Process CSV file and create family types with parameter mapping"""
    family_doc = get_family_document()
    if not family_doc:
        return
    
    # Initialize parameter mapper with correct path to parameter_mappings.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file_path = os.path.join(script_dir, 'parameter_mappings.json')
    mapper = ParameterMapper(mapping_file_path)
    
    # Check if mappings exist
    if not mapper.get_all_mappings():
        print("\n" + "="*60)
        print("🔧 PARAMETER MAPPING REQUIRED")
        print("="*60)
        print("No parameter mappings found. Would you like to create them now?")
        
        response = forms.alert(
            "No parameter mappings found for this CSV file.\n\n"
            "Would you like to create parameter mappings now?\n\n"
            "This will help map CSV column names to actual Revit family parameters.",
            options=["Yes, create mappings", "No, use default mapping", "Cancel"]
        )
        
        if response == "Yes, create mappings":
            if not mapper.create_mapping_interactive(csv_file=csv_path, doc=family_doc):
                print("❌ Parameter mapping cancelled.")
                return
        elif response == "Cancel":
            return
    
    # Process CSV
    results = []
    processed = 0
    success_count = 0
    errors = 0
    
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            total_rows = len(rows)
            
            print("\n" + "="*60)
            print("⚙️ Processing profiles...")
            print("="*60)

            # Wrap the entire process in a single transaction for efficiency
            with revit.Transaction("Create Family Types from CSV"):
                
                for i, row in enumerate(rows):
                    try:
                        print("\n🔍 DEBUG: Processing row {}: {}".format(i+1, row))
                        
                        # Get profile type from CSV filename
                        csv_filename = os.path.basename(csv_path)
                        profile_type = os.path.splitext(csv_filename)[0]  # e.g., "ANGLE_profiles"
                        
                        print("🔍 DEBUG: Profile type: '{}'".format(profile_type))
                        
                        # Map CSV columns to parameters using the mapper with unit conversion
                        mapped_parameters = {}
                        for csv_col, value in row.items():
                            if csv_col.lower() != 'name' and value and value.strip():
                                # Get parameter mapping info including unit type
                                parameter_info = mapper.get_parameter_info(profile_type, csv_col)
                                revit_param = parameter_info['revit_parameter']
                                unit_type = parameter_info['unit_type']
                                
                                print("🔍 DEBUG: CSV column '{}' -> Revit parameter '{}' (unit: {}) = '{}'".format(
                                    csv_col, revit_param, unit_type, value))
                                
                                if revit_param and revit_param != csv_col:  # Only use if mapping was found
                                    mapped_parameters[revit_param] = {
                                        'value': value,
                                        'unit_type': unit_type
                                    }
                        
                        print("🔍 DEBUG: Final mapped parameters: {}".format(mapped_parameters))
                        
                        # Create type name
                        type_name = row.get("Name", "Type{}".format(i+1))
                        print("🔍 DEBUG: Creating type: '{}'".format(type_name))
                        
                        # Create family type with mapped parameters
                        result = create_family_type(family_doc, type_name, mapped_parameters)
                        results.append(result)
                        
                        if result["success"]:
                            success_count += 1
                            print("✅ {}".format(result["message"]))
                        else:
                            errors += 1
                            print("❌ {}".format(result["message"]))
                        
                        processed += 1
                        
                    except Exception as ex:
                        errors += 1
                        print("❌ Row {}: {}".format(i+1, str(ex)))
             
            # Summary
            print("\n" + "="*60)
            print("📊 PROCESSING SUMMARY")
            print("="*60)
            print("✅ Total Processed: {}".format(processed))
            print("✅ Successful: {}".format(success_count))
            print("⚠️ Errors: {}".format(errors))
            
            if errors > 0:
                print("\n⚠️ Some types failed to create. Check the messages above.")
            
            forms.alert(
                "Processing complete!\n\nTotal processed: {}\nSuccessful: {}\nErrors: {}\nSuccess rate: {:.1f}%".format(
                    processed, success_count, errors, (success_count/processed*100) if processed > 0 else 0
                ),
                title="Processing Complete"
            )
            
    except Exception as e:
        print("❌ Processing failed: {}".format(str(e)))
        forms.alert(
            "Processing failed: {}".format(str(e)),
            title="Error"
        )

def main():
    """Main execution function for pyRevit button"""
    print("\n" + "="*60)
    print("🚀 FAMILY PROFILE UPDATER - STARTING...")
    print("="*60)
    
    try:
        # Get family document
        family_doc = get_family_document()
        if not family_doc:
            print("❌ No family document found. Please open a family file.")
            return
            
        print("✅ Family document loaded: {}".format(family_doc.Title))
        
        # File selection dialog
        file_dialog = OpenFileDialog()
        file_dialog.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
        file_dialog.Title = "Select CSV file"
        
        if file_dialog.ShowDialog() == DialogResult.OK:
            csv_path = file_dialog.FileName
            print("✅ Selected CSV file: {}".format(csv_path))
            
            # Process the CSV file
            process_csv_file(csv_path)
            
        else:
            print("❌ No CSV file selected.")
            
    except Exception as e:
        print("❌ Unexpected error in main(): {}".format(str(e)))
        import traceback
        traceback.print_exc()
        forms.alert("Error: {}".format(str(e)), title="Script Error")

# This is the entry point that pyRevit will call when button is pressed
if __name__ == '__main__':
    main()