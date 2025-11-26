# -*- coding: utf-8 -*-
"""
Inspect Area Reinforcement Parameters
Debug script to check available parameters on Area Reinforcement instances
"""

__title__ = "Inspect AR\nParameters"
__author__ = "PrasKaaPyKit"

import sys
import os

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB.Structure import AreaReinforcement
import clr
clr.AddReference('System')
from System.Collections.Generic import List

# Import pyRevit forms
from pyrevit import forms, script

# Add lib folder to path
script_dir = os.path.dirname(__file__)
lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

# Akses dokumen Revit
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application

def inspect_area_reinforcement_parameters():
    """Inspect parameters available on Area Reinforcement instances"""

    output = script.get_output()

    # Step 1: Get Area Reinforcement selection
    selection = uidoc.Selection.GetElementIds()
    if selection.Count == 0:
        forms.alert("Please select an Area Reinforcement element first!")
        return

    area_reinf = doc.GetElement(selection[0])
    if not isinstance(area_reinf, AreaReinforcement):
        forms.alert("Selected element is not an Area Reinforcement!")
        return

    output.print_md("## 🔍 **Area Reinforcement Parameter Inspection**")
    output.print_md("Element ID: {}".format(area_reinf.Id))
    output.print_md("---")

    # Get all parameters
    parameters = area_reinf.Parameters

    # Categorize parameters
    spacing_params = []
    bar_type_params = []
    direction_params = []
    other_params = []

    for param in parameters:
        param_name = param.Definition.Name

        if "Spacing" in param_name:
            spacing_params.append(param)
        elif "Bar Type" in param_name:
            bar_type_params.append(param)
        elif "Direction" in param_name:
            direction_params.append(param)
        else:
            other_params.append(param)

    # Display spacing parameters
    output.print_md("### 📏 **Spacing Parameters:**")
    for param in spacing_params:
        param_name = param.Definition.Name
        try:
            if param.HasValue:
                if param.StorageType == StorageType.Double:
                    value = param.AsDouble()
                    # Convert feet to mm for display
                    value_mm = value * 304.8
                    output.print_md("• **{}**: {:.2f} ft ({:.1f} mm)".format(param_name, value, value_mm))
                else:
                    output.print_md("• **{}**: {}".format(param_name, "Has value but not double"))
            else:
                output.print_md("• **{}**: No value".format(param_name))
        except:
            output.print_md("• **{}**: Error reading value".format(param_name))

    # Display bar type parameters
    output.print_md("\n### 🔧 **Bar Type Parameters:**")
    for param in bar_type_params:
        param_name = param.Definition.Name
        try:
            if param.HasValue:
                element_id = param.AsElementId()
                if element_id != ElementId.InvalidElementId:
                    element = doc.GetElement(element_id)
                    if element:
                        name = element.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                        output.print_md("• **{}**: {} (ID: {})".format(param_name, name, element_id))
                    else:
                        output.print_md("• **{}**: Element not found (ID: {})".format(param_name, element_id))
                else:
                    output.print_md("• **{}**: Invalid Element ID".format(param_name))
            else:
                output.print_md("• **{}**: No value".format(param_name))
        except:
            output.print_md("• **{}**: Error reading value".format(param_name))

    # Display direction parameters
    output.print_md("\n### 🎯 **Direction Parameters:**")
    for param in direction_params:
        param_name = param.Definition.Name
        try:
            if param.HasValue:
                if param.StorageType == StorageType.Integer:
                    value = param.AsInteger()
                    status = "Enabled" if value == 1 else "Disabled"
                    output.print_md("• **{}**: {} ({})".format(param_name, value, status))
                else:
                    output.print_md("• **{}**: {}".format(param_name, "Has value but not integer"))
            else:
                output.print_md("• **{}**: No value".format(param_name))
        except:
            output.print_md("• **{}**: Error reading value".format(param_name))

    # Display other important parameters
    output.print_md("\n### 📋 **Other Parameters:**")
    important_params = ["Layout Rule", "Additional Bottom Cover Offset", "Additional Top Cover Offset"]
    for param in other_params:
        param_name = param.Definition.Name
        if any(imp in param_name for imp in important_params):
            try:
                if param.HasValue:
                    if param.StorageType == StorageType.Integer:
                        value = param.AsInteger()
                        output.print_md("• **{}**: {}".format(param_name, value))
                    elif param.StorageType == StorageType.Double:
                        value = param.AsDouble()
                        value_mm = value * 304.8
                        output.print_md("• **{}**: {:.4f} ft ({:.1f} mm)".format(param_name, value, value_mm))
                    else:
                        output.print_md("• **{}**: Has value".format(param_name))
                else:
                    output.print_md("• **{}**: No value".format(param_name))
            except:
                output.print_md("• **{}**: Error reading value".format(param_name))

    # Summary
    output.print_md("\n### 📊 **Summary:**")
    output.print_md("• Spacing parameters: {}".format(len(spacing_params)))
    output.print_md("• Bar type parameters: {}".format(len(bar_type_params)))
    output.print_md("• Direction parameters: {}".format(len(direction_params)))
    output.print_md("• Total parameters: {}".format(len(list(parameters))))

    output.print_md("\n💡 **Use this information to fix parameter names in the library!**")

def main():
    """Main execution function"""
    try:
        inspect_area_reinforcement_parameters()
    except Exception as e:
        forms.alert("Error: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    main()