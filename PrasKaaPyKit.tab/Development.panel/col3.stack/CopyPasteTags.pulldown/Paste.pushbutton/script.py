'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Pastes tags from clipboard to a linked Revit model. Uses location detection
to find corresponding elements in the linked model.
_____________________________________________________________________
How-to:
1. Ensure linked model is loaded
2. Click "Paste Tags"
3. Tags are placed based on matching location in linked model

Notes:
- Requires a loaded Revit link
- Uses spatial search to find host elements
- Falls back to bounding box intersection if exact ID not found

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
temp_path = os.path.join(os.environ['TEMP'], 'revit_tag_clipboard.json')

if not os.path.exists(temp_path):
    forms.toast("Clipboard kosong!")
    exit()

# 1. Cari Link yang aktif (Loaded)
all_links = db.FilteredElementCollector(doc).OfClass(db.RevitLinkInstance).ToElements()
link_inst = None
link_doc = None

for link in all_links:
    l_doc = link.GetLinkDocument()
    if l_doc:
        link_inst = link
        link_doc = l_doc
        break

if not link_doc:
    forms.toast("Error: Tidak ada Link Model yang 'Loaded'.")
    exit()

with open(temp_path, 'r') as f:
    tag_records = json.load(f)

def find_tag_type(fam_name, typ_name):
    collector = db.FilteredElementCollector(doc).OfClass(db.FamilySymbol)
    for ts in collector:
        if ts.FamilyName == fam_name and db.Element.Name.__get__(ts) == typ_name:
            return ts.Id
    return None

with db.Transaction(doc, "Paste Tags by Location") as t:
    t.Start()
    count = 0
    
    for data in tag_records:
        try:
            pos = db.XYZ(data['x'], data['y'], data['z'])
            target_id = db.ElementId(data['host_id'])
            linked_element = link_doc.GetElement(target_id)
             
            # JIKA ID TIDAK KETEMU, CARI BERDASARKAN LOKASI (Spatial Search)
            if not linked_element:
                # Gunakan filter bounding box kecil di titik koordinat tersebut
                tolerance = 0.01 
                outline = db.Outline(
                    pos.Add(db.XYZ(-tolerance, -tolerance, -tolerance)), 
                    pos.Add(db.XYZ(tolerance, tolerance, tolerance))
                )
                 
                # Cari elemen di link doc yang bersentuhan dengan titik ini
                potential_hosts = db.FilteredElementCollector(link_doc)\
                    .WhereElementIsNotElementType()\
                    .WherePasses(db.BoundingBoxIntersectsFilter(outline))\
                    .ToElements()
                 
                if potential_hosts:
                    linked_element = potential_hosts[0]

            if linked_element:
                link_ref = db.Reference(linked_element).CreateLinkReference(link_inst)
                 
                tag_type_id = find_tag_type(data['family_name'], data['type_name'])
                if not tag_type_id:
                    tag_type_id = doc.GetDefaultElementTypeId(db.ElementTypeGroup.IndependentTag)

                # Pasang Tag
                new_tag = db.IndependentTag.Create(
                    doc, tag_type_id, view.Id, link_ref, False, 
                    db.TagOrientation.Horizontal, pos
                )
                new_tag.TagHeadPosition = pos
                count += 1
                     
        except Exception as e:
            forms.toast("Gagal pada titik {}: {}".format(data['host_id'], e))
             
    t.Commit()

forms.toast("Berhasil memproses {} tag menggunakan deteksi lokasi.".format(count))