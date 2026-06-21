---
name: pyrevit
description: Expert guide for writing, debugging, and reviewing pyRevit scripts targeting the PrasKaaPyKitv2 personal toolkit. Use this skill whenever the user asks to write a new pyRevit button/script, debug an existing one, review API usage, fix a Revit API error, or asks about pyRevit patterns, Revit collector syntax, transaction handling, cross-version compatibility (2024/2025/2026), or IronPython 2.7 constraints. Also trigger when the user pastes a script and asks "what's wrong" or "why does this crash".
---

# pyRevit Skill — PrasKaaPyKitv2

## Context

- **Toolkit**: PrasKaaPyKitv2 — a personal pyRevit extension with push buttons, hooks, and a `lib/` shared library.
- **Runtime**: IronPython 2.7 (pyRevit). No CPython, no external pip packages.
- **Revit versions in use**: 2024, 2025, 2026. All scripts must be safe across all three unless the user explicitly targets one.
- **Author tag**: Every script must include `# Author: PrasKaa` near the top.
- **Output style**: Explanation first, then code. Keep explanations concise but precise. English only — all code comments, variable names, and output strings in English.

---

## Output Format

Always structure responses as:

1. **What's happening / why** — explain the API choice, the bug root cause, or the design decision.
2. **What to watch out for** — flag version differences, IronPython quirks, or common traps.
3. **Code** — clean, ready-to-run, with inline comments on non-obvious lines.

---

## Coding Conventions

### IronPython 2.7 Hard Rules

- No f-strings → use `.format()` or `%` formatting
- No walrus operator (`:=`)
- No type hints
- No external dependencies (`requests`, `pandas`, etc.)
- String formatting: `"Hello, {}".format(name)` not `f"Hello, {name}"`
- Use `unicode` carefully — prefer `str()` for Revit API string returns
- List comprehensions are fine; generator expressions are fine

### Script Header Template

```python
# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: <one-line description>
# Version: 1.0

from pyrevit import revit, DB, forms, script, output
doc = revit.doc
uidoc = revit.uidoc
```

### Minimal Surgical Changes
When editing existing scripts, make only the changes needed. Do not restructure, rename, or reformat untouched code. Preserve the author's style.

---

## Import Guidelines (pyRevit-only)

These scripts run only from the pyRevit UI; never standalone. Do **not** use `sys.path.append(os.path.join(...))`, `import os`, or path setup in pyRevit tools.

### Import order

1. Standard library
2. pyRevit / Revit API
3. Local `lib/` modules
4. Same-folder config / relative imports

### Do

```python
from pyrevit import revit, DB, forms, script

from lib.compat import get_element_id_value
from database import (
    get_param_value_as_string,
    p_storage_type,
    get_builtin_label
)
```

### Don't

- `from database import *`
- `sys.path.append(...)` in pyRevit scripts
- `import sys` / `import os` unless actually used
- `import database` followed by `database.func()` if only a few functions are used

---

## Revit API Patterns

### FilteredElementCollector

Always chain `.WhereElementIsNotElementType()` unless you explicitly need types.

```python
# CORRECT
walls = DB.FilteredElementCollector(doc)\
          .OfClass(DB.Wall)\
          .WhereElementIsNotElementType()\
          .ToElements()

# WRONG — returns both instances AND types
walls = DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements()
```

For category-based collection:
```python
cols = DB.FilteredElementCollector(doc)\
         .OfCategory(DB.BuiltInCategory.OST_Columns)\
         .WhereElementIsNotElementType()\
         .ToElements()
```

### Transaction Handling

Always use a standard `DB.Transaction`, not pyRevit's `ef_Transaction`, unless editing an existing script that already uses `ef_Transaction` (preserve conventions).

```python
t = DB.Transaction(doc, "Transaction Name")
t.Start()
try:
    # your changes
    t.Commit()
except Exception as e:
    t.RollbackIfPending()  # safer than t.Rollback() alone
    forms.alert("Error: {}".format(str(e)), exitscript=True)
```

**Never** open a transaction inside a loop that could trigger regeneration unpredictably. Open once, batch changes, commit once.

### ElementId — Cross-Version Compatibility

`ElementId.IntegerValue` was removed in Revit 2026. Always use the try/except pattern:

```python
def get_element_id_value(element_id):
    """Get integer value of ElementId, compatible with Revit 2024-2026."""
    try:
        return element_id.Value          # Revit 2026+
    except AttributeError:
        return element_id.IntegerValue   # Revit 2024-2025
```

Place this in `lib/compat.py` (see lib/ section below).

### Safe ElementId Usage

For callers needing a usable int, import `get_element_id_value` from `lib.compat.py`, or define the helper in the script if the helper cannot be added yet.

### Checking for Non-Existent API Members

Before using any property or method that isn't in the official docs or that you haven't verified, check it exists. Common traps:

