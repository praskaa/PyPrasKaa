# -*- coding: utf-8 -*-
"""
Updates Room Number, SDL, and LL from CSV
Author: PrasKaa
"""
__title__ = 'Set Load Plan by CSV'
__author__ = 'PrasKaa'

import clr
import csv
from pyrevit import forms, script

# Import Revit API classes
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, BuiltInParameter, StorageType
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

doc = __revit__.ActiveUIDocument.Document
logger = script.get_logger()

def get_csv_mapping(csv_filepath):
    """
    Membaca CSV dan membuat dictionary mapping.
    """
    mapping = {}
    try:
        with open(csv_filepath, 'r') as f:
            reader = csv.reader(f)
            
            # Skip 2 baris header
            next(reader) 
            next(reader)

            for row in reader:
                if len(row) >= 4:
                    target_number = row[0].strip()
                    key_name = row[1].strip()
                    val_sdl = row[2].strip()
                    val_ll = row[3].strip()
                    
                    if key_name:
                        mapping[key_name] = {
                            'number': target_number,
                            'sdl': val_sdl,
                            'll': val_ll
                        }
    except Exception as e:
        forms.alert("Gagal membaca CSV: {}".format(str(e)))
        return None
        
    return mapping

def set_param_value(element, param_name, new_value_str, is_load_knm2=False):
    """
    Mencari parameter dan mengisinya.
    
    Args:
        element: Revit Element (Room)
        param_name: Nama Parameter (SDL/LL)
        new_value_str: Nilai dari CSV (String)
        is_load_knm2: Boolean. Jika True, nilai akan dikonversi dari kN/m2 ke Internal Unit.
    """
    param = element.LookupParameter(param_name)
    
    if not param:
        return False
    
    if param.IsReadOnly:
        return False

    updated = False
    
    # -- TIPE STRING/TEXT --
    if param.StorageType == StorageType.String:
        current_val = param.AsString()
        if current_val != new_value_str:
            param.Set(new_value_str)
            updated = True
            
    # -- TIPE DOUBLE/NUMBER/AREA FORCE --
    elif param.StorageType == StorageType.Double:
        try:
            val_double = float(new_value_str)
            
            # LOGIKA KONVERSI UNIT
            # Jika parameter ini adalah Load (kN/m2), kita harus convert ke Internal Unit
            if is_load_knm2:
                # Convert dari kN/m2 (Metric) -> Internal Unit (Revit System)
                val_to_set = UnitUtils.ConvertToInternalUnits(val_double, UnitTypeId.KilonewtonsPerSquareMeter)
            else:
                # Jika hanya angka biasa tanpa satuan
                val_to_set = val_double

            # Cek nilai eksisting (menggunakan toleransi presisi)
            current_val = param.AsDouble()
            if abs(current_val - val_to_set) > 0.0001:
                param.Set(val_to_set)
                updated = True
                
        except ValueError:
            pass # Value di CSV bukan angka valid

    # -- TIPE INTEGER --
    elif param.StorageType == StorageType.Integer:
        try:
            new_val_int = int(new_value_str)
            if param.AsInteger() != new_val_int:
                param.Set(new_val_int)
                updated = True
        except ValueError:
            pass

    return updated

def main():
    csv_path = forms.pick_file(file_ext='csv', title='Pilih Tabel Loading Plan CSV')
    if not csv_path: return

    name_to_data_map = get_csv_mapping(csv_path)
    if not name_to_data_map: return

    print("Mapping Loaded. Mengupdate Room dengan konversi kN/m2...")
    print("-" * 50)

    collector = FilteredElementCollector(doc)\
                .OfCategory(BuiltInCategory.OST_Rooms)\
                .WhereElementIsNotElementType()
    rooms = list(collector)

    t = Transaction(doc, "Update Room Loads")
    t.Start()

    count_updated = 0

    for room in rooms:
        p_name = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        room_name = p_name.AsString() if p_name else ""

        if room_name in name_to_data_map:
            data = name_to_data_map[room_name]
            
            # 1. Update Number (Tidak perlu konversi unit, biasanya String)
            new_number = data['number']
            p_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if p_number.AsString() != new_number:
                try:
                    p_number.Set(new_number)
                    print("Room '{}': Number Updated -> {}".format(room_name, new_number))
                    count_updated += 1
                except:
                    print("FAIL: Room '{}' Number duplikat.".format(room_name))

            # 2. Update SDL (Aktifkan mode convert kN/m2)
            if set_param_value(room, 'SDL', data['sdl'], is_load_knm2=True):
                print("Room '{}': SDL Updated -> {} kN/m2".format(room_name, data['sdl']))
                count_updated += 1
                
            # 3. Update LL (Aktifkan mode convert kN/m2)
            if set_param_value(room, 'LL', data['ll'], is_load_knm2=True):
                print("Room '{}': LL Updated -> {} kN/m2".format(room_name, data['ll']))
                count_updated += 1

    t.Commit()

if __name__ == '__main__':
    main()