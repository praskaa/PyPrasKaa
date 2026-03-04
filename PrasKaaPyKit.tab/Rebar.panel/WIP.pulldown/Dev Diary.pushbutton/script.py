# -*- coding: utf-8 -*-
__title__ = 'Try get host beams'
__author__ = 'PrasKaa Team'
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Matches beams by geometry intersection and transfers family types from linked EXR model.

Analyzes structural framing elements and detects duplicate family types
with numerical suffixes (e.g., "Beam 1", "Beam 2").

How-to:
1. Click the tool button
2. The tool automatically collects all Structural Framing elements
3. Filters for Rectangular framing sections
4. Groups families into Original vs Duplicate categories
5. Shows analysis results in output window

Notes:
- Uses regex pattern to detect numerical suffixes
- Checks if duplicates have instances in the model
- Helps identify which families can be cleaned up

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#==================================================
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    FamilySymbol
)

from collections import defaultdict
from pyrevit import revit, forms
import re
#.NET Imports 
import clr
clr.AddReference('System')
from System.Collections.Generic import List

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================
app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#==================================================

def get_family_symbols_by_family_name(doc, family_name):
    symbols_type = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsElementType()\
        .ToElements()
    result = []  
    for sym in symbols_type:
        if sym.Family.Name == family_name:
            result.append(sym)
    return result

def has_instance(doc,family_symbol):
    instances_element=FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()
    for inst in instances_element:
        if inst.Symbol.Id == family_symbol.Id:
            return True
    return False
    
def get_instance_count_by_family(doc,family_name):
    symbols = get_family_symbols_by_family_name(doc,family_name)
    if not symbols:
        return 0
    symbols_ids = set (sym.Id for sym in symbols)
    
    count=0
    instances = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()
    
    for inst in instances:
        if inst.GetTypeId() in symbols_ids:
            count += 1
    return count

def main():
#1️⃣ Collect semua Family type dari Structural Framing
    beam_symbol = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_StructuralFraming)\
    .WhereElementIsElementType()\
    .ToElements()

#2️⃣ Filter : hanya Rectangular Framing
# Caranya cek parameter "Section Shape" harus "Rectangular"!
    rectangular_beams = []
    for sym in beam_symbol:
        section_shape_param = sym.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_SHAPE)

        if section_shape_param and section_shape_param.HasValue:
            shape_value = section_shape_param.AsValueString()

            if shape_value == "Rectangle":
                rectangular_beams.append(sym)
#3️⃣ Ambil Family, Get family dari Element menggunakan set untuk menghapus duplikasi.
    family_names_set = set()
    for sym in rectangular_beams:
        family = sym.Family
        family_names_set.add(family.Name)  # Simpan NAMA, bukan object!
    
    family_names = list(family_names_set)  # Convert set ke list

    print("Unique Families ({})".format(family_names))

#4️⃣  Deteksi duplikasi dengan regex pattern, grouping, deteksi family ada original atau tidak    
    originals = []
    duplicates = []

    for family_name in family_names:
        match = re.search(r'\d+$', family_name)     
        if match:
            suffix       =  match.group()
            orginal_name =  family_name[:-len(suffix)].strip()
            duplicates.append((family_name, orginal_name)) #Simpan sebagai tuple (pasangan).
        else:
            originals.append(family_name)

    # Cek apakah setiap family mempunyai original family atau tidak
    for family_name in sorted(originals):
        print("{}⬅️ini Family Original".format(family_name))
    
    for dup_name, orig_name in sorted(duplicates):
        if orig_name in originals:
            print("✓ {} -> DUPLIKAT (Originalnya: {})".format(dup_name,orig_name))
        else:
            print("⚠️ {} -> ORPHAN (Tidak mempunya Original {}' TIDAK ADA!)".format(dup_name,orig_name))

#5️⃣ Cek Duplicate family dipakai di instance atau tidak?
    for dup_name, orig_name in duplicates:
        print('Cek: {} '.format(dup_name))
        dup_symbols = get_family_symbols_by_family_name(doc, dup_name)
        if dup_symbols:
            instance_count = get_instance_count_by_family(doc, dup_name)
            if instance_count > 0:
                print('⚠️  {} → {} instance PERLU DIMIGRATE ke: {}'.format(dup_name, instance_count, orig_name))
            else:
                print('🗑️  {} → Tidak ada instance, bisa langsung dihapus'.format(dup_name))
        else:
            print('❓ {} → Symbol tidak ditemukan di project'.format(dup_name))

if __name__ == '__main__':
    main() 

