# Panduan Arsitektur PrasKaaPyKit

## Daftar Isi
1. [Prinsip Arsitektur](#prinsip-arsitektur)
2. [Struktur Direktori](#struktur-direktori)
3. [Logic Library vs Lib Folder](#logic-library-vs-lib-folder)
4. [Panduan Import](#panduan-import)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Prinsip Arsitektur

PrasKaaPyKit menggunakan arsitektur **modular** dengan pemisahan yang jelas antara:

### 🏗️ **Separation of Concerns**
- **Scripts** (`*.py` dalam folders tool) = Logic UI dan workflow
- **Lib** (`lib/` folder) = Shared utilities yang bisa di-import
- **Logic Library** (`logic-library/`) = Dokumentasi spesifikasi (tidak untuk import)

### 📚 **Layer Architecture**
```
┌─────────────────────────────────────┐
│           TOOL SCRIPTS              │ ← UI Logic, User Interaction
│          (pyRevit Tools)            │
├─────────────────────────────────────┤
│         SHARED LIBRARIES            │ ← Reusable Code, Utilities
│           (lib/ folder)             │
├─────────────────────────────────────┤
│       LOGIC SPECIFICATIONS         │ ← Documentation Only
│       (logic-library/ folder)       │
├─────────────────────────────────────┤
│         REVIT API LAYER            │ ← Autodesk Revit API
└─────────────────────────────────────┘
```

## Struktur Direktori

### 📁 **Root Structure**
```
PrasKaaPyKit.extension/
├── PrasKaaPyKit.tab/           # Main pyRevit tab
│   └── [Category].panel/       # Tool categories
│       └── [Tool].pulldown/    # Individual tools
│           ├── script.py       # 🟢 MAIN SCRIPT (executable)
│           ├── README.md       # 🟢 DOCUMENTATION
│           ├── bundle.yaml     # 🟢 CONFIGURATION
│           └── icon.png        # 🟢 ICON
├── lib/                        # 🟢 SHARED LIBRARIES (importable)
├── logic-library/              # 🔴 DOCUMENTATION ONLY (no import)
├── README.md                   # 🟢 MAIN DOCUMENTATION
├── CHANGELOG.md                # 🟢 VERSION HISTORY
└── ARCHITECTURE_GUIDE.md       # 🟢 THIS FILE
```

### 🏷️ **Color Coding**
- 🟢 **Green**: Files yang bisa dieksekusi/diakses langsung
- 🔴 **Red**: Files yang HANYA untuk dokumentasi (jangan import)

## Logic Library vs Lib Folder

### ❌ **Logic Library** (`logic-library/`)
**Tujuan**: Dokumentasi spesifikasi untuk development
**Status**: **TIDAK BOLEH di-import oleh scripts**
**Isi**: Markdown files dengan spesifikasi logic, contoh kode, design decisions

```
logic-library/
├── active/
│   ├── utilities/
│   │   ├── selection/
│   │   │   ├── smart_selection.py     # 🔴 HANYA DOKUMENTASI
│   │   │   └── LOG-UTIL-SELECTION-001-v1-smart-selection.md
│   │   └── parameters/
│   │       └── LOG-UTIL-PARAM-001-v1-parameter-finder.md
│   └── structural-elements/
│       └── walls/
│           └── wall_orientation_logic.py  # 🔴 HANYA DOKUMENTASI
└── sources/                           # Original implementations
```

### ✅ **Lib Folder** (`lib/`)
**Tujuan**: Shared code yang bisa di-import
**Status**: **BOLEH di-import oleh scripts**
**Isi**: Python modules yang berfungsi dan bisa digunakan

```
lib/
├── Snippets/
│   ├── _selection.py            # ✅ BISA DI-IMPORT
│   ├── _convert.py              # ✅ BISA DI-IMPORT
│   └── smart_selection.py       # ✅ BISA DI-IMPORT (copied from logic-lib)
├── parameters/
│   ├── framework.py             # ✅ BISA DI-IMPORT
│   └── validators.py            # ✅ BISA DI-IMPORT
├── wall_orientation_logic.py    # ✅ BISA DI-IMPORT (copied from logic-lib)
└── graphicOverrides.py         # ✅ BISA DI-IMPORT
```

## Panduan Import

### ✅ **Import Patterns yang Benar**

#### **1. Import dari Lib Folder**
```python
# ✅ BENAR: Import dari lib folder
from Snippets.smart_selection import get_filtered_selection
from wall_orientation_logic import WallOrientationHandler
from parameters.framework import find_parameter_element
from graphicOverrides import setProjLines
```

#### **2. Import dari pyRevit Standard**
```python
# ✅ BENAR: Import dari pyRevit
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *
```

#### **3. Relative Imports dalam Tool**
```python
# ✅ BENAR: Import dari folder yang sama
from config import MY_CONFIG
from utils import helper_function
```

### ❌ **Import Patterns yang Salah**

#### **1. JANGAN Import dari Logic Library**
```python
# ❌ SALAH: Jangan import dari logic-library
sys.path.append('logic-library/active/utilities/selection')
from smart_selection import get_filtered_selection  # ❌ VIOLATION
```

#### **2. JANGAN Import dengan sys.path.append yang kompleks**
```python
# ❌ SALAH: Hindari path manipulation yang rumit
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logic-library', 'active', 'utilities', 'selection'))
```

## Best Practices

### 🛠️ **Development Workflow**

#### **1. Untuk Menambah Utility Baru**
```
1. Buat spesifikasi di logic-library/
   ├── Tulis dokumentasi lengkap
   ├── Buat contoh kode
   ├── Tentukan API interface

2. Implementasi di lib/
   ├── Copy logic ke lib folder
   ├── Pastikan bisa di-import
   ├── Test functionality

3. Update scripts
   ├── Import dari lib folder
   ├── Gunakan utility yang sudah diimplement
```

#### **2. Untuk Menggunakan Utility Existing**
```python
# ✅ Selalu import dari lib, bukan logic-library
from Snippets.smart_selection import get_filtered_selection
from parameters.framework import set_parameter_value_safe
```

### 📝 **Coding Standards**

#### **1. Import Order**
```python
# 1. Standard library imports
import sys
import os

# 2. Third-party imports (pyRevit, .NET)
from pyrevit import revit, forms
from Autodesk.Revit.DB import *

# 3. Local lib imports
from Snippets.smart_selection import get_filtered_selection
from parameters.framework import find_parameter_element

# 4. Relative imports (if needed)
from config import MY_SETTINGS
```

#### **2. Error Handling untuk Imports**
```python
# ✅ BENAR: Graceful import dengan fallback
try:
    from Snippets.smart_selection import get_filtered_selection
except ImportError:
    # Fallback implementation
    def get_filtered_selection(*args, **kwargs):
        return []
```

### 🔍 **Code Organization**

#### **1. Utility Functions**
- Masukkan ke `lib/` jika reusable
- Gunakan naming yang konsisten
- Dokumentasikan dengan docstrings

#### **2. Tool-Specific Code**
- Tetap di folder tool masing-masing
- Import utilities dari `lib/`
- Minimal duplikasi kode

## Troubleshooting

### 🚨 **Common Issues**

#### **1. "Module not found" Error**
```python
# ❌ Jika dapat error ini
ImportError: No module named 'smart_selection'

# ✅ Periksa import path
from Snippets.smart_selection import get_filtered_selection  # Pastikan 'Snippets.'
```

#### **2. Logic Library Import Violation**
```python
# ❌ JANGAN lakukan ini
sys.path.append('logic-library/active/utilities/selection')
from smart_selection import get_filtered_selection

# ✅ Lakukan ini sebagai gantinya
from Snippets.smart_selection import get_filtered_selection
```

#### **3. Circular Import Issues**
- Pastikan tidak ada circular dependencies
- Gunakan lazy imports jika diperlukan
- Restrukturisasi code organization

### 🔧 **Migration Guide**

#### **Mengubah Import dari Logic Library ke Lib**

**Sebelum:**
```python
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logic-library', 'active', 'utilities', 'selection'))
from smart_selection import get_filtered_selection
```

**Sesudah:**
```python
from Snippets.smart_selection import get_filtered_selection
```

### 📋 **Checklist untuk New Tools**

#### **Pre-Development**
- [ ] Spesifikasi logic sudah ada di `logic-library/`?
- [ ] Utility yang dibutuhkan sudah ada di `lib/`?
- [ ] Dependencies sudah teridentifikasi?

#### **Development**
- [ ] Import hanya dari `lib/` folder
- [ ] Error handling untuk import failures
- [ ] Code mengikuti established patterns
- [ ] Documentation lengkap

#### **Testing**
- [ ] Tool bisa dijalankan tanpa error
- [ ] Import berhasil di semua environments
- [ ] Fallback mechanisms bekerja
- [ ] Performance acceptable

### 🎯 **Architecture Principles**

#### **1. Single Responsibility**
- Setiap utility punya satu tugas utama
- Tool scripts fokus pada UI/workflow
- Lib modules fokus pada reusable logic

#### **2. Dependency Inversion**
- High-level modules tidak depend pada low-level modules
- Abstraction interfaces di logic-library
- Implementation di lib folder

#### **3. Open/Closed Principle**
- Mudah untuk extend dengan utility baru
- Sulit untuk modify existing utilities
- Backward compatibility maintained

---

## 📞 Support

**Untuk pertanyaan arsitektur:**
- Baca dokumentasi di `logic-library/`
- Lihat contoh di existing tools
- Buat issue jika ada confusion

**Untuk development help:**
- Ikuti patterns di existing code
- Test thoroughly sebelum commit
- Update dokumentasi sesuai perubahan

---

**PrasKaaPyKit Architecture Guide v1.0**
*Terakhir update: November 2024*