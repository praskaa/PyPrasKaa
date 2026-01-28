from pyrevit import revit, forms
from Autodesk.Revit import DB as db

doc = revit.doc
uidoc = revit.uidoc
view = revit.active_view

# 1. Ambil ID untuk Independent Tags
tags = db.FilteredElementCollector(doc, view.Id) \
         .OfClass(db.IndependentTag) \
         .ToElementIds()

# 2. Ambil ID untuk Spot Dimensions (Elevation & Slope)
spot_dimensions = db.FilteredElementCollector(doc, view.Id) \
                    .OfClass(db.SpotDimension) \
                    .ToElementIds()

# 3. Gabungkan kedua daftar ID
final_selection = list(tags) + list(spot_dimensions)

# 4. Eksekusi Seleksi di Layar
if final_selection:
    # Convert ke List[ElementId] untuk Revit API
    from System.Collections.Generic import List
    id_list = List[db.ElementId](final_selection)
    
    uidoc.Selection.SetElementIds(id_list)
    
    forms.toast("Terpilih: {} Tags & {} Spot Dimensions"
                .format(len(tags), len(spot_dimensions)), 
                title="Selection Success")
else:
    forms.alert("Tidak ada Tags atau Spot Dimensions di view ini.", title="Empty View")