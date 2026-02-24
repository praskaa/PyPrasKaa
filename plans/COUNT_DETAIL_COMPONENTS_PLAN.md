# Plan: Count Selected Detail Components

## Objective
Buat pyRevit script sederhana untuk menghitung jumlah Detail Components (OST_DetailComponents) yang dipilih di viewport.

## Requirements
- User memilih elements di viewport (detail components)
- Script menghitung hanya Detail Components dari seleksi
- Tampilkan jumlah dalam output window

## Implementation Steps

### 1. Script Logic (`script.py`)
```
1. Get uidoc (active UIDocument)
2. Get selection (Selection.GetElementIds)
3. Filter elements yang termasuk OST_DetailComponents
4. Hitung jumlah
5. Tampilkan hasil dengan pyRevit output
```

### 2. Bundle Configuration (`bundle.yaml`)
- title: "Count Detail Components"
- tooltip: Hitung jumlah detail components yang dipilih
- context: selection (membutuhkan ada elemen yang dipilih)

### 3. Output Format
- Menggunakan `output.log_info()` atau `output.print_md()` untuk output yang baik
- Tampilkan jumlah detail components yang dipilih

## File Structure
```
PrasKaaPyKit.tab/
└── [panel pilihan]/
    └── CountDetailComponents.pushbutton/
        ├── script.py
        └── bundle.yaml
```

## Script Template
```python
from pyrevit import revit, DB, script
from Autodesk.Revit.DB import BuiltInCategory, OST_DetailComponents

# Get selection
uidoc = revit.uidoc
selection_ids = uidoc.Selection.GetElementIds()

# Filter for Detail Components
detail_components = []
for elem_id in selection_ids:
    elem = revit.doc.GetElement(elem_id)
    if elem.Category.Id == OST_DetailComponents:
        detail_components.append(elem)

# Display result
output = script.get_output()
output.log_info("{} detail components selected".format(len(detail_components)))
```

## Notes
- Detail Components adalah view-specific elements
- Script hanya menghitung yang termasuk OST_DetailComponents
- Jika tidak ada yang dipilih, tampilkan pesan info
