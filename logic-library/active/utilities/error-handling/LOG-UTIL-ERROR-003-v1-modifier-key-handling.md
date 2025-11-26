---
id: "LOG-UTIL-ERROR-003"
version: "v1"
status: "active"
category: "utilities/error-handling"
element_type: "UserInput"
operation: "handle"
revit_versions: [2024, 2026]
tags: ["ui", "input", "modifier", "shift", "ctrl", "behavior"]
created: "2025-10-10"
updated: "2025-10-10"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py"
source_location: "Helper.panel/SmartTag.pushbutton"
---

# LOG-UTIL-ERROR-003-v1: Modifier Key Behavior Switching

## Problem Context

pyRevit buttons typically have a single action, but users often need different behaviors from the same button (settings vs execution, verbose vs quiet mode, etc.). Modifier keys (Shift, Ctrl, Alt) provide a way to access alternative behaviors without cluttering the UI with multiple buttons.

## Solution Summary

This pattern checks for modifier key states when the script starts and switches behavior accordingly. It uses `System.Windows.Forms.Control.ModifierKeys` to detect Shift, Ctrl, and Alt key combinations, allowing different execution paths based on user input.

## Working Code

```python
import System.Windows.Forms as WinForms

def main():
    """Main execution with modifier key support"""
    # Check modifier keys for different behaviors
    modifier_keys = WinForms.Control.ModifierKeys

    if modifier_keys == WinForms.Keys.Shift:
        # Shift+Click: Alternative behavior (e.g., settings)
        execute_settings_mode()
    elif modifier_keys == WinForms.Keys.Control:
        # Ctrl+Click: Verbose/debug mode
        execute_verbose_mode()
    elif modifier_keys == (WinForms.Keys.Control | WinForms.Keys.Shift):
        # Ctrl+Shift+Click: Advanced/debug mode
        execute_advanced_mode()
    else:
        # Normal click: Default behavior
        execute_normal_mode()

# Alternative implementation using flags
def check_modifier_keys():
    """Check individual modifier keys and return behavior flags"""
    modifier_keys = WinForms.Control.ModifierKeys

    is_shift = (modifier_keys & WinForms.Keys.Shift) == WinForms.Keys.Shift
    is_ctrl = (modifier_keys & WinForms.Keys.Control) == WinForms.Keys.Control
    is_alt = (modifier_keys & WinForms.Keys.Alt) == WinForms.Keys.Alt

    return {
        'shift': is_shift,
        'ctrl': is_ctrl,
        'alt': is_alt,
        'shift_ctrl': is_shift and is_ctrl,
        'shift_alt': is_shift and is_alt,
        'ctrl_alt': is_ctrl and is_alt,
        'shift_ctrl_alt': is_shift and is_ctrl and is_alt
    }

def execute_based_on_modifiers():
    """Execute different behaviors based on modifier combinations"""
    modifiers = check_modifier_keys()

    if modifiers['shift_ctrl_alt']:
        # Shift+Ctrl+Alt: Nuclear option
        execute_nuclear_mode()
    elif modifiers['shift_ctrl']:
        # Shift+Ctrl: Advanced settings
        execute_advanced_settings()
    elif modifiers['shift_alt']:
        # Shift+Alt: Alternative execution
        execute_alternative_mode()
    elif modifiers['ctrl_alt']:
        # Ctrl+Alt: Debug mode
        execute_debug_mode()
    elif modifiers['shift']:
        # Shift: Settings
        execute_settings_mode()
    elif modifiers['ctrl']:
        # Ctrl: Verbose
        execute_verbose_mode()
    elif modifiers['alt']:
        # Alt: Quiet mode
        execute_quiet_mode()
    else:
        # No modifiers: Normal
        execute_normal_mode()
```

## Key Techniques

1. **Modifier Key Detection**: Uses `WinForms.Control.ModifierKeys` to read current key state
2. **Bitwise Operations**: Checks for specific key combinations using bitwise AND
3. **Behavior Switching**: Clean separation of execution paths based on modifiers
4. **Flag-based Checking**: Alternative approach using individual key flags for complex combinations

## Revit API Compatibility

- **Windows Forms**: Uses `System.Windows.Forms.Control.ModifierKeys` which is stable
- **No Revit API Dependencies**: Pure input handling pattern
- **Cross-platform**: Works on Windows (Revit's platform)

## Performance Notes

- **Execution Time**: Instant - just a few bitwise operations
- **Memory Usage**: Minimal - no additional allocations
- **Thread Safety**: Must be called from UI thread (pyRevit buttons are UI-threaded)

## Usage Examples

### Basic Settings vs Execution
```python
def main():
    if WinForms.Control.ModifierKeys == WinForms.Keys.Shift:
        # Shift+Click: Open settings
        show_settings_dialog()
    else:
        # Normal click: Execute main function
        execute_main_process()
```

### Verbose vs Quiet Mode
```python
def process_data():
    verbose = (WinForms.Control.ModifierKeys == WinForms.Keys.Control)

    if verbose:
        print("Starting data processing in VERBOSE mode...")
        # Enable detailed logging
        logger.setLevel(DEBUG)
    else:
        # Quiet mode
        logger.setLevel(ERROR)

    # Process data...
    result = process_data_internal(verbose)
    return result
```

### Multiple Behavior Options
```python
def handle_button_click():
    modifiers = WinForms.Control.ModifierKeys

    if modifiers == (WinForms.Keys.Control | WinForms.Keys.Shift):
        # Ctrl+Shift: Export data
        export_data_to_file()
    elif modifiers == WinForms.Keys.Control:
        # Ctrl: Show preview
        show_data_preview()
    elif modifiers == WinForms.Keys.Shift:
        # Shift: Configure options
        show_configuration_dialog()
    else:
        # Normal: Process data
        process_data()
```

## Common Pitfalls

1. **Key Constants**: Use `WinForms.Keys.Shift`, not just `Keys.Shift`
2. **Bitwise AND**: Use `&` operator for checking key combinations
3. **UI Thread**: Modifier key checking only works on UI thread
4. **Key Release**: Check keys at button click time, not script start

## Related Logic Entries

- [LOG-UTIL-ERROR-001-v1-graceful-api-failures](LOG-UTIL-ERROR-001-v1-graceful-api-failures.md) - Error handling patterns
- [LOG-UTIL-ERROR-002-v1-user-friendly-messages](LOG-UTIL-ERROR-002-v1-user-friendly-messages.md) - User feedback

## Optimization History

*This is the initial version (v1) with no optimizations yet.*