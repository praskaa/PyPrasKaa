# Plan Refactoring: Boolean Geometry Matching
## Consolidating All Duplicate Code into Shared Module

---

## 1. Current State Analysis

### Scripts with Duplicate Boolean Geometry Functions

| Script Location | Functions to Consolidate |
|----------------|------------------------|
| EXR_Framing.pulldown/* | `get_solid()`, `find_best_match()`, `select_linked_model()` |
| EXR_Column.pulldown/* | `get_solid()`, `find_best_match()`, `select_linked_model()` |
| **Gistama UID.pulldown/Transfer** | `get_transformed_solid()`, `find_best_match()`** |
| Validation.pulldown/AutoLoadMissingTypes | `select_linked_model()` |

**Note: Gistama UID script already uses shared modules for element names**

### Functions with High Duplication (All Scripts Combined)

| Function | Occurrences | Description |
|----------|-------------|-------------|
| `get_solid()` / `get_transformed_solid()` | 9 | Extract solid geometry from element |
| `select_linked_model()` | 9 | Select linked Revit model |
| `find_best_match()` | 8 | Find matching by intersection volume |
| `debug_log()` | 3 | Smart logging with debug levels |
| `feet3_to_mm3()` | 3 | Volume unit conversion |

---

## 2. Proposed Architecture

### Single Unified Module: `lib/linked_geometry.py`

```python
# lib/linked_geometry.py
"""
Linked Model Geometry Utilities - Unified Module for Boolean Geometry Matching

This module provides shared utilities for:
- Extracting solid geometry from elements
- Finding best matches between host and linked elements
- Managing linked model selection and validation

Usage:
    from lib.linked_geometry import (
        get_solid,
        find_best_match,
        select_linked_model,
        create_geometry_options
    )
"""
```

### Module Structure

```python
# lib/linked_geometry.py

# === Geometry Options ===
def create_geometry_options(doc)
def get_solid(element, options=None)
def get_transformed_solid(element, options=None, transform=None)

# === Matching ===
def find_best_match(host_solid, linked_elements_dict)
def find_best_match_with_validation(host_element, linked_elements_dict, validate_func)

# === Unit Conversion ===
FEET3_TO_MM3 = 28316846.592
def feet3_to_mm3(volume_cu_ft)
def mm3_to_feet(volume_mm3)

# === Debug Utilities ===
def debug_log(message, level='NORMAL', force=False)
```

### Supporting Module: `lib/linked_model.py`

```python
# lib/linked_model.py

# === Linked Model Selection ===
def select_linked_model(doc, title='Select Linked Model')
def get_linked_document(selected_link)
def validate_linked_model(link_doc)
def get_link_transform(selected_link)

# === Element Collection ===
def collect_by_categories(doc, categories, selection_ids=None)
def collect_structural_framing(doc, selection_ids=None)
def collect_structural_columns(doc, selection_ids=None)
```

---

## 3. Migration Steps

### Phase 1: Create Shared Modules
- [ ] Create `lib/linked_geometry.py` with all geometry functions
- [ ] Create `lib/linked_model.py` with linked model utilities
- [ ] Add unit tests (optional)

### Phase 2: Update Each Script

#### Priority 1: Gistama UID (Already has clean structure!)
- [ ] Replace `get_transformed_solid()` with import
- [ ] Replace `find_best_match()` with import

#### Priority 2: EXR_Framing Tools
- [ ] CheckFramingDimensions.pushbutton/script.py
- [ ] MatchingFraming.pushbutton/script.py
- [ ] TransferMarkWithOverride.pushbutton/script.py
- [ ] TransferMarkWithRevitModel.pushbutton/script.py
- [ ] TransferMarkManual.pushbutton/script.py
- [ ] TransferETABSGUIDManual.pushbutton/script.py
- [ ] TransferMarkByGUID.pushbutton/script.py
- [ ] PreRunMatchingDimension.pushbutton/script.py

#### Priority 3: EXR_Column Tools
- [ ] CheckColumnDimensions.pushbutton/script.py
- [ ] MatchingColumn_v2.pushbutton/script.py
- [ ] TransferTypeMarkAndMark_v2.pushbutton/script.py
- [ ] PreRunMatchingDimension.pushbutton/script.py

#### Priority 4: Other Tools
- [ ] Validation.pulldown/AutoLoadMissingTypes

---

## 4. Import Pattern After Refactoring

### Before (Current - Duplicated ~50 lines per script)
```python
def get_solid(element):
    # ... 30-50 lines of geometry extraction code
    
def find_best_match(host_element, linked_dict):
    # ... 20-30 lines of matching code
```

### After (Single Import)
```python
# At top of script.py
from lib.linked_geometry import (
    get_solid,
    get_transformed_solid,
    find_best_match,
    FEET3_TO_MM3,
    feet3_to_mm3,
    create_geometry_options
)

from lib.linked_model import (
    select_linked_model,
    get_linked_document,
    collect_structural_framing
)
```

---

## 5. Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Lines of duplicate code | ~3000 | ~500 |
| Maintenance | Update each file | Update one module |
| Bugs | Fix in 10+ places | Fix in 1 place |
| Consistency | Varying implementations | Unified approach |

---

## 6. Effort Estimate

| Phase | Task | Estimated Time |
|-------|------|-----------------|
| Phase 1 | Create modules | 2-3 hours |
| Phase 2 | Update Gistama UID | 30 min |
| Phase 3 | Update EXR_Framing (8 scripts) | 3-4 hours |
| Phase 4 | Update EXR_Column (3 scripts) | 2 hours |
| Phase 5 | Update other tools | 1 hour |
| | **Testing** | 2-3 hours |
| | **Total** | **~10-13 hours** |

---

## 7. Backward Compatibility

- Keep local functions as aliases during transition
- Add deprecation warnings in v1.1
- All scripts will work immediately after update

---

## Next Steps

1. ✅ Plan approved by user
2. ⏳ Start Phase 1: Create shared modules
3. ⏳ Proceed with migration script by script

---

## Files to Modify

```
lib/
├── linked_geometry.py     # NEW - geometry utilities
├── linked_model.py       # NEW - linked model utilities
└── geometry_matching.py  # KEEP - existing, extend if needed
```

```
PrasKaaPyKit.tab/
├── Documentation.panel/col3.stack/Gistama UID.pulldown/Transfer.pushbutton/
│   └── script.py         # UPDATE - use lib/linked_geometry
├── QualityControl.panel/
│   ├── EXR_Framing.pulldown/    # UPDATE - 8 scripts
│   └── EXR_Column.pulldown/    # UPDATE - 3 scripts
└── Validation.pulldown/        # UPDATE - 1 script
```
