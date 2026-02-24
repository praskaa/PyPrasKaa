# LOG-UTIL-PARAM-012-v1: Shared Parameter Creation Guide

## Overview

This document explains how to create and bind a shared parameter to Revit categories using the Revit API. The example is based on the "Revitesse Clouds" parameter creation logic found in the Clouds on Sheet script.

## Source Code Reference

**Source Script:** `Revitesse.extension/Revitesse.tab/Revitesse Revision Clouds.panel/Clouds on Sheet.pushbutton/script.py`

**Function:** `ensureRevitesseParameter()` (Lines 148-186)

## Parameter Details

| Attribute | Value |
|-----------|-------|
| Parameter Name | `Revitesse Clouds` |
| Parameter Group | `Project Parameters` |
| Data Type | String (Text) |
| Binding Type | Instance Binding |
| Categories | Views, Sheets |

## Step-by-Step Process

### Step 1: Open Shared Parameter File

```python
sharedParameterFilePath = app.SharedParametersFilename
sharedParameterFile = app.OpenSharedParameterFile()

if not sharedParameterFilePath or not sharedParameterFile:
    folder = os.path.dirname(doc.PathName) if doc.PathName else os.environ.get("TEMP")
    sharedParameterFilePath = os.path.join(folder, "sharedParameters.txt")
    if not os.path.exists(sharedParameterFilePath):
        with open(sharedParameterFilePath, 'w'): pass
    app.SharedParametersFilename = sharedParameterFilePath
    sharedParameterFile = app.OpenSharedParameterFile()
```

**Explanation:**
- Check if a shared parameter file is already configured in Revit
- If not configured, create a new file in the project folder or TEMP directory
- Set the file path and reopen it

### Step 2: Create or Get Parameter Group

```python
paramGroupName = "Project Parameters"
group = next((g for g in sharedParameterFile.Groups if g.Name == paramGroupName), None)
if not group: group = sharedParameterFile.Groups.Create(paramGroupName)
```

**Explanation:**
- Define the parameter group name
- Check if the group already exists
- Create a new group if it doesn't exist

### Step 3: Create or Get Parameter Definition

```python
paramName = "Revitesse Clouds"
definition = next((d for d in group.Definitions if d.Name == paramName), None)
if not definition:
    opt = ExternalDefinitionCreationOptions(paramName, SpecTypeId.String.Text)
    definition = group.Definitions.Create(opt)
```

**Explanation:**
- Define the parameter name
- Check if the definition already exists in the group
- Create a new external definition with String data type if not exists

**Available Spec Types:**
- `SpecTypeId.String.Text` - Text/String
- `SpecTypeId.Number` - Number
- `SpecTypeId.Integer` - Integer
- `SpecTypeId.Length` - Length
- `SpecTypeId.Area` - Area
- `SpecTypeId.Volume` - Volume
- `SpecTypeId.Boolean` - Yes/No
- And many more...

### Step 4: Create Category Set

```python
cats = CategorySet()
for cat in [doc.Settings.Categories.get_Item(BuiltInCategory.OST_Views), 
            doc.Settings.Categories.get_Item(BuiltInCategory.OST_Sheets)]:
    if cat.AllowsBoundParameters: cats.Insert(cat)
```

**Explanation:**
- Create a new CategorySet
- Add categories that allow bound parameters
- In this example: Views and Sheets

**Common BuiltInCategory values:**
| Category | BuiltInCategory |
|----------|------------------|
| Views | `OST_Views` |
| Sheets | `OST_Sheets` |
| Walls | `OST_Walls` |
| Doors | `OST_Doors` |
| Windows | `OST_Windows` |
| Rooms | `OST_Rooms` |
| Areas | `OST_Areas` |
| Revision Clouds | `OST_RevisionClouds` |

### Step 5: Bind Parameter to Document

```python
binding = InstanceBinding(cats)
t = Transaction(doc, "Bind Revitesse Clouds parameter")
t.Start()
if not isBound(paramName): 
    bindings.Insert(definition, binding, GroupTypeId.Text)
else: 
    bindings.ReInsert(definition, binding, GroupTypeId.Text)
t.Commit()
```

**Explanation:**
- Create an InstanceBinding (for per-element values)
- Use TypeBinding if you want per-type values
- Check if parameter is already bound
- Insert or ReInsert the binding
- Place in "Text" group (built-in parameter group)

**Binding Types:**
| Type | Use Case |
|------|----------|
| `InstanceBinding` | Different value per instance |
| `TypeBinding` | Same value for all instances of a type |

