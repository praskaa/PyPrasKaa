# LOGIC LIBRARY: PARAM-GUIDE-001-v1

**Title:** Parameter Setting Framework Migration Guide
**Version:** 1.0
**Status:** Active
**Author:** Kilo Code
**Date:** 2025-10-24

---

## 1. Introduction

This guide provides a step-by-step process for migrating existing pyRevit scripts to use the new **Parameter Setting Framework**. The framework is designed to standardize parameter operations, improve robustness, and reduce boilerplate code. Adhering to this guide will ensure consistency and maintainability across the extension.

## 2. Why Migrate?

-   **Robustness:** The framework includes built-in validation, error handling, and transaction management, preventing common bugs.
-   **Consistency:** A single, unified API for all parameter setting operations.
-   **Performance:** Caching and batch processing strategies optimize performance for complex operations.
-   **Maintainability:** Centralized logic means improvements to the framework benefit all scripts that use it.

## 3. Migration Process

The migration process involves three main steps:

### Step 1: Import and Initialize the Framework

In your script's setup section, import the framework and initialize it with the current `doc` and `logger` objects.

**Before:**
```python
# No framework import
logger = script.get_logger()
```

**After:**
```python
# PyRevit imports
from pyrevit import revit, forms, script, output
from pyrevit.revit import doc, uidoc

# Parameter Setting Framework import
from lib.parameters import ParameterSettingFramework

# Setup
logger = script.get_logger()
output_window = output.get_output()

# Initialize Parameter Setting Framework
param_framework = ParameterSettingFramework(doc, logger)
```

### Step 2: Identify and Replace Parameter Setting Logic

Locate all instances of manual parameter setting. This typically involves finding `.LookupParameter()` followed by `.Set()`, often wrapped in a Revit `Transaction`.

**Before:**
```python
def set_parameter_value(element, param_name, new_value):
    param = element.LookupParameter(param_name)
    if not param:
        # ... error handling ...
        return False

    t = Transaction(doc, "Set Parameter Value")
    try:
        t.Start()
        storage_type = param.StorageType
        if storage_type == StorageType.Double:
            param.Set(float(new_value))
        # ... other type checks ...
        t.Commit()
        return True
    except Exception as e:
        # ... error handling ...
        t.RollBack()
        return False
```

### Step 3: Replace with a Framework Call

Replace the entire block of legacy code with a single call to the framework's `set_parameter` method.

**After:**
```python
def set_parameter_value(element, param_name, new_value):
    """
    Sets the value of a parameter using the standardized framework.
    """
    try:
        success = param_framework.set_parameter(
            element=element,
            param_name=param_name,
            value=new_value,
            validate=True  # Recommended for safety
        )
        return success
    except Exception as e:
        logger.error("Framework error setting parameter '{}': {}".format(param_name, str(e)))
        return False
```

## 4. Choosing an Optimization Level

The framework supports different optimization levels. For most single-operation UI scripts, the default (`OPTIMIZED`) is sufficient.

-   **`OptimizationLevel.BASIC`**: Use for simple, one-off operations where performance is not critical.
-   **`OptimizationLevel.OPTIMIZED`**: Default. Uses caching to speed up repeated operations on the same elements. Ideal for interactive scripts.
-   **`OptimizationLevel.BATCH`**: Use when setting parameters on many elements at once. This wraps all operations in a single transaction, providing a significant performance boost.

**Example (Batch Operation):**
```python
operations = [
    (element1, "Comments", "Value A"),
    (element2, "Comments", "Value B"),
    (element3, "Comments", "Value C")
]

param_framework.set_multiple_parameters(
    operations,
    optimization_level=OptimizationLevel.BATCH
)
```

## 5. Verification

After migrating a script, thoroughly test its functionality to ensure that:
1.  Parameters are set correctly for all data types.
2.  Error conditions (e.g., read-only parameters, invalid values) are handled gracefully.
3.  The script's performance is acceptable.

Consult the framework's test suite (`lib/parameters/tests.py`) for more examples of advanced usage and validation.