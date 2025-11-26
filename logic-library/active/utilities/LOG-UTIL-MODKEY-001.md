---
id: LOG-UTIL-MODKEY-001
version: v1
status: active
category: utilities
element_type: n/a
operation: modifier-keys
revit_versions: [2024, 2026]
tags: [modifier-keys, shift-click, ctrl-click, pyrevit-ui, multi-mode]
created: 2025-10-10
updated: 2025-10-10
confidence: high
performance: fast
source_file: PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py
source_location: PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton
---

# Modifier Keys Detection for Multi-Mode pyRevit Buttons

## Problem Context
How to implement multi-mode functionality in pyRevit buttons using modifier keys (Shift+Click, Ctrl+Click) to access different features like settings or debug modes without adding extra UI elements.

## Solution Summary
Use `System.Windows.Forms.Control.ModifierKeys` to detect pressed modifier keys at button click time, allowing conditional execution of different code paths based on Shift, Ctrl, or Alt combinations.

## Working Code

```python
def main():
    """Main execution with modifier key support"""
    import System.Windows.Forms as WinForms

    # Check modifier keys
    if WinForms.Control.ModifierKeys == WinForms.Keys.Shift:
        # Shift+Click: Open settings
        execute_settings()
    else:
        # Normal/Ctrl+Click: Execute main tagging
        execute_main_tagging()
```

## Key Techniques
- Import `System.Windows.Forms` for access to modifier key detection
- Use `WinForms.Control.ModifierKeys` to check current modifier state
- Compare against `WinForms.Keys.Shift`, `WinForms.Keys.Control`, etc.
- Execute different functions based on modifier combination

## Revit API Compatibility
- Works with all Revit versions (2020+)
- No Revit API dependencies, pure .NET Windows Forms

## Performance Notes
- Instant detection, no performance impact
- Memory efficient, no additional objects created

## Usage Examples
- Shift+Click for settings/configuration dialogs
- Ctrl+Click for verbose/debug mode
- Alt+Click for alternative workflows

## Related Logic Entries
- None currently documented

## Source Information
- **Original Source**: PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py
- **Script Location**: PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton
- **Project Context**: Smart Tag System for structural element tagging
- **Date Created**: 2025-10-10
- **Author**: PrasKaa Team

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-10