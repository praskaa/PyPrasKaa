# -*- coding: utf-8 -*-
"""
Inspect Rebar Bar Types and Parameters
Memeriksa semua Rebar Bar Type yang tersedia beserta parameter-parameternya
"""

__title__ = "Inspect Rebar\nBar Types"
__author__ = "Your Name"

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.Structure import RebarBarType
import clr
clr.AddReference('System')
from System.Collections.Generic import List

# Akses dokumen Revit
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application


def inspect_rebar_bar_type(rebar_bar_type):
    """
    Memeriksa parameter-parameter RebarBarType
    """
    results = {
        'basic_info': {},
        'parameters': [],
        'properties': [],
        'methods': []
    }

    try:
        # Basic info - use Type Name parameter
        results['basic_info']['id'] = rebar_bar_type.Id

        # Try to get Type Name parameter first
        type_name_param = rebar_bar_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if type_name_param and type_name_param.AsString():
            results['basic_info']['name'] = type_name_param.AsString()
        else:
            results['basic_info']['name'] = getattr(rebar_bar_type, 'Name', 'Unnamed')

        # Get all parameters
        for param in rebar_bar_type.Parameters:
            try:
                param_info = {
                    'name': param.Definition.Name,
                    'value': 'N/A',
                    'type': param.StorageType.ToString(),
                    'readonly': param.IsReadOnly
                }

                # Try to get parameter value
                if param.StorageType == StorageType.String:
                    param_info['value'] = param.AsString() or 'Empty'
                elif param.StorageType == StorageType.Integer:
                    param_info['value'] = str(param.AsInteger())
                elif param.StorageType == StorageType.Double:
                    # Convert feet to mm for diameter parameters
                    double_value = param.AsDouble()
                    if 'diameter' in param.Definition.Name.lower():
                        # Convert from feet to mm (1 foot = 304.8 mm)
                        mm_value = double_value * 304.8
                        param_info['value'] = "{:.1f} mm".format(mm_value)
                    else:
                        param_info['value'] = str(double_value)
                elif param.StorageType == StorageType.ElementId:
                    elem_id = param.AsElementId()
                    if elem_id != ElementId.InvalidElementId:
                        param_info['value'] = str(elem_id)
                    else:
                        param_info['value'] = 'Invalid ElementId'

                results['parameters'].append(param_info)

            except Exception as e:
                results['parameters'].append({
                    'name': param.Definition.Name,
                    'value': 'Error: {}'.format(str(e)),
                    'type': 'Unknown',
                    'readonly': param.IsReadOnly
                })

        # Get properties
        for attr_name in dir(rebar_bar_type):
            if not attr_name.startswith('_') and not callable(getattr(rebar_bar_type, attr_name)):
                try:
                    value = getattr(rebar_bar_type, attr_name)
                    if not callable(value):
                        results['properties'].append({
                            'name': attr_name,
                            'value': str(value),
                            'type': type(value).__name__
                        })
                except:
                    results['properties'].append({
                        'name': attr_name,
                        'value': 'Error accessing property',
                        'type': 'Unknown'
                    })

        # Get methods
        for attr_name in dir(rebar_bar_type):
            if not attr_name.startswith('_') and callable(getattr(rebar_bar_type, attr_name)):
                results['methods'].append(attr_name)

    except Exception as e:
        results['error'] = str(e)

    return results


def main():
    try:
        # Dapatkan semua Rebar Bar Type
        rebar_bar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()

        if not rebar_bar_types:
            TaskDialog.Show("Info", "Tidak ada Rebar Bar Type di project ini!")
            return

        # Buat report
        report = "=== REBAR BAR TYPES INSPECTION ===\n\n"

        # Summary
        report += "SUMMARY:\n"
        report += "Total Rebar Bar Types: {}\n\n".format(len(rebar_bar_types))

        # Inspect each type
        for i, rbt in enumerate(rebar_bar_types, 1):
            report += "--- REBAR BAR TYPE {} ---\n".format(i)

            # Basic info - use Type Name parameter
            try:
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.AsString():
                    name = type_name_param.AsString()
                else:
                    name = rbt.Name if hasattr(rbt, 'Name') and rbt.Name else "Unnamed"
            except AttributeError:
                name = "Unnamed"

            report += "ID: {}\n".format(rbt.Id)
            report += "Name: {}\n".format(name)

            # Add diameter info to dialog
            try:
                bar_diameter_param = rbt.get_Parameter(BuiltInParameter.REBAR_BAR_DIAMETER)
                if bar_diameter_param:
                    diameter_feet = bar_diameter_param.AsDouble()
                    diameter_mm = diameter_feet * 304.8
                    report += "Diameter: {:.1f} mm\n".format(diameter_mm)
            except:
                pass

            # Key parameters (limit to important ones for dialog)
            key_params = []
            for param in rbt.Parameters:
                try:
                    param_name = param.Definition.Name
                    if any(keyword in param_name.lower() for keyword in ['diameter', 'size', 'grade', 'type']):
                        if param.StorageType == StorageType.Double:
                            value = str(param.AsDouble())
                        elif param.StorageType == StorageType.String:
                            value = param.AsString() or 'Empty'
                        elif param.StorageType == StorageType.Integer:
                            value = str(param.AsInteger())
                        else:
                            value = 'N/A'

                        key_params.append("{}: {}".format(param_name, value))
                except:
                    continue

            if key_params:
                report += "Key Parameters:\n"
                for param in key_params[:5]:  # Limit to 5 key params
                    report += "- {}\n".format(param)
            else:
                report += "No key parameters found\n"

            report += "\n"

        # Tampilkan dialog (limit text length untuk dialog)
        if len(report) > 2000:
            report = report[:2000] + "\n\n[Report truncated - see console for full details]"

        TaskDialog.Show("Rebar Bar Types Inspection", report)

        # Print full detailed report ke console
        print("=== FULL REBAR BAR TYPES INSPECTION ===")

        for i, rbt in enumerate(rebar_bar_types, 1):
            print("\n--- REBAR BAR TYPE {} ---".format(i))

            # Inspect detailed parameters
            inspection_results = inspect_rebar_bar_type(rbt)

            print("Basic Info:")
            print("  ID:", inspection_results['basic_info']['id'])
            print("  Name:", inspection_results['basic_info']['name'])

            print("\nParameters:")
            for param in inspection_results['parameters']:
                print("  {}: {} ({}) [{}]".format(param['name'], param['value'], param['type'], 'RO' if param['readonly'] else 'RW'))

            print("\nProperties:")
            for prop in inspection_results['properties'][:10]:  # Limit properties
                print("  {}: {} ({})".format(prop['name'], prop['value'], prop['type']))

            print("\nMethods ({} total):".format(len(inspection_results['methods'])))
            for method in inspection_results['methods'][:15]:  # Limit methods
                print("  {}".format(method))

            if len(inspection_results['methods']) > 15:
                print("  ... and {} more methods".format(len(inspection_results['methods']) - 15))

        print("\n=== INSPECTION COMPLETE ===")
        print("Total Rebar Bar Types inspected: {}".format(len(rebar_bar_types)))

    except Exception as e:
        TaskDialog.Show("Error", "Error: {}".format(str(e)))
        print("Error detail: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())


# Jalankan script
if __name__ == '__main__':
    main()