'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Copies tags from the active view to a temporary file. Stores tag data
including host element, position, family, and type for later pasting.
_____________________________________________________________________
How-to:
1. Navigate to the view containing tags
2. Click "Copy Tags"
3. Tags data is saved to temporary clipboard

Notes:
- Stores: host element ID, position (X, Y, Z), family name, type name
- Data is saved to TEMP folder as JSON file
- Use "Paste Tags" to paste on linked model

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

from pyrevit import revit, forms
from Autodesk.Revit import DB as db
import json
import os

doc = revit.doc
view = revit.active_view
tag_data_list = []

# Filter Tag di View aktif
tags = db.FilteredElementCollector(doc, view.Id).OfClass(db.IndependentTag)

for t in tags:
    try:
        # Ambil ID Host (ElementId) dari HashSet
        host_ids = t.GetTaggedLocalElementIds()
        if host_ids.Count == 0: 
            continue
         
        # Cara mengambil elemen dari HashSet: Gunakan loop atau list conversion
        first_host_id = None
        for hid in host_ids:
            first_host_id = hid.IntegerValue
            break # Kita hanya butuh host pertama
         
        # Ambil tipe tag
        tag_type = doc.GetElement(t.GetTypeId())
        family_name = tag_type.FamilyName
        type_name = db.Element.Name.__get__(tag_type)
         
        tag_info = {
            'host_id': first_host_id,
            'x': t.TagHeadPosition.X,
            'y': t.TagHeadPosition.Y,
            'z': t.TagHeadPosition.Z,
            'family_name': family_name,
            'type_name': type_name,
            'orientation': str(t.TagOrientation)
        }
        tag_data_list.append(tag_info)
         
    except Exception as e:
        forms.toast("Gagal ambil data pada Tag ID {}: {}".format(t.Id, e))

# Simpan ke Temp
temp_path = os.path.join(os.environ['TEMP'], 'revit_tag_clipboard.json')
with open(temp_path, 'w') as f:
    json.dump(tag_data_list, f)

forms.toast("Berhasil menyalin {} tag ke clipboard.".format(len(tag_data_list)))