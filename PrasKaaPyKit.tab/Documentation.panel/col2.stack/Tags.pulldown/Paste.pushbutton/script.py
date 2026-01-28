from pyrevit import revit, db
import json
import os

doc = revit.doc
view = doc.ActiveView
tag_data_list = []

tags = db.FilteredElementCollector(doc, view.Id).OfClass(db.IndependentTag)

for t in tags:
    try:
        host_ids = t.GetTaggedLocalElementIds()
        if not host_ids: continue
        
        # Ambil tipe tag
        tag_type = doc.GetElement(t.GetTypeId())
        family_name = tag_type.FamilyName
        type_name = db.Element.Name.__get__(tag_type)
        
        tag_info = {
            'host_id': host_ids[0].IntegerValue,
            'x': t.TagHeadPosition.X,
            'y': t.TagHeadPosition.Y,
            'z': t.TagHeadPosition.Z,
            'family_name': family_name,
            'type_name': type_name
        }
        tag_data_list.append(tag_info)
    except:
        pass

temp_path = os.path.join(os.environ['TEMP'], 'revit_tag_clipboard.json')
with open(temp_path, 'w') as f:
    json.dump(tag_data_list, f)

print("Berhasil menyalin {} data tag beserta tipenya!".format(len(tag_data_list)))