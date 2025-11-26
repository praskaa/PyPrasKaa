# -*- coding: utf-8 -*-
__title__ = "Visibility Link Revit"
__doc__ = "Pilih Link, lalu pilih View/Template mana saja secara manual untuk di-hide."

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script
import System.Collections.Generic as List

# Inisialisasi Document
doc = revit.doc

# ==================================================
# 1. PILIH REVIT LINK
# ==================================================
link_collector = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()

if not link_collector:
    forms.alert("Tidak ada Revit Link ditemukan.", exitscript=True)

link_dict = {link.Name: link for link in link_collector}

# Popup 1: Pilih Link yang mau di-hide
selected_link_name = forms.SelectFromList.show(
    sorted(link_dict.keys()),
    title='Langkah 1: Pilih Revit Link',
    multiselect=False
)

if not selected_link_name:
    script.exit()

selected_link = link_dict[selected_link_name]
link_id = selected_link.Id

# Siapkan List ID untuk fungsi HideElements
link_ids_collection = List.List[ElementId]()
link_ids_collection.Add(link_id)


# ==================================================
# 2. KUMPULKAN VIEW & TEMPLATE VALID
# ==================================================
view_collector = FilteredElementCollector(doc).OfClass(View).ToElements()
invalid_id = ElementId.InvalidElementId

# Dictionary untuk menyimpan {Nama Tampilan : Object View}
view_choices = {}

for v in view_collector:
    # Filter standar: Bukan sheet, bukan internal view
    if v.ViewType == ViewType.DrawingSheet or (not v.IsTemplate and not v.CanEnableTemporaryViewPropertiesMode()):
        continue
        
    key_name = ""
    
    # LOGIKA PENAMAAN LIST
    if v.IsTemplate:
        # Ini View Template
        key_name = "[TEMPLATE] - " + v.Name
        view_choices[key_name] = v
        
    else:
        # Ini View Biasa
        # Kita hanya tampilkan View yang settingannya MANUAL (tidak punya View Template aktif)
        # Karena jika punya Template, kita harus edit Templatenya, bukan Viewnya.
        if v.ViewTemplateId == invalid_id:
            key_name = "[VIEW]     - " + v.Name
            view_choices[key_name] = v

if not view_choices:
    forms.alert("Tidak ada View atau Template yang valid untuk diedit.", exitscript=True)

# Urutkan nama agar rapi (Template kumpul dengan template)
sorted_keys = sorted(view_choices.keys())


# ==================================================
# 3. PILIH VIEW TARGET (CHECKLIST)
# ==================================================
# Popup 2: Checklist View
selected_view_names = forms.SelectFromList.show(
    sorted_keys,
    title='Langkah 2: Checklist View/Template Target',
    multiselect=True,  # Ini yang membuat bisa pilih banyak
    button_name='Hide Link di Item Terpilih'
)

if not selected_view_names:
    script.exit()


# ==================================================
# 4. EKSEKUSI
# ==================================================
t = Transaction(doc, "Hide Revit Link Manual Select")
t.Start()

count = 0
error_log = []

for name in selected_view_names:
    v = view_choices[name]
    try:
        if v.IsValidObject:
             v.HideElements(link_ids_collection)
             count += 1
             
    except Exception as e:
        error_msg = "Gagal di {}: {}".format(name, e)
        print(error_msg)
        error_log.append(error_msg)

t.Commit()

# ==================================================
# 5. LAPORAN
# ==================================================
msg = "Sukses!\nLink '{}' telah disembunyikan di {} View/Template terpilih.".format(selected_link_name, count)
forms.alert(msg)