**GroupTypeId Options:**
| Group | GroupTypeId |
|-------|-------------|
| Text | `GroupTypeId.Text` |
| Identity Data | `GroupTypeId.IdentityData` |
| Phasing | `GroupTypeId.Phasing` |
| Graphics | `GroupTypeId.Graphics` |
| Material | `GroupTypeId.Material` |
| Dimensions | `GroupTypeId.Dimensions` |
| General | `GroupTypeId.General` |
| Analysis | `GroupTypeId.Analysis` |

## Helper Function: Check if Parameter is Bound

```python
def isBound(name):
    bindings = doc.ParameterBindings
    it = bindings.ForwardIterator()
    it.Reset()
    while it.MoveNext():
        if it.Key.Name.strip().lower() == name.strip().lower(): 
            return True
    return False
```

## Complete Function Template

```python
def ensureSharedParameter(doc, app, paramName, paramGroupName, categories):
    """
    Creates and binds a shared parameter to specified categories.
    
    Args:
        doc: Revit Document
        app: Revit Application
        paramName: Name of the parameter
        paramGroupName: Name of the parameter group
        categories: List of BuiltInCategory values
    
    Returns:
        bool: True if successful
    """
    import os
    from Autodesk.Revit.DB import *
    
    bindings = doc.ParameterBindings
    
    def isParameterBound(name):
        it = bindings.ForwardIterator()
        it.Reset()
        while it.MoveNext():
            if it.Key.Name.strip().lower() == name.strip().lower():
                return True
        return False
    
    # Step 1: Open or create shared parameter file
    sharedParameterFilePath = app.SharedParametersFilename
    sharedParameterFile = app.OpenSharedParameterFile()
    
    if not sharedParameterFilePath or not sharedParameterFile:
        folder = os.path.dirname(doc.PathName) if doc.PathName else os.environ.get("TEMP")
        sharedParameterFilePath = os.path.join(folder, "sharedParameters.txt")
        if not os.path.exists(sharedParameterFilePath):
            with open(sharedParameterFilePath, 'w'): pass
        app.SharedParametersFilename = sharedParameterFilePath
        sharedParameterFile = app.OpenSharedParameterFile()
    
    # Step 2: Create or get parameter group
    group = next((g for g in sharedParameterFile.Groups if g.Name == paramGroupName), None)
    if not group:
        group = sharedParameterFile.Groups.Create(paramGroupName)
    
    # Step 3: Create or get parameter definition
    definition = next((d for d in group.Definitions if d.Name == paramName), None)
    if not definition:
        opt = ExternalDefinitionCreationOptions(paramName, SpecTypeId.String.Text)
        definition = group.Definitions.Create(opt)
    
    # Step 4: Create category set
    cats = CategorySet()
    for cat in categories:
        category = doc.Settings.Categories.get_Item(cat)
        if category and category.AllowsBoundParameters:
            cats.Insert(category)
    
    # Step 5: Bind parameter
    binding = InstanceBinding(cats)
    t = Transaction(doc, "Bind {} parameter".format(paramName))
    t.Start()
    try:
        if not isParameterBound(paramName):
            bindings.Insert(definition, binding, GroupTypeId.Text)
        else:
            bindings.ReInsert(definition, binding, GroupTypeId.Text)
        t.Commit()
        return True
    except:
        t.RollBack()
        return False
```

## Usage Example

```python
from Autodesk.Revit.DB import BuiltInCategory

# Create the Revitesse Clouds parameter
ensureSharedParameter(
    doc=doc,
    app=app,
    paramName="Revitesse Clouds",
    paramGroupName="Project Parameters",
    categories=[BuiltInCategory.OST_Views, BuiltInCategory.OST_Sheets]
)
```

## Key Concepts

### 1. Idempotency
The function is designed to be idempotent - running it multiple times won't create duplicate parameters. It checks if the parameter already exists before creating.

### 2. Shared Parameter File
- Shared parameters are stored in external `.txt` files
- They must be created in the Shared Parameters file before binding
- The file path is configured in Revit Options > External Files

### 3. Transaction Required
All binding operations must be performed within a Revit Transaction.

### 4. Category Restrictions
Not all categories allow bound parameters. Always check `cat.AllowsBoundParameters` before adding to CategorySet.

## Related Documentation

- [LOG-UTIL-PARAM-001-v1-Parameter Finder](./LOG-UTIL-PARAM-001-v1-parameter-finder.py)
- [LOG-UTIL-PARAM-008-v1-Set Parameter Value](./LOG-UTIL-PARAM-008-v1-set-parameter-value.md)
- [LOG-UTIL-PARAM-009-v1-Standardized Parameter Setting Framework](./LOG-UTIL-PARAM-009-v1-standardized-parameter-setting-framework.md)

---

**Document Version:** 1.0  
**Created:** 2026-02-24  
**Source:** Revitesse.extension - Clouds on Sheet.pushbutton
