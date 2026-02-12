# Linked Elements Utilities

## Status: PRESERVED FOR FUTURE DEVELOPMENT

**Catatan:** Modul ini sudah dibuat sebagai reusable library, tetapi fitur linked element checking di script MissingBeamTags **tidak diaktifkan** karena keterbatasan Revit API.

### Keterbatasan Revit API

Revit API TIDAK mendukung "collect linked elements visible in host view" secara langsung:
```python
# ERROR - view_id dari host document tidak bisa digunakan untuk linked document
FilteredElementCollector(linked_doc, host_view_id)
```

API expects `view_id` untuk ada di dalam `linked_doc`, bukan di host document.

### Alternatif yang tersedia

1. **Collect ALL linked elements** - tidak filter by visibility
   - Masalah: Element yang tidak visible di view akan ikut terdeteksi
2. **Geometric intersection check** - complex dan computationally expensive
   - Butuh ekstrak geometry dari link instance dan view clip box
   - Tidak praktis untuk daily workflow

### Use Case yang Mungkin

Jika di masa depan Revit API berubah atau ada workaround, modul ini siap digunakan:

```python
from linked_elements import find_missing_tags

result = find_missing_tags(
    revit.doc,
    revit.active_view,
    OST_StructuralFraming
)
```

### Import Functions

```python
from linked_elements import (
    get_all_revti_link_instances,
    get_linked_document,
    get_linked_elements_in_view,
    get_untagged_linked_elements,
    find_missing_tags,
    select_untagged_linked_elements
)
```

### Koleksi Link Instances

```python
from linked_elements import get_all_revti_link_instances

links = get_all_revti_link_instances(revit.doc)
for link in links:
    print(link.Name)
    # Output: "Structure.rvt"
    # Output: "Architecture.rvt"
```

### Koleksi Elements dari Linked Document

```python
from linked_elements import (
    get_linked_document,
    get_linked_elements_in_view
)

links = get_all_revti_link_instances(revit.doc)
for link in links:
    linked_doc = get_linked_document(link)
    
    if linked_doc:
        beams = get_linked_elements_in_view(
            linked_doc,
            revit.active_view.Id,
            OST_StructuralFraming
        )
        print("Beams in {}: {}".format(link.Name, len(beams)))
```

### Cek Tags pada Linked Elements

```python
from linked_elements import get_tagged_linked_element_ids

tagged = get_tagged_linked_element_ids(revit.doc, revit.active_view.Id)
print("Tagged linked elements: {}".format(len(tagged)))
```

### Dapatkan Untagged Elements

```python
from linked_elements import get_untagged_linked_elements

untagged = get_untagged_linked_elements(
    revit.doc,
    revit.active_view.Id,
    OST_StructuralFraming
)

for info in untagged:
    print("Untagged: {}".format(info.name))
```

### Select Untagged Elements

```python
from linked_elements import select_untagged_linked_elements

count = select_untagged_linked_elements(
    revit.doc,
    revit.active_view.Id,
    OST_StructuralFraming
)
```

## API Reference

### Classes

#### LinkedElementInfo

Container untuk data linked element dengan reference info.

```python
class LinkedElementInfo:
    def __init__(self, element, link_instance, linked_doc):
        self.element = element          # Element di linked doc
        self.link_instance = link_instance  # RevitLinkInstance
        self.linked_doc = linked_doc    # Document object
    
    @property
    def element_id(self):
        """ElementId di linked document."""
        return self.element.Id
    
    @property
    def link_instance_id(self):
        """ElementId dari link instance di host document."""
        return self.link_instance.Id
    
    @property
    def name(self):
        """Nama element dengan prefix nama link."""
        return "{0} :: {1}".format(
            self.link_instance.Name,
            self.element.Name
        )
```

### Functions

#### get_all_revti_link_instances(doc)

Mengembalikan semua RevitLinkInstance di document.

```python
links = get_all_revti_link_instances(revit.doc)
# Returns: List[RevitLinkInstance]
```

#### get_linked_document(link_instance)

Mendapatkan Document object dari RevitLinkInstance.

```python
linked_doc = get_linked_document(link_instance)
# Returns: Document atau None jika unavailable
```

#### get_linked_elements_in_view(linked_doc, view_id, category)

Mengumpulkan elements dari linked document yang visible di view.

```python
beams = get_linked_elements_in_view(
    linked_doc,
    revit.active_view.Id,
    OST_StructuralFraming
)
# Returns: List[Element]
```

#### collect_linked_elements_with_info(doc, view_id, category)

Convenience function yang mengembalikan LinkedElementInfo objects.

```python
linked_beams = collect_linked_elements_with_info(
    revit.doc,
    revit.active_view.Id,
    OST_StructuralFraming
)
# Returns: List[LinkedElementInfo]
```

#### get_tagged_linked_element_ids(doc, view_id)

Mendapatkan dictionary dari tagged linked elements.

```python
tagged = get_tagged_linked_element_ids(revit.doc, view.Id)
# Returns: {(link_instance_id, element_id): LinkedElementInfo}
```