- `LinkVisibility.Hidden` — **does not exist**. Use `view.HideElements([link_type_id])`.
- `Element.Name` on `RevitLinkType` — use `Element.Name.GetValue(element)` in IronPython.
- `OwnerViewId` — only valid on annotation/detail elements, not model elements.

---

## pyRevit UI Patterns

### Output Panel (for reports, diagnostics, logs)

```python
output = script.get_output()
output.print_html("<h3>Results</h3>")
output.print_html("<p>{} elements found.</p>".format(count))

# Clickable element link
output.print_html(output.linkify(element.Id, title=element.Name))
```

Use `<details>/<summary>` for collapsible sections in long reports:

```python
output.print_html("<details><summary>Sheet: {}</summary>".format(sheet_name))
output.print_html("...content...")
output.print_html("</details>")
```

### Forms (user interaction)

```python
# Simple alert
forms.alert("No elements selected.", exitscript=True)

# Pick one item from a list
chosen = forms.ask_for_one_item(
    item_list,
    prompt="Select an item:",
    title="PrasKaaPyKitv2"
)
if not chosen:
    script.exit()

# Yes/No confirmation
if not forms.alert("Proceed?", yes=True, no=True):
    script.exit()
```

**Do not** build WPF/XAML modeless dialogs for new scripts — use `output.print_html()` for rich display and `forms.*` for interaction.

---

## Cross-Version Strategy

All scripts must run on Revit 2024, 2025, and 2026 unless the user says otherwise.

**Pattern**: try the newer API first, fall back to the older one.

```python
# Example: API that changed between versions
try:
    result = new_api_call()       # 2026+
except AttributeError:
    result = old_api_call()       # 2024-2025
```

Flag in a comment when a block is version-specific:

```python
# Revit 2026+: Value replaces IntegerValue
try:
    id_val = eid.Value
except AttributeError:
    id_val = eid.IntegerValue  # 2024-2025 fallback
```

---

## IronPython Patterns

Prefer direct imports from `lib/` in pyRevit tools. Avoid unnecessary `sys.path` setup.

```python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
```

This pattern is generally not needed for pyRevit and should only remain where required for legacy compatibility or non-pyRevit execution paths.

---

## lib/ Shared Library

The `lib/` folder is for reusable helpers shared across scripts. Currently being built out — recommend creating modules as patterns repeat.

### When to create a module

- The same try/except compatibility block appears in 2+ scripts → move to `lib/compat.py`
- Color/override logic is reused → `lib/colorize.py`
- A collector pattern is used in 3+ places → `lib/collectors.py`

### Known modules (update this list as toolkit grows)

| Module | Purpose | Key contents |
|---|---|---|
| `lib/compat.py` | Cross-version API shims | `get_element_id_value(eid)` |

> **Maintainer note (Pras):** Update the table above whenever a new lib/ module is added to PrasKaaPyKitv2.

### Import patterns

**Preferred (direct imports):**

```python
from pyrevit import revit, DB, forms, script, output

from lib.compat import get_element_id_value
from database import get_param_value_as_string, p_storage_type
from colorize import get_colours, set_colour_overrides_by_option
```

**Old style (legacy compatibility only):**

```python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
from compat import get_element_id_value
```

### Keep-only-one rule

Keep **exactly one** canonical pattern in this skill. After this edit, the skill should stop listing both `from lib.X import ...` and the `sys.path.append(...)` form in multiple places. Use a single "Preferred" example and mention the old form only when explaining why it is being removed.

---

## Common Bugs Checklist

When debugging a script, run through this list first:

| # | Check | What to look for |
|---|---|---|
| 1 | Collector missing `.WhereElementIsNotElementType()` | Getting element types mixed with instances |
| 2 | `ElementId.IntegerValue` | Crashes on Revit 2026 — use `compat.get_element_id_value()` |
| 3 | Transaction not started before DB write | `Autodesk.Revit.Exceptions.InvalidOperationException` |
| 4 | Non-existent API property | `AttributeError` at runtime — verify against actual API |
| 5 | f-string used | `SyntaxError` in IronPython 2.7 |
| 6 | `t.Rollback()` called when transaction already committed | Use `t.RollbackIfPending()` |
| 7 | `Element.Name` on `RevitLinkType` | Use `Element.Name.GetValue(lt)` |
| 8 | Reading `OST_Viewports` for view parameters | Use `OST_Views` instead |

---

## Quick Reference: Revit API Gotchas

```python
# Get view name parameter (NOT OST_Viewports)
view_name = view.get_Parameter(DB.BuiltInParameter.VIEW_NAME).AsString()

# Hide elements in a view
view.HideElements(List[DB.ElementId]([elem_id]))  # pass a List, not a Python list

# IronPython: convert Python list to .NET List
from System.Collections.Generic import List
id_list = List[DB.ElementId]()
for eid in python_list:
    id_list.Add(eid)

# Get RevitLinkType name
link_name = DB.Element.Name.GetValue(link_type)

# Safe parameter read
param = element.get_Parameter(DB.BuiltInParameter.SOME_PARAM)
value = param.AsString() if param and param.HasValue else None
```
