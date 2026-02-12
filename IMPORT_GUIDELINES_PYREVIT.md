# Panduan Import Module untuk PyRevit Extension

> **Context:** Dokumentasi ini untuk pyRevit-only tools. Semua script hanya dijalankan dari pyRevit UI, tidak perlu standalone execution.

---

## 📋 Table of Contents

1. [Pattern Standar](#pattern-standar)
2. [Best Practices](#best-practices)
3. [Anti-Patterns yang Harus Dihindari](#anti-patterns-yang-harus-dihindari)
4. [Contoh Nyata: Benar vs Salah](#contoh-nyata-benar-vs-salah)
5. [Import Order yang Benar](#import-order-yang-benar)
6. [Checklist Refactoring](#checklist-refactoring)
7. [Tool Auto-Check](#tool-auto-check)

---

## Pattern Standar

### ✅ Template Dasar untuk PyRevit Button/Command

```python
"""
Deskripsi singkat tool ini.

CONTEXT: PyRevit UI tool - hanya dijalankan dari Revit interface
"""

# 1. Standard library imports
from collections import defaultdict

# 2. PyRevit imports
from pyrevit import revit, DB, forms, script
from pyrevit.revit.db import query

# 3. Revit API imports
from Autodesk.Revit import Exceptions

# 4. Local imports dari lib/ (explicit, bukan wildcard)
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME
from elements.element_names import get_family_name, get_type_name
from database import (
    get_param_value_as_string,
    p_storage_type,
    get_builtin_label
)

# Main logic
def main():
    """Main function untuk tool ini."""
    doc = revit.doc
    
    # Your code here
    pass

if __name__ == '__main__':
    main()
```

### 🔑 Mengapa Pattern Ini Benar?

1. **pyRevit Auto-adds Root Extension Folder**
   - pyRevit secara otomatis menambahkan root extension folder ke `sys.path`
   - Ini adalah **design intention** dari pyRevit framework
   - Tidak perlu `sys.path.append()` atau path manipulation

2. **Direct Import adalah Standar**
   - `from parameters.gis_categories import GIS_CATEGORIES` adalah **BENAR**
   - Ini bukan "pyRevit-only workaround" - ini adalah **best practice** pyRevit

3. **Explicit Imports untuk Clarity**
   - Tahu persis apa yang diimport
   - IDE auto-completion bekerja optimal
   - Mudah tracking dependencies

---

## Best Practices

### ✅ 1. Direct Import dari lib/

```python
# ✅ BENAR - Direct import
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME
from elements.element_names import get_family_name, get_type_name
from expUtils import expUtils_canPrint, expUtils_getDir
```

**Keuntungan:**
- Simple dan clean
- pyRevit handle path secara otomatis
- Standar di seluruh pyRevit ecosystem

### ✅ 2. Explicit Imports (Bukan Wildcard)

```python
# ❌ BURUK - Wildcard import
from database import *
from colorize import *

# ✅ BAIK - Explicit imports
from database import (
    get_param_value_as_string,
    p_storage_type,
    get_builtin_label
)

from colorize import (
    get_colours,
    set_colour_overrides_by_option,
    get_categories_config
)
```

**Keuntungan:**
- **Clarity** - Tahu persis apa yang digunakan
- **No Name Collision** - Hindari konflik namespace
- **IDE Support** - Auto-completion dan go-to-definition bekerja
- **Refactoring Safe** - Mudah tracking siapa pakai apa
- **Code Review** - Reviewer langsung tahu dependencies

### ✅ 3. Hapus Unused Imports

```python
# ❌ BURUK - Import tidak digunakan
import sys
import os

from pyrevit import revit, DB, forms
from database import get_value  # Tidak dipakai dalam code

# ✅ BAIK - Hanya import yang dipakai
from pyrevit import revit, DB, forms
```

**Cara Check:**
- Visual scan code
- Gunakan IDE warnings
- Run auto-check script (lihat bagian Tool Auto-Check)

### ✅ 4. Group Related Imports

```python
# ✅ BAIK - Grouped dan organized
from pyrevit import revit, DB, forms, script

# Multi-line untuk >3 imports
from database import (
    func1,
    func2,
    func3,
    func4
)
```

### ✅ 5. Konsisten di Seluruh Project

```python
# Semua scripts gunakan pattern yang sama
# KONSISTENSI adalah kunci maintainability
```

---

## Anti-Patterns yang Harus Dihindari

### ❌ 1. Wildcard Imports

```python
# ❌ BURUK
from database import *
from colorize import *

# Masalah:
# - Tidak tahu apa yang diimport
# - Bisa terjadi name collision
# - IDE tidak bisa auto-complete dengan baik
# - Sulit refactoring
```

**Fix:**
```python
# ✅ BAIK
from database import (
    get_param_value_as_string,
    p_storage_type
)
```

### ❌ 2. Unnecessary Path Setup untuk PyRevit

```python
# ❌ BURUK - Tidak perlu untuk pyRevit tools!
import sys
import os

lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from expUtils import expUtils_canPrint

# Masalah:
# - pyRevit SUDAH menambahkan root extension ke sys.path
# - Path manipulation ini REDUNDANT
# - Menambah complexity tanpa manfaat
# - Bisa menyebabkan duplicate paths di sys.path
```

**Fix:**
```python
# ✅ BAIK - Direct import
from expUtils import expUtils_canPrint
```

### ❌ 3. Unused Imports

```python
# ❌ BURUK
import sys  # Tidak digunakan
import os   # Tidak digunakan

from pyrevit import revit, DB, forms
```

**Fix:**
```python
# ✅ BAIK
from pyrevit import revit, DB, forms
```

### ❌ 4. Hardcoded Paths

```python
# ❌ BURUK - Tidak portable
sys.path.append('C:/Projects/PrasKaaPyKit/lib')

# Masalah:
# - Tidak akan berfungsi di komputer lain
# - Tidak akan berfungsi jika folder dipindah
# - Untuk pyRevit, ini tidak perlu sama sekali
```

**Fix:**
```python
# ✅ BAIK - Direct import (pyRevit handle path)
from expUtils import function
```

### ❌ 5. Import Modules Instead of Functions

```python
# ⚠️ KURANG BAIK
import database
import colorize

# Penggunaan:
value = database.get_param_value_as_string(param)
colors = colorize.get_colours()
```

**Better:**
```python
# ✅ LEBIH BAIK - Import fungsi langsung
from database import get_param_value_as_string
from colorize import get_colours

# Penggunaan lebih clean:
value = get_param_value_as_string(param)
colors = get_colours()
```

**Exception:** Import module jika banyak fungsi digunakan dan perlu namespace clarity:
```python
# ✅ OK jika banyak fungsi dan perlu namespace
import colorizebyvalueconfig as config

# Usage
config.SOME_CONSTANT
config.some_function()
```

---

## Contoh Nyata: Benar vs Salah

### 📁 1. Colorize by Value.pushbutton/script.py

#### ❌ SEBELUM (Salah):

```python
import sys  # ❌ import tidak digunakan

from pyrevit import revit, DB, forms
from pyrevit import script
from database import *  # ❌ Wildcard - tidak jelas apa yang diimport
from colorize import *   # ❌ Wildcard - tidak jelas apa yang diimport
import colorizebyvalueconfig
from collections import defaultdict
from pyrevit.revit.db import query
```

**Masalah:**
1. `import sys` tidak digunakan → Dead code
2. Wildcard import dari `database` → Tidak tahu apa yang diimport
3. Wildcard import dari `colorize` → Potensi name collision
4. Import order tidak terorganisir

#### ✅ SESUDAH (Benar):

```python
# Standard library
from collections import defaultdict

# PyRevit
from pyrevit import revit, DB, forms, script
from pyrevit.revit.db import query

# Local - Explicit imports
from database import (
    get_param_value_as_string,
    p_storage_type,
    get_builtin_label
)

from colorize import (
    get_colours,
    set_colour_overrides_by_option,
    get_categories_config
)

import colorizebyvalueconfig
```

**Perbaikan:**
- ✅ Hapus unused `sys` import
- ✅ Explicit imports - jelas apa yang digunakan
- ✅ Grouped imports by source
- ✅ Multi-line untuk readability

---

### 📁 2. Filters by Value.pushbutton/script.py

#### ❌ SEBELUM (Salah):

```python
import sys
import os

# ❌ Ini tidak perlu untuk pyRevit!
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), 'lib')
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

from pyrevit import revit, DB, forms
from pyrevit import script
import database  # ❌ Should be explicit
import colorize  # ❌ Should be explicit
from pyrevit.framework import List
import filterbyvalueconfig
from pyrevit.revit.db import query
from pyrevit.forms import reactive, WPF_VISIBLE, WPF_COLLAPSED
from Autodesk.Revit import Exceptions
```

**Masalah:**
1. **BIGGEST ISSUE:** sys.path manipulation tidak perlu untuk pyRevit
2. `sys` dan `os` hanya untuk path setup yang tidak diperlukan
3. Import `database` dan `colorize` as module, bukan fungsi spesifik
4. Import order tidak terorganisir

#### ✅ SESUDAH (Benar):

```python
# PyRevit
from pyrevit import revit, DB, forms, script
from pyrevit.framework import List
from pyrevit.revit.db import query
from pyrevit.forms import reactive, WPF_VISIBLE, WPF_COLLAPSED

# Revit API
from Autodesk.Revit import Exceptions

# Local - Explicit imports
from database import (
    p_storage_type,
    get_param_value_by_storage_type,
    get_builtin_label,
    check_filter_exists,
    filter_from_rules,
    create_filter_by_name_bics,
    shared_param_id_from_guid,
    get_name
)

from colorize import (
    get_colours,
    set_colour_overrides_by_option,
    get_categories_config
)

import filterbyvalueconfig
```

**Perbaikan:**
- ✅ Hapus seluruh path setup (tidak perlu)
- ✅ Hapus `sys` dan `os` imports
- ✅ Explicit imports dari `database` dan `colorize`
- ✅ Organized import order
- ✅ Grouped related imports

---

### 📁 3. Reset Overrides.pushbutton/script.py

#### ❌ SEBELUM (Salah):

```python
import sys  # ❌ import tidak digunakan

from pyrevit import revit, DB
from pyrevit import forms
from database import *  # ❌ Wildcard
```

**Masalah:**
1. Unused `sys` import
2. Wildcard import dari `database`
3. Ternyata setelah dicek, `database` **TIDAK DIGUNAKAN** sama sekali!

#### ✅ SESUDAH (Benar):

```python
from pyrevit import revit, DB, forms

# Tidak perlu import database - tidak ada fungsi yang digunakan!
```

**Perbaikan:**
- ✅ Hapus unused `sys` import
- ✅ Hapus wildcard import
- ✅ **DEAD CODE ELIMINATION** - Hapus import `database` yang tidak terpakai
- ✅ Simple dan clean

**Learning Point:**
- Ini menunjukkan pentingnya **audit actual usage**
- Jangan assume import diperlukan hanya karena ada di code
- Check apakah benar-benar digunakan

---

### 📁 4. Gistama UID Scripts (Sudah Benar ✅)

#### ✅ Generate.pushbutton/script.py

```python
"""Generate Gistama UID untuk elements."""

from pyrevit import revit, DB, forms, script

# Direct imports - INI SUDAH BENAR! ✅
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME
from elements.element_names import get_family_name, get_type_name

def main():
    doc = revit.doc
    # Logic here
    
if __name__ == '__main__':
    main()
```

**Ini adalah PATTERN STANDAR yang BENAR! ✅**

**Tidak perlu diubah karena:**
- Direct import dari lib/
- Explicit imports
- No wildcard
- No unnecessary path setup
- Clean dan readable

---

### 📁 5. Export Scripts (Perlu Perbaikan Kecil)

#### ⚠️ SEBELUM (Hampir Benar, tapi ada issue):

```python
import sys
import os

# ❌ Path setup tidak perlu untuk pyRevit
lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from pyrevit import forms, revit, DB, script
from expUtils import *  # ❌ Wildcard import
```

**Issues:**
1. Path setup tidak diperlukan
2. Wildcard import dari `expUtils`

#### ✅ SESUDAH (Benar):

```python
from pyrevit import forms, revit, DB, script

# Explicit imports
from expUtils import (
    expUtils_canPrint,
    expUtils_getDir,
    expUtils_getFolder,
    expUtils_ensureDir,
    expUtils_exportSheetDwg,
    expUtils_exportSheetPdf,
    expUtils_pdfOpts,
    expUtils_dwgOpts
)
```

**Perbaikan:**
- ✅ Hapus path setup (tidak perlu)
- ✅ Hapus `sys` dan `os` imports
- ✅ Ganti wildcard dengan explicit imports

---

## Import Order yang Benar

Ikuti **PEP 8 import order**:

```python
"""
Module docstring here.
"""

# 1. Standard library imports
from collections import defaultdict
import json

# 2. Third-party imports (pyRevit)
from pyrevit import revit, DB, forms, script
from pyrevit.framework import List
from pyrevit.revit.db import query
from pyrevit.forms import reactive, WPF_VISIBLE, WPF_COLLAPSED

# 3. Revit API imports
from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import FilteredElementCollector

# 4. Local application imports
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME
from elements.element_names import get_family_name, get_type_name

from database import (
    get_param_value_as_string,
    p_storage_type,
    get_builtin_label
)

from colorize import (
    get_colours,
    set_colour_overrides_by_option,
    get_categories_config
)

import colorizebyvalueconfig

# Blank line sebelum code
def main():
    pass
```

**Aturan:**
1. Standard library dulu
2. Kemudian third-party (pyRevit)
3. Kemudian Revit API
4. Terakhir local imports
5. Pisahkan setiap grup dengan blank line
6. Dalam grup, sort alphabetically (optional tapi recommended)

---

## Checklist Refactoring

Gunakan checklist ini sebelum commit code:

### 📋 Pre-Commit Checklist

```python
# ✅ CHECKLIST IMPORT REFACTORING

# 1. Unused imports?
import sys     # ← Dipakai? Kalau tidak → HAPUS ❌
import os      # ← Dipakai? Kalau tidak → HAPUS ❌

# 2. Wildcard imports?
from module import *  # ← Ada? → GANTI dengan explicit ❌

# 3. Unnecessary path setup? (untuk pyRevit)
sys.path.insert(0, ...)  # ← Untuk pyRevit tool? → HAPUS ❌

# 4. Import order benar?
# Standard lib → PyRevit → Revit API → Local ✅

# 5. Grouped imports?
from pyrevit import revit, DB, forms  # ✅ Good

# 6. Multi-line untuk >3 imports?
from database import (  # ✅ Good for readability
    func1,
    func2,
    func3
)

# 7. Dead code? Actual usage check
from database import *  # ← Benar-benar dipakai? Check! ⚠️

# 8. Import as module vs import functions?
import database  # ← Apakah lebih baik import fungsi spesifik? ⚠️

# 9. Konsisten dengan codebase lain?
# Pattern sama dengan scripts lain? ✅
```

### 🔍 How to Check

#### Manual Check:
```python
# 1. Search untuk wildcard
# Cari: "import *"

# 2. Search untuk unused imports
# Cari import, lalu cari usage-nya di file

# 3. Search untuk path setup
# Cari: "sys.path"

# 4. Visual scan import order
# Apakah terorganisir dengan baik?
```

#### IDE Check:
- **VS Code:** Unused imports akan abu-abu/dimmed
- **PyCharm:** Warning untuk unused imports
- **pylint/flake8:** Run linter untuk auto-detect

---

## Tool Auto-Check

### Script untuk Validasi Import

Simpan sebagai `check_imports.py`:

```python
"""
Auto-check import issues in Python files.

Usage:
    python check_imports.py script.py
    python check_imports.py *.py
    python check_imports.py **/*.py  # Recursive
"""

import ast
import sys
import os
from pathlib import Path

class ImportChecker(ast.NodeVisitor):
    """AST visitor untuk check import issues."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.issues = []
        self.warnings = []
        self.imports = []
        
    def visit_Import(self, node):
        """Check regular imports."""
        for alias in node.names:
            self.imports.append(alias.name)
            
            # Check for potentially unused sys/os
            if alias.name in ['sys', 'os']:
                self.warnings.append({
                    'line': node.lineno,
                    'type': 'potential_unused',
                    'message': f"Check if '{alias.name}' is actually used (often not needed for pyRevit)"
                })
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Check from...import statements."""
        module = node.module or ''
        
        for alias in node.names:
            # Check wildcard imports
            if alias.name == '*':
                self.issues.append({
                    'line': node.lineno,
                    'type': 'wildcard_import',
                    'message': f"Wildcard import from '{module}' - use explicit imports",
                    'severity': 'high'
                })
            
            # Check sys.path manipulation (likely in code, not import)
            if module == 'sys' and 'path' in alias.name:
                self.warnings.append({
                    'line': node.lineno,
                    'type': 'path_manipulation',
                    'message': "sys.path import detected - check if path manipulation is needed for pyRevit"
                })
        
        self.generic_visit(node)

def check_file(filepath):
    """Check single file untuk import issues."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        checker = ImportChecker(filepath)
        checker.visit(tree)
        
        # Check for sys.path in code (not just imports)
        if 'sys.path' in content:
            checker.warnings.append({
                'line': 0,
                'type': 'path_manipulation',
                'message': 'sys.path manipulation found in code - usually not needed for pyRevit tools'
            })
        
        return checker.issues, checker.warnings
        
    except Exception as e:
        return [], [{'line': 0, 'type': 'error', 'message': f"Error parsing file: {e}"}]

def print_results(filepath, issues, warnings):
    """Print check results."""
    if not issues and not warnings:
        print(f"✅ {filepath}: No issues found!")
        return
    
    print(f"\n📄 {filepath}:")
    
    if issues:
        print("  ❌ ISSUES (must fix):")
        for issue in issues:
            print(f"    Line {issue['line']}: {issue['message']}")
    
    if warnings:
        print("  ⚠️  WARNINGS (review needed):")
        for warning in warnings:
            line = f"Line {warning['line']}" if warning['line'] else "General"
            print(f"    {line}: {warning['message']}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Collect files
    files = []
    for pattern in sys.argv[1:]:
        if '*' in pattern:
            files.extend(Path('.').glob(pattern))
        else:
            files.append(Path(pattern))
    
    if not files:
        print("No files found!")
        sys.exit(1)
    
    # Check each file
    total_issues = 0
    total_warnings = 0
    
    for filepath in files:
        if filepath.suffix != '.py':
            continue
            
        issues, warnings = check_file(filepath)
        total_issues += len(issues)
        total_warnings += len(warnings)
        
        print_results(filepath, issues, warnings)
    
    # Summary
    print("\n" + "="*60)
    print(f"📊 SUMMARY:")
    print(f"  Files checked: {len(files)}")
    print(f"  Issues found: {total_issues}")
    print(f"  Warnings: {total_warnings}")
    
    if total_issues > 0:
        print("\n❌ Please fix the issues before committing!")
        sys.exit(1)
    elif total_warnings > 0:
        print("\n⚠️  Please review the warnings.")
    else:
        print("\n✅ All files look good!")

if __name__ == '__main__':
    main()
```

### Cara Menggunakan:

```bash
# Check single file
python check_imports.py script.py

# Check multiple files
python check_imports.py script1.py script2.py

# Check all Python files in directory
python check_imports.py *.py

# Check recursively
python check_imports.py **/*.py

# Check specific directory
python check_imports.py PrasKaaPyKit.tab/**/*.py
```

### Example Output:

```
📄 Colorize by Value.pushbutton/script.py:
  ❌ ISSUES (must fix):
    Line 5: Wildcard import from 'database' - use explicit imports
    Line 6: Wildcard import from 'colorize' - use explicit imports
  ⚠️  WARNINGS (review needed):
    Line 1: Check if 'sys' is actually used (often not needed for pyRevit)

📄 Generate.pushbutton/script.py:
✅ No issues found!

================================================================
📊 SUMMARY:
  Files checked: 2
  Issues found: 2
  Warnings: 1

❌ Please fix the issues before committing!
```

---

## 📁 Struktur Folder Reference

```
PrasKaaPyKitv2.extension/          # ← pyRevit auto-adds INI ke sys.path
├── lib/                            # ← Accessible via direct import
│   ├── parameters/
│   │   └── gis_categories.py      # from parameters.gis_categories import ...
│   ├── elements/
│   │   └── element_names.py       # from elements.element_names import ...
│   ├── database.py                # from database import ...
│   ├── colorize.py                # from colorize import ...
│   ├── expUtils.py                # from expUtils import ...
│   └── Snippets/
│       └── _selection.py          # from Snippets._selection import ...
│
└── PrasKaaPyKit.tab/
    └── Documentation.panel/
        └── col3.stack/
            ├── Gistama UID.pulldown/
            │   ├── Generate.pushbutton/
            │   │   └── script.py      # ✅ Direct import works!
            │   ├── Transfer.pushbutton/
            │   │   └── script.py
            │   └── SyncMark.pushbutton/
            │       └── script.py
            │
            ├── Colorize.pulldown/
            │   ├── Colorize by Value.pushbutton/
            │   │   └── script.py
            │   └── Reset Overrides.pushbutton/
            │       └── script.py
            │
            └── Export.pulldown/
                ├── SheetsDWG.pushbutton/
                │   └── SheetsDWG_script.py
                └── SheetsPDF.pushbutton/
                    └── SheetsPDF_script.py
```

**Key Point:**
- pyRevit adds `PrasKaaPyKitv2.extension/` to `sys.path`
- Semua yang di `lib/` bisa di-import langsung
- **TIDAK PERLU** path manipulation manual

---

## 📚 Common Questions (FAQ)

### Q1: Kenapa Gistama UID tidak perlu sys.path.append?

**A:** Karena pyRevit **otomatis** menambahkan root extension folder ke `sys.path`. Ini adalah design intention dari pyRevit framework.

```python
# pyRevit secara internal melakukan:
sys.path.insert(0, '/path/to/PrasKaaPyKitv2.extension')

# Sehingga kita bisa langsung:
from parameters.gis_categories import GIS_CATEGORIES  # ✅ Works!
```

### Q2: Kapan saya PERLU sys.path.append?

**A:** **HANYA** jika:
- Script dijalankan **OUTSIDE** pyRevit (standalone Python script)
- Import dari library yang **BUKAN** di extension folder
- Setup environment untuk unit testing

Untuk **pyRevit UI tools** → TIDAK PERNAH PERLU!

### Q3: Wildcard import selalu buruk?

**A:** Ya, **99% kasus wildcard adalah anti-pattern**. Pengecualian sangat jarang:
- Test files (kadang menggunakan `from module import *` untuk convenience)
- Interactive console/REPL

Untuk production code → **SELALU gunakan explicit imports**.

### Q4: Bagaimana dengan `import module` vs `from module import function`?

**A:** 
```python
# ⚠️ Kurang baik - perlu qualify setiap call
import database
value = database.get_param_value_as_string(param)  # Verbose

# ✅ Lebih baik - direct access
from database import get_param_value_as_string
value = get_param_value_as_string(param)  # Clean

# ✅ OK - jika perlu namespace clarity atau banyak fungsi
import colorizebyvalueconfig as config
config.SOME_CONSTANT
```

**Guideline:**
- Import fungsi langsung jika hanya beberapa fungsi
- Import module dengan alias jika banyak fungsi atau perlu namespace

### Q5: Bagaimana cara tahu import mana yang tidak dipakai?

**A:** Beberapa cara:
1. **IDE:** VS Code/PyCharm akan highlight unused imports
2. **Linter:** `pylint` atau `flake8` detect unused imports
3. **Auto-check script:** Gunakan tool yang disediakan di dokumentasi ini
4. **Manual:** Search import name di file - kalau tidak ada usage → hapus

### Q6: Apakah import order benar-benar penting?

**A:** Ya! Import order yang konsisten:
- Memudahkan code review
- Standar di Python community (PEP 8)
- Lebih mudah dibaca
- Hindari merge conflict

### Q7: Bagaimana dengan relative imports (`.` dan `..`)?

**A:** Untuk pyRevit extension:
```python
# ❌ Hindari relative imports
from ..lib.database import get_value

# ✅ Gunakan absolute imports
from database import get_value
```

Relative imports bisa membingungkan dan tidak perlu karena pyRevit sudah setup path dengan benar.

---

## 📋 Summary: Action Items untuk Project

### 1. ✅ KEEP - Scripts yang Sudah Benar

**Gistama UID Scripts:**
```python
# INI SUDAH PERFECT! ✅ Jangan diubah!
from parameters.gis_categories import GIS_CATEGORIES
from elements.element_names import get_family_name
```

### 2. 🔧 FIX - Wildcard Imports

**Export Scripts (SheetsDWG, SheetsPDF):**

```python
# SEBELUM:
from expUtils import *  # ❌

# SESUDAH:
from expUtils import (  # ✅
    expUtils_canPrint,
    expUtils_getDir,
    expUtils_ensureDir,
    expUtils_exportSheetDwg,
    expUtils_exportSheetPdf,
    expUtils_pdfOpts,
    expUtils_dwgOpts
)
```

**Colorize Scripts:**

```python
# SEBELUM:
from database import *  # ❌
from colorize import *  # ❌

# SESUDAH:
from database import (  # ✅
    get_param_value_as_string,
    p_storage_type,
    get_builtin_label
)

from colorize import (  # ✅
    get_colours,
    set_colour_overrides_by_option,
    get_categories_config
)
```

### 3. 🗑️ REMOVE - Path Setup

**Export Scripts:**

```python
# HAPUS seluruh blok ini:
import sys  # ❌
import os   # ❌

lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# Ganti dengan direct import seperti Gistama UID
```

**Filter Scripts:**

```python
# HAPUS seluruh path manipulation:
import sys  # ❌
import os   # ❌

script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(...)
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# Direct import sudah cukup!
```

### 4. 🧹 CLEANUP - Unused Imports

Semua scripts: Hapus import yang tidak digunakan
```python
# Check dan hapus:
import sys  # Dipakai? Kalau tidak → HAPUS
import os   # Dipakai? Kalau tidak → HAPUS
```

### 5. ✅ VERIFY - Run Auto-Check

```bash
# Setelah refactor, run check:
python check_imports.py PrasKaaPyKit.tab/**/*.py

# Harus keluar:
# ✅ All files look good!
```

---

## 🎯 Quick Reference Card

Print dan tempel di meja developer:

```
╔═══════════════════════════════════════════════════════════╗
║          PYREVIT IMPORT QUICK REFERENCE                   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ✅ DO:                                                   ║
║  • Direct import: from database import get_value         ║
║  • Explicit import: from module import func1, func2      ║
║  • Clean unused imports                                  ║
║  • Follow import order: stdlib → pyRevit → Revit → local ║
║                                                           ║
║  ❌ DON'T:                                                ║
║  • Wildcard: from module import *                        ║
║  • Path setup: sys.path.append(...) for pyRevit          ║
║  • Unused imports: import sys (unused)                   ║
║  • Hardcoded paths: sys.path.append('C:/...')            ║
║                                                           ║
║  📝 TEMPLATE:                                             ║
║  # Standard library                                      ║
║  from collections import defaultdict                     ║
║                                                           ║
║  # PyRevit                                                ║
║  from pyrevit import revit, DB, forms, script            ║
║                                                           ║
║  # Revit API                                              ║
║  from Autodesk.Revit import Exceptions                   ║
║                                                           ║
║  # Local                                                  ║
║  from database import get_value, set_value               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📚 Referensi

### Internal Documentation
- `ARCHITECTURE_GUIDE.md` - Arsitektur umum extension
- `CODING_STANDARDS.md` - Standar coding project

### External Resources
- [PEP 8 - Import Guidelines](https://pep8.org/#imports) - Python import standards
- [pyRevit Documentation](https://docs.pyrevitlabs.io/) - pyRevit framework docs
- [pyRevit GitHub](https://github.com/eirannejad/pyRevit) - Source code dan examples

### Tools
- [pylint](https://pylint.org/) - Python linter
- [flake8](https://flake8.pycqa.org/) - Style guide enforcement
- [black](https://black.readthedocs.io/) - Code formatter (optional)

---

## 📝 Changelog

### 2026-02-12
- ✅ Revisi total dokumentasi untuk pyRevit-only context
- ✅ Tambahkan contoh nyata dari project
- ✅ Tambahkan auto-check script
- ✅ Tambahkan FAQ section
- ✅ Tambahkan quick reference card
- ✅ Perbaiki penjelasan tentang path setup
- ✅ Clarify bahwa Gistama UID pattern sudah benar

### 2026-02-11
- Initial version (over-engineered untuk standalone context)

---

## 🤝 Contributing

Jika menemukan pattern baru atau improvement:

1. Diskusikan dengan tim
2. Update dokumentasi ini
3. Update auto-check script jika perlu
4. Share knowledge dengan team

---

## ⚠️ Important Notes

### pyRevit-Specific Behavior

**pyRevit OTOMATIS menambahkan root extension folder ke `sys.path`**

Ini berarti:
```python
# Struktur:
# PrasKaaPyKitv2.extension/
#   ├── lib/
#   │   └── database.py
#   └── PrasKaaPyKit.tab/
#       └── Tool.pushbutton/
#           └── script.py

# Di script.py, ini LANGSUNG WORKS:
from database import get_value  # ✅ pyRevit handle path

# TIDAK PERLU:
sys.path.insert(0, lib_path)  # ❌ Redundant!
```

### When Path Setup IS Needed

**HANYA untuk:**
- Standalone Python scripts (non-pyRevit)
- Unit tests
- Development utilities
- Scripts yang import dari OUTSIDE extension folder

**TIDAK PERNAH untuk:**
- pyRevit UI buttons/commands
- Tools yang dijalankan dari pyRevit interface

---

*Dokumentasi ini dibuat untuk membantu team developer maintain code quality yang konsisten. Untuk pertanyaan atau saran improvement, hubungi team lead.*

**Last Updated:** 2026-02-12  
**Version:** 2.0 (Revised for PyRevit-only context)  
**Status:** ✅ Production Ready
