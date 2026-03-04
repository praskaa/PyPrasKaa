# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Selects all Independent Tags and Spot Dimensions (Elevation & Slope) in the
active view and highlights them in the selection. Useful for batch operations.
_____________________________________________________________________
How-to:
1. Click "Select All Tags"
2. All tags and spot dimensions in active view will be selected

Notes:
- Works on Independent Tags and Spot Dimensions
- Only processes elements in the active view

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
'''

__title__ = "Select All Tags"
__author__ = "PrasKaa Team"
__version__ = "1.0"

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
