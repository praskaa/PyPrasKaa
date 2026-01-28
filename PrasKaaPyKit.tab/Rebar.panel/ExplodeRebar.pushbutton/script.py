# -*- coding: utf-8 -*-
from pyrevit import forms, revit, script
from Autodesk.Revit.DB import *
import csv

# Menggunakan Helper untuk tampilan list yang lebih rapi
class FamilySymbolOption(forms.TemplateListItem):
    @property
    def name(self):
        # Menampilkan Nama Family + Nama Tipe
        return "{} : {}".format(self.item.Family.Name, revit.query.get_name(self.item))

doc = __revit__.ActiveUIDocument.Document

# 1. Pilih File CSV
csv_path = forms.pick_file(file_ext='csv')

if csv_path:
    # 2. Ambil semua tipe (FamilySymbol) dari kategori Structural Foundation
    pile_symbols = FilteredElementCollector(doc) \
        .OfClass(FamilySymbol) \
        .OfCategory(BuiltInCategory.OST_StructuralFoundation) \
        .ToElements()

    if not pile_symbols:
        forms.alert("Tidak ditemukan Family di kategori Structural Foundation.", exitscript=True)

    # 3. Pilih tipe pile menggunakan SelectFromList (Lebih stabil)
    selected_symbol = forms.SelectFromList.show(
        [FamilySymbolOption(s) for s in pile_symbols],
        title='Pilih Tipe Piling (450x450)',
        button_name='Pilih Tipe',
        width=500,
        height=600
    )

    if selected_symbol:
        # Mulai Transaksi
        with revit.Transaction("Place Piles from CSV"):
            try:
                # Aktifkan simbol agar tidak error saat placement
                if not selected_symbol.IsActive:
                    selected_symbol.Activate()

                with open(csv_path, 'r') as f:
                    reader = csv.reader(f)
                    next(reader) # Lewati header PN, X, Y
                    
                    count = 0
                    for row in reader:
                        if len(row) < 3: continue
                        
                        pn = row[0]
                        # Konversi Meter ke Feet (Satuan Internal Revit)
                        x_ft = float(row[1]) * 3.28084
                        y_ft = float(row[2]) * 3.28084
                        
                        point = XYZ(x_ft, y_ft, 0)

                        # Menempatkan Family Instance
                        new_pile = doc.Create.NewFamilyInstance(
                            point, 
                            selected_symbol, 
                            Structure.StructuralType.Footing
                        )
                        
                        # Masukkan nomor PN ke parameter 'Mark'
                        param_mark = new_pile.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                        if param_mark:
                            param_mark.Set(str(pn))
                        
                        count += 1
                
                forms.alert("Berhasil memasang {} pile.".format(count))

            except Exception as e:
                forms.alert("Gagal: {}".format(str(e)))