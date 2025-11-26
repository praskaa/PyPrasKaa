# -*- coding: utf-8 -*-
"""
List Area Reinforcement Types
Menampilkan semua Area Reinforcement Type yang tersedia di project
"""

__title__ = "List Area\nReinforcement Types"
__author__ = "Your Name"

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


def main():
    try:
        # Dapatkan semua Area Reinforcement Type
        area_reinforcement_types = FilteredElementCollector(doc)\
            .OfClass(AreaReinforcementType)\
            .ToElements()

        if not area_reinforcement_types:
            TaskDialog.Show("Info", "Tidak ada Area Reinforcement Type di project ini!")
            return

        # Buat pesan untuk ditampilkan
        message = "Area Reinforcement Types di Project:\n\n"
        count = 1

        for art in area_reinforcement_types:
            try:
                # Try to get Type Name parameter first (this is what shows in UI)
                type_name_param = art.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.AsString():
                    art_name = type_name_param.AsString()
                else:
                    # Fallback to Name property
                    art_name = art.Name if hasattr(art, 'Name') and art.Name else "Unnamed Type"
            except AttributeError:
                art_name = "Unnamed Type"
            message += "{}. {} (ID: {})\n".format(count, art_name, art.Id)
            count += 1

        message += "\nTotal: {} Area Reinforcement Type(s)".format(len(area_reinforcement_types))

        # Tampilkan dialog
        TaskDialog.Show("Area Reinforcement Types", message)

        # Print ke console juga untuk debugging
        print("=== AREA REINFORCEMENT TYPES ===")
        for art in area_reinforcement_types:
            try:
                # Try to get Type Name parameter first (this is what shows in UI)
                type_name_param = art.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.AsString():
                    art_name = type_name_param.AsString()
                else:
                    # Fallback to Name property
                    art_name = art.Name if hasattr(art, 'Name') and art.Name else "Unnamed Type"
            except AttributeError:
                art_name = "Unnamed Type"
            print("ID: {}, Name: {}".format(art.Id, art_name))
        print("Total: {}".format(len(area_reinforcement_types)))

    except Exception as e:
        TaskDialog.Show("Error", "Error: {}".format(str(e)))
        print("Error detail: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())


# Jalankan script
if __name__ == '__main__':
    main()