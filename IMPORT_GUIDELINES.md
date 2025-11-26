# Panduan Import dan Best Practices PrasKaaPyKit

## Daftar Isi
1. [Prinsip Import](#prinsip-import)
2. [Import Patterns](#import-patterns)
3. [Directory Structure untuk Imports](#directory-structure-untuk-imports)
4. [Common Mistakes](#common-mistakes)
5. [Migration Examples](#migration-examples)
6. [Testing Imports](#testing-imports)

## Prinsip Import

### 🏗️ **Architecture Rules**
1. **Logic Library** = **TIDAK BOLEH di-import**
2. **Lib Folder** = **BOLEH di-import**
3. **Scripts** hanya import dari `lib/`
4. **Relative imports** untuk tool-specific code

### 🎯 **Import Hierarchy**
```
Scripts (pyRevit tools)
    ↓ import from
lib/ (shared utilities)
    ↓ import from
pyRevit API (.NET, Revit)
    ↓ import from
Python Standard Library
```

## Import Patterns

### ✅ **Correct Import Patterns**

#### **1. Import dari Lib Folder**
```python
# ✅ BENAR: Direct import dari lib
from Snippets.smart_selection import get_filtered_selection
from wall_orientation_logic import WallOrientationHandler
from parameters.framework import find_parameter_element
from graphicOverrides import setProjLines
```

#### **2. Import dengan Try/Except**
```python
# ✅ BENAR: Graceful import dengan fallback
try:
    from Snippets.smart_selection import get_filtered_selection
except ImportError:
    # Fallback implementation
    def get_filtered_selection(doc, uidoc, category_filter_func, **kwargs):
        """Fallback selection function"""
        return uidoc.Selection.GetElementIds()
```

#### **3. Import Multiple Functions**
```python
# ✅ BENAR: Import multiple dari satu module
from Snippets.smart_selection import (
    get_filtered_selection,
    create_single_category_filter,
    create_category_filter
)
```

#### **4. Import untuk Type Checking**
```python
# ✅ BENAR: Import untuk type hints
from typing import List, Dict, Optional
from Autodesk.Revit.DB import Element, Document
```

### ❌ **Incorrect Import Patterns**

#### **1. JANGAN Import dari Logic Library**
```python
# ❌ SALAH: Logic library hanya dokumentasi
sys.path.append('logic-library/active/utilities/selection')
from smart_selection import get_filtered_selection

# ❌ SALAH: Path manipulation yang rumit
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../logic-library/...'))
```

#### **2. JANGAN Import dengan Wildcard**
```python
# ❌ SALAH: Wildcard imports tidak direkomendasikan
from Snippets._selection import *
from parameters.framework import *
```

#### **3. JANGAN Circular Imports**
```python
# ❌ SALAH: Module A import B, B import A
# lib/module_a.py
from lib.module_b import function_b

# lib/module_b.py
from lib.module_a import function_a  # Circular!
```

## Directory Structure untuk Imports

### 📁 **Lib Folder Structure**
```
lib/
├── Snippets/                    # UI utilities
│   ├── __init__.py             # Package marker
│   ├── _selection.py           # Selection utilities
│   ├── _convert.py             # Conversion utilities
│   └── smart_selection.py      # Smart selection logic
├── parameters/                 # Parameter utilities
│   ├── __init__.py
│   ├── framework.py            # Main parameter framework
│   └── validators.py           # Parameter validation
├── wall_orientation_logic.py   # Wall orientation utilities
├── graphicOverrides.py         # Graphic override utilities
└── area_reinforcement.py       # Area reinforcement utilities
```

### 🔗 **Import Path Examples**

#### **Dari Tool Scripts**
```python
# Tool: PrasKaaPyKit.tab/Modeling.panel/Join.pulldown/Join.pushbutton/script.py
from Snippets.smart_selection import get_filtered_selection
from wall_orientation_logic import WallOrientationHandler
```

#### **Dari Lib Modules**
```python
# lib/Snippets/smart_selection.py
from Snippets._selection import get_selected_elements
from parameters.framework import find_parameter_element
```

#### **Dari Test Scripts**
```python
# tests/test_smart_selection.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.Snippets.smart_selection import get_filtered_selection
```

## Common Mistakes

### 🚨 **Mistake 1: Logic Library Imports**
```python
# ❌ WRONG - Scripts mengimport dari logic-library
sys.path.append('logic-library/active/utilities/selection')
from smart_selection import get_filtered_selection

# ✅ CORRECT - Import dari lib
from Snippets.smart_selection import get_filtered_selection
```

### 🚨 **Mistake 2: Hardcoded Paths**
```python
# ❌ WRONG - Hardcoded absolute paths
sys.path.append('C:/Projects/PrasKaaPyKit/lib')

# ✅ CORRECT - Relative paths atau direct imports
from Snippets.smart_selection import get_filtered_selection
```

### 🚨 **Mistake 3: Missing Error Handling**
```python
# ❌ WRONG - No error handling
from lib.custom_module import custom_function

# ✅ CORRECT - Graceful fallback
try:
    from lib.custom_module import custom_function
except ImportError:
    def custom_function(*args, **kwargs):
        return None
```

### 🚨 **Mistake 4: Import Order**
```python
# ❌ WRONG - Wrong import order
from my_custom_module import my_function  # Local first
import sys                               # Standard library
from pyrevit import revit               # Third-party

# ✅ CORRECT - Standard import order
import sys                               # 1. Standard library
from pyrevit import revit               # 2. Third-party
from Snippets.smart_selection import get_filtered_selection  # 3. Local lib
from config import MY_SETTINGS           # 4. Relative imports
```

## Migration Examples

### 🔄 **Contoh 1: Smart Selection Migration**

**Before (Wrong):**
```python
# script.py - OLD VERSION
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logic-library', 'active', 'utilities', 'selection'))
from smart_selection import get_filtered_selection

# Usage
walls = get_filtered_selection(doc, uidoc, lambda elem: isinstance(elem, Wall))
```

**After (Correct):**
```python
# script.py - NEW VERSION
from Snippets.smart_selection import get_filtered_selection

# Usage (unchanged)
walls = get_filtered_selection(doc, uidoc, lambda elem: isinstance(elem, Wall))
```

### 🔄 **Contoh 2: Wall Orientation Migration**

**Before (Wrong):**
```python
# script.py - OLD VERSION
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../logic-library/active/structural-elements/walls'))

try:
    from wall_orientation_logic import WallOrientationHandler
except ImportError:
    WallOrientationHandler = None
```

**After (Correct):**
```python
# script.py - NEW VERSION
try:
    from wall_orientation_logic import WallOrientationHandler
except ImportError:
    WallOrientationHandler = None
```

### 🔄 **Contoh 3: Parameter Framework Migration**

**Before (Wrong):**
```python
# script.py - OLD VERSION
import sys
sys.path.append(os.path.dirname(__file__))
try:
    from logic_library.active.utilities.parameters.LOG_UTIL_PARAM_001_v1_parameter_finder import find_parameter_element
except ImportError:
    find_parameter_element = None
```

**After (Correct):**
```python
# script.py - NEW VERSION
try:
    from parameters.framework import find_parameter_element
except ImportError:
    find_parameter_element = None
```

## Testing Imports

### 🧪 **Import Testing Script**
```python
# test_imports.py - Jalankan untuk test semua imports
import sys
import os

def test_import(module_path, function_name=None):
    """Test if import works correctly"""
    try:
        module = __import__(module_path, fromlist=[function_name] if function_name else [])
        if function_name:
            func = getattr(module, function_name)
            print(f"✅ {module_path}.{function_name} - OK")
            return True
        else:
            print(f"✅ {module_path} - OK")
            return True
    except ImportError as e:
        print(f"❌ {module_path} - FAILED: {e}")
        return False

# Test critical imports
tests = [
    ('Snippets.smart_selection', 'get_filtered_selection'),
    ('wall_orientation_logic', 'WallOrientationHandler'),
    ('parameters.framework', 'find_parameter_element'),
    ('graphicOverrides', 'setProjLines'),
]

print("Testing Imports...")
passed = 0
total = len(tests)

for module, func in tests:
    if test_import(module, func):
        passed += 1

print(f"\nResults: {passed}/{total} imports working")
```

### 🔍 **Debug Import Issues**
```python
# debug_imports.py - Untuk troubleshoot import problems
import sys
import os

print("Python Path:")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

print("\nCurrent Directory:", os.getcwd())

# Test specific import
try:
    from Snippets.smart_selection import get_filtered_selection
    print("✅ smart_selection import successful")
except ImportError as e:
    print(f"❌ smart_selection import failed: {e}")

# Check if file exists
import_path = os.path.join(os.path.dirname(__file__), 'lib', 'Snippets', 'smart_selection.py')
print(f"File exists: {os.path.exists(import_path)}")
```

### 📋 **Import Checklist**

#### **Untuk Setiap Tool Script**
- [ ] Import hanya dari `lib/` folder
- [ ] Tidak ada `sys.path.append` ke `logic-library/`
- [ ] Error handling untuk import failures
- [ ] Import order mengikuti standard
- [ ] Tidak ada wildcard imports

#### **Untuk Lib Modules**
- [ ] `__init__.py` ada di setiap package
- [ ] Relative imports menggunakan `.` atau `..`
- [ ] Tidak import dari `logic-library/`
- [ ] Function names descriptive dan konsisten

#### **Testing**
- [ ] Jalankan `test_imports.py` setelah changes
- [ ] Test di Revit environment
- [ ] Verify fallback mechanisms work
- [ ] Check console untuk import errors

## Best Practices Summary

### 📝 **Do's**
- ✅ Import dari `lib/` folder
- ✅ Use try/except untuk error handling
- ✅ Follow standard import order
- ✅ Test imports secara regular
- ✅ Document import dependencies

### 🚫 **Don'ts**
- ❌ Import dari `logic-library/`
- ❌ Use complex `sys.path` manipulation
- ❌ Wildcard imports
- ❌ Circular dependencies
- ❌ Hardcoded absolute paths

### 🛠️ **Tools & Scripts**
- `test_imports.py` - Test semua critical imports
- `debug_imports.py` - Troubleshoot import issues
- `ARCHITECTURE_GUIDE.md` - Comprehensive architecture docs
- Regular code reviews untuk import patterns

---

**Import Guidelines v1.0 - PrasKaaPyKit**
*Follow these rules to maintain clean, maintainable code architecture*