#### get_untagged_linked_elements(doc, view_id, category)

Mendapatkan semua untagged elements dari linked documents.

```python
untagged = get_untagged_linked_elements(
    revit.doc,
    revit.active_view.Id,
    OST_StructuralFraming
)
# Returns: List[LinkedElementInfo]
```

#### select_untagged_linked_elements(doc, view_id, category)

Select semua untagged elements di linked documents.

```python
count = select_untagged_linked_elements(
    revit.doc,
    revit.active_view.Id,
    OST_StructuralFraming
)
# Returns: int - jumlah elements yang di-select
```

#### find_missing_tags(doc, view, category, include_host=True, include_linked=True)

Convenience function yang menggabungkan local dan linked checking.

```python
result = find_missing_tags(
    revit.doc,
    revit.active_view,
    OST_StructuralFraming
)
# Returns: {
#     'host': [Element, ...],
#     'linked': [LinkedElementInfo, ...],
#     'total': int
# }
```

## Contoh Lengkap

### Missing Beam Tags (Host + Linked)

```python
"""Cek missing tags untuk beams dari host dan linked documents."""

from pyrevit import revit, forms
from linked_elements import (
    find_missing_tags,
    get_references_for_selection
)

doc = revit.doc
view = revit.active_view

# Cek missing tags
result = find_missing_tags(
    doc, view,
    OST_StructuralFraming,
    include_host=True,
    include_linked=True
)

print("Host beams missing tags: {}".format(len(result['host'])))
print("Linked beams missing tags: {}".format(len(result['linked'])))
print("Total: {}".format(result['total']))

# Select semua untagged
all_untagged = result['host'] + result['linked']

# Host elements bisa langsung di-select
selection = revit.get_selection()
host_ids = [e.Id for e in result['host']]

# Linked elements butuh Reference objects
linked_refs = get_references_for_selection(result['linked'])

# Combine selection
all_ids = host_ids + linked_refs
selection.set_to(all_ids)

forms.alert(
    "Selected {0} untagged beams".format(len(all_ids)),
    title="Missing Beam Tags"
)
```

### Create Tags pada Linked Elements

```python
"""Buat tags pada untagged linked elements."""

from pyrevit import revit
from linked_elements import (
    get_untagged_linked_elements,
    create_tags_on_linked_elements
)

doc = revit.doc
view = revit.active_view

# Get untagged linked elements
untagged = get_untagged_linked_elements(
    doc,
    view.Id,
    OST_StructuralFraming
)

print("Creating tags for {} linked beams...".format(len(untagged)))

# Create tags
count = create_tags_on_linked_elements(
    doc,
    view,
    untagged,
    OST_StructuralFramingTags
)

print("Created {} tags".format(count))
```

## Kategori yang Didukung

| Category | BuiltInCategory | Tag Category |
|----------|-----------------|--------------|
| Structural Framing | `OST_StructuralFraming` | `OST_StructuralFramingTags` |
| Structural Columns | `OST_StructuralColumns` | `OST_StructuralColumnTags` |
| Walls | `OST_Walls` | `OST_WallTags` |
| Floors | `OST_Floors` | `OST_FloorTags` |
| Foundations | `OST_StructuralFoundation` | `OST_StructuralFoundationTags` |

## Catatan Penting

### GetLinkDocument() Returns None

Beberapa link instances mungkin return None dari GetLinkDocument() jika:
- File linked sudah di-reload/dipindah
- Link unloaded
- Permission issues

```python
linked_doc = get_linked_document(link_instance)
if linked_doc is None:
    print("Warning: {} is unloaded".format(link_instance.Name))
    continue
```

### Element Selection untuk Linked Elements

Untuk linked elements, pyRevit selection membutuhkan Reference objects:

```python
from linked_elements import get_references_for_selection

refs = get_references_for_selection(linked_elements)
selection.set_to(refs)  # ✅ Benar

# Salah:
# selection.set_to([elem.Id for elem in linked_elements])  # ❌
```

### Revit Version Compatibility

Fungsi ini menggunakan `GetTaggedLocalElementIds()` (Revit 2023+):
- Revit 2023+: `tag.GetTaggedLocalElementIds()`
- Revit 2022: `tag.GetTaggedLocalElementIds()` (dengan or_equal=True check)

## Troubleshooting

### "No elements found" tapi link exists

Pastikan link sudah di-load dan visible di view:

```python
# Cek apakah link loaded
link_doc = get_linked_document(link_instance)
if link_doc is None:
    print("Link unloaded")
    continue

# Cek visibility di view
beams = get_linked_elements_in_view(link_doc, view.Id, OST_StructuralFraming)
if not beams:
    print("No beams visible in view - check view settings")
```

### Selection tidak bekerja

Pastikan menggunakan Reference objects untuk linked elements:

```python
# Salah
selection.set_to([e.Id for e in linked_elements])

# Benar
refs = get_references_for_selection(linked_elements)
selection.set_to(refs)
```

## Lihat Juga

- `lib/smart_tag_engine.py` - Smart tag placement engine
- `logic-library/active/utilities/annotations/` - Annotation utilities
