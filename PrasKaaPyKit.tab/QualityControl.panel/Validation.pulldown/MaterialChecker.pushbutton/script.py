# -*- coding: utf-8 -*-
"""
Structural Material Manager by Level Range
Description: Set structural materials for elements based on Level ranges (Elevation).
Author: Gemini for User
Revit Version: 2025
"""

from pyrevit import revit, DB, script
from pyrevit import forms

doc = revit.doc
output = script.get_output()

# ============================================================================
# 1. KONFIGURASI USER (EDIT BAGIAN INI SESUAI KEBUTUHAN)
# ============================================================================

# Format Aturan:
# "Category": Kategori Revit (Columns/Framing/Floors)
# "Start_Level": Nama level terbawah (inklusif)
# "End_Level": Nama level teratas (inklusif)
# "Material_Name": Nama Material persis seperti di Material Browser

RULES = [
    # --- CONTOH UNTUK KOLOM (Berdasarkan Gambar Notes: B5 - L.12) ---
    {
        "Category": DB.BuiltInCategory.OST_StructuralColumns,
        "Start_Level": "B5", 
        "End_Level": "L.12",
        "Material_Name": "Concrete - fc' 50 MPa" # Ganti dengan nama material di Revitmu
    },
    # --- CONTOH UNTUK KOLOM (L.12 - L.24) ---
    {
        "Category": DB.BuiltInCategory.OST_StructuralColumns,
        "Start_Level": "L.12",
        "End_Level": "L.24",
        "Material_Name": "Concrete - fc' 45 MPa"
    },
    # --- CONTOH UNTUK FRAMING/BALOK (L.12 - L.24) ---
    {
        "Category": DB.BuiltInCategory.OST_StructuralFraming,
        "Start_Level": "L.12",
        "End_Level": "L.24",
        "Material_Name": "Concrete - fc' 35 MPa"
    },
    # --- CONTOH UNTUK LANTAI/FLOOR ---
    {
        "Category": DB.BuiltInCategory.OST_Floors,
        "Start_Level": "L.10",
        "End_Level": "L.15",
        "Material_Name": "Concrete - fc' 30 MPa"
    }
]

# ============================================================================
# 2. FUNGSI & LOGIKA
# ============================================================================

def get_level_ids_in_range(start_name, end_name):
    """Mencari semua Level ID yang berada di antara elevasi Start dan End."""
    all_levels = DB.FilteredElementCollector(doc)\
                   .OfClass(DB.Level)\
                   .ToElements()
    
    # Cari object level berdasarkan nama
    start_lvl_obj = next((l for l in all_levels if l.Name == start_name), None)
    end_lvl_obj = next((l for l in all_levels if l.Name == end_name), None)

    if not start_lvl_obj or not end_lvl_obj:
        print("❌ Error: Level '{}' atau '{}' tidak ditemukan.".format(start_name, end_name))
        return []

    min_elev = min(start_lvl_obj.Elevation, end_lvl_obj.Elevation)
    max_elev = max(start_lvl_obj.Elevation, end_lvl_obj.Elevation)

    # Toleransi floating point
    target_ids = []
    for l in all_levels:
        # Mengambil level yang ada di range (dengan sedikit toleransi)
        if l.Elevation >= (min_elev - 0.001) and l.Elevation <= (max_elev + 0.001):
            target_ids.append(l.Id)
    
    return target_ids

def get_material_id(mat_name):
    """Mencari Material ID berdasarkan Nama."""
    mat = DB.FilteredElementCollector(doc)\
            .OfClass(DB.Material)\
            .WhereElementIsNotElementType()\
            .ToElements()
    
    for m in mat:
        if m.Name == mat_name:
            return m.Id
    return None

def get_element_level_param(element):
    """Menentukan parameter level yang tepat berdasarkan kategori elemen."""
    cat_id = element.Category.Id.IntegerValue
    
    # Structural Columns biasanya pakai Base Level
    if cat_id == int(DB.BuiltInCategory.OST_StructuralColumns):
        return element.get_Parameter(DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
    
    # Structural Framing biasanya pakai Reference Level
    elif cat_id == int(DB.BuiltInCategory.OST_StructuralFraming):
        # Coba Reference Level Param dulu
        p = element.get_Parameter(DB.BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
        if p and p.HasValue: return p
        # Fallback untuk kondisi tertentu
        return element.get_Parameter(DB.BuiltInParameter.LEVEL_PARAM)
        
    # Floors pakai Level Param
    elif cat_id == int(DB.BuiltInCategory.OST_Floors):
        return element.get_Parameter(DB.BuiltInParameter.LEVEL_PARAM)
        
    return None

# ============================================================================
# 3. EKSEKUSI UTAMA
# ============================================================================

# Mulai Transaction
t = DB.Transaction(doc, "Auto Set Structural Material")
t.Start()

print("--- Memulai Update Material Struktur ---")

try:
    for rule in RULES:
        cat_enum = rule["Category"]
        mat_name = rule["Material_Name"]
        
        # 1. Validasi Material
        mat_id = get_material_id(mat_name)
        if not mat_id:
            print("⚠️ SKIP: Material '{}' tidak ditemukan di Project.".format(mat_name))
            continue

        # 2. Dapatkan Range Level
        target_level_ids = get_level_ids_in_range(rule["Start_Level"], rule["End_Level"])
        if not target_level_ids:
            continue

        # 3. Ambil Semua Elemen Kategori Tersebut
        collector = DB.FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType().ToElements()
        
        count = 0
        for el in collector:
            # Cek Level Elemen
            lvl_param = get_element_level_param(el)
            
            if lvl_param and lvl_param.HasValue:
                elem_lvl_id = lvl_param.AsElementId()
                
                # Jika level elemen ada di dalam daftar target level
                if elem_lvl_id in target_level_ids:
                    # Set Material Structur
                    struct_mat_param = el.get_Parameter(DB.BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
                    
                    if struct_mat_param and not struct_mat_param.IsReadOnly:
                        # Cek apakah material sudah benar agar tidak membebani performance
                        if struct_mat_param.AsElementId() != mat_id:
                            struct_mat_param.Set(mat_id)
                            count += 1
        
        print("✅ Updated {} elemen: {} | Range: {}-{}".format(
            count, 
            rule["Category"], 
            rule["Start_Level"], 
            rule["End_Level"]
        ))

    t.Commit()
    print("--- Selesai ---")

except Exception as e:
    t.RollBack()
    print("❌ Error Critical: {}".format(e))