# -*- coding: utf-8 -*-
"""
Inspect Area Reinforcement Type Parameters
Memeriksa parameter-parameter yang tersedia pada Area Reinforcement Type
"""

__title__ = "Inspect Area Reinforcement Type"
__author__ = "PrasKaa Team"

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.Structure import AreaReinforcementType
import clr
clr.AddReference('System')
from System.Collections.Generic import List

# Akses dokumen Revit
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application


def inspect_area_reinforcement_type(area_reinforcement_type):
    """
    Memeriksa parameter-parameter AreaReinforcementType
    """
    results = {
        'basic_info': {},
        'parameters': [],
        'properties': [],
        'methods': []
    }

    try:
        # Basic info
        results['basic_info']['id'] = area_reinforcement_type.Id
        results['basic_info']['name'] = getattr(area_reinforcement_type, 'Name', 'Unnamed')

        # Get all parameters
        for param in area_reinforcement_type.Parameters:
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
                    param_info['value'] = str(param.AsDouble())
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
        for attr_name in dir(area_reinforcement_type):
            if not attr_name.startswith('_') and not callable(getattr(area_reinforcement_type, attr_name)):
                try:
                    value = getattr(area_reinforcement_type, attr_name)
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
        for attr_name in dir(area_reinforcement_type):
            if not attr_name.startswith('_') and callable(getattr(area_reinforcement_type, attr_name)):
                results['methods'].append(attr_name)

    except Exception as e:
        results['error'] = str(e)

    return results


def main():
    try:
        # Dapatkan semua Area Reinforcement Type
        area_reinforcement_types = FilteredElementCollector(doc)\
            .OfClass(AreaReinforcementType)\
            .ToElements()

        if not area_reinforcement_types:
            TaskDialog.Show("Info", "Tidak ada Area Reinforcement Type di project ini!")
            return

        # Untuk prototype, inspect yang pertama saja
        art = area_reinforcement_types[0]

        # Inspect parameters
        inspection_results = inspect_area_reinforcement_type(art)

        # Buat report
        report = "=== AREA REINFORCEMENT TYPE INSPECTION ===\n\n"

        # Basic info
        report += "BASIC INFO:\n"
        report += "ID: {}\n".format(inspection_results['basic_info']['id'])
        report += "Name: {}\n\n".format(inspection_results['basic_info']['name'])

        # Parameters
        report += "PARAMETERS ({}):\n".format(len(inspection_results['parameters']))
        for param in inspection_results['parameters'][:20]:  # Limit to first 20
            report += "- {}: {} ({})\n".format(param['name'], param['value'], param['type'])
        if len(inspection_results['parameters']) > 20:
            report += "... and {} more parameters\n".format(len(inspection_results['parameters']) - 20)
        report += "\n"

        # Properties
        report += "PROPERTIES ({}):\n".format(len(inspection_results['properties']))
        for prop in inspection_results['properties'][:10]:  # Limit to first 10
            report += "- {}: {} ({})\n".format(prop['name'], prop['value'], prop['type'])
        if len(inspection_results['properties']) > 10:
            report += "... and {} more properties\n".format(len(inspection_results['properties']) - 10)
        report += "\n"

        # Methods
        report += "METHODS ({}):\n".format(len(inspection_results['methods']))
        for method in inspection_results['methods'][:15]:  # Limit to first 15
            report += "- {}\n".format(method)
        if len(inspection_results['methods']) > 15:
            report += "... and {} more methods\n".format(len(inspection_results['methods']) - 15)

        # Tampilkan dialog (limit text length untuk dialog)
        if len(report) > 2000:
            report = report[:2000] + "\n\n[Report truncated - see console for full details]"

        TaskDialog.Show("Area Reinforcement Type Inspection", report)

        # Print full report ke console
        print("=== FULL AREA REINFORCEMENT TYPE INSPECTION ===")
        print("Basic Info:")
        print("  ID:", inspection_results['basic_info']['id'])
        print("  Name:", inspection_results['basic_info']['name'])
        print("\nParameters:")
        for param in inspection_results['parameters']:
            print("  {}: {} ({}) [{}]".format(param['name'], param['value'], param['type'], 'RO' if param['readonly'] else 'RW'))
        print("\nProperties:")
        for prop in inspection_results['properties']:
            print("  {}: {} ({})".format(prop['name'], prop['value'], prop['type']))
        print("\nMethods:")
        for method in inspection_results['methods']:
            print("  {}".format(method))

    except Exception as e:
        TaskDialog.Show("Error", "Error: {}".format(str(e)))
        print("Error detail: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())


# Jalankan script
if __name__ == '__main__':
    main()