# pyRevit Script Development Prompt Template

## 🎯 **Development Request**
[Deskripsikan apa yang ingin dibuat, contoh: "Buat script untuk export view templates ke CSV"]

## 🔧 **Technical Requirements**

### **Environment Constraints:**
- ✅ **pyRevit environment** (IronPython 2.7 based)
- ❌ **NO f-strings** (f"...") - use `.format()` instead
- ❌ **NO advanced Python 3+ features**
- ✅ **Manual file operations** preferred over complex modules

### **Import Pattern Required:**
```python
import clr
import os

# Add references BEFORE importing
clr.AddReference('System.Windows.Forms')
clr.AddReference('RevitAPI') 
clr.AddReference('RevitAPIUI')

# Import AFTER adding references
from System.Windows.Forms import MessageBox, SaveFileDialog, DialogResult
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

# Use pyRevit document access
from pyrevit import revit
doc = revit.doc
```

### **Code Style Guidelines:**
- ✅ Use `"text {}".format(variable)` instead of f-strings
- ✅ Use `open(file, 'w')` without encoding/newline parameters
- ✅ Manual CSV writing instead of csv module
- ✅ Simple error handling with try/except
- ✅ MessageBox for user feedback

### **File Structure Requirements:**
- ✅ Create proper folder structure: `Panel.panel/Stack.stack/Button.pushbutton/script.py`
- ✅ Include `bundle.yaml` files where needed
- ✅ Register panels in main tab's `bundle.yaml` layout
- ✅ Include `__title__`, `__author__` metadata

### **Testing Checklist:**
- [ ] Panel appears in pyRevit tab
- [ ] No syntax errors in pyRevit console
- [ ] Script runs without import errors
- [ ] File operations work correctly
- [ ] Error messages display properly

## 📝 **Additional Context**
[Tambahkan detail spesifik seperti naming convention, file format requirements, dll]

## 🎬 **Expected Deliverables**
- [ ] Working script file(s)
- [ ] Proper folder structure
- [ ] Basic error handling
- [ ] User-friendly feedback messages

---

**🚨 CRITICAL REMINDERS:**
- Always test imports first
- Use IronPython 2.7 compatible syntax only
- Avoid modern Python features
- Test panel registration before script functionality
