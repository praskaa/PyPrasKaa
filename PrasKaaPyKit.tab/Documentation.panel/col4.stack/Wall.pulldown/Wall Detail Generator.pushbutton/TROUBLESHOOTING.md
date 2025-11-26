# Wall Plan Generator - Troubleshooting Guide

## Common Issues & Solutions

### 1. "No walls found with valid classifications"

#### Symptoms
- Script shows "No walls found with valid classifications"
- Classification summary shows 0 classified walls
- All walls appear as unclassified

#### Causes & Solutions

**Cause 1: Missing Parameter**
```
Error: Parameter "Wall Scheme Classification" not found
```
**Solution:**
- Check if parameter exists in your Revit project
- Verify spelling: `"Wall Scheme Classification"` (case-sensitive)
- Add parameter if missing

**Cause 2: Empty Parameter Values**
```
Debug: Classification is None - returning None
```
**Solution:**
- Check that walls have values in the classification parameter
- Fill empty parameter values
- Use project browser to filter walls with empty classifications

**Cause 3: Parameter Type Mismatch**
```
Debug: Classification is not string (type: <type 'int'>)
```
**Solution:**
- Ensure parameter is text type (not number/integer)
- Convert existing values to text if needed

### 2. "View creation failed"

#### Symptoms
- Script creates classification summary but fails on view creation
- Error messages about view creation
- Some views created, others failed

#### Causes & Solutions

**Cause 1: Invalid Wall Geometry**
```
Error: Could not process wall: No valid Location.Curve
```
**Solution:**
- Check wall has valid geometry (not just symbolic lines)
- Repair or recreate problematic walls
- Use "Warnings" dialog in Revit to identify geometry issues

**Cause 2: Level Issues**
```
Error: Selected level not found in document
```
**Solution:**
- Verify selected level still exists
- Check level is not hidden or filtered
- Re-select level in the level selection dialog

**Cause 3: Duplicate View Names**
```
Error: View name already exists
```
**Solution:**
- Script auto-handles this with numbering (View Name (1), etc.)
- Manual cleanup of conflicting views if needed

### 3. "Script runs but no output shown"

#### Symptoms
- Script appears to run but no results displayed
- pyRevit output window is empty
- No error messages

#### Causes & Solutions

**Cause 1: Debug Mode Disabled**
```
DEBUG_MODE = False (but no output visible)
```
**Solution:**
- Check that `DEBUG_MODE = False` in script.py
- Ensure script completes successfully (check pyRevit console)
- Look for output in pyRevit output window

**Cause 2: Early Exit**
```
Script exits before displaying results
```
**Solution:**
- Enable debug mode temporarily to see where script stops
- Check for unhandled exceptions
- Verify all required inputs are provided

### 4. "Parameter extraction fails"

#### Symptoms
- Debug shows parameter extraction failures
- Walls classified as unclassified despite having parameter values

#### Causes & Solutions

**Cause 1: Shared Parameter Issues**
```
Debug: Instance parameter not found, trying type parameter
```
**Solution:**
- Ensure shared parameter is properly loaded in project
- Check parameter binding (instance vs type)
- Verify parameter group and category bindings

**Cause 2: Parameter Storage Type**
```
Debug: Unexpected storage type: ElementId
```
**Solution:**
- Change parameter type to Text if currently ElementId/Number
- Update existing values accordingly

### 5. Performance Issues

#### Symptoms
- Script takes unusually long to run
- Progress bar moves very slowly
- Memory usage spikes

#### Causes & Solutions

**Cause 1: Large Selection**
```
Processing 500+ walls takes >30 seconds
```
**Solution:**
- Process walls in smaller batches
- Close other Revit views to free memory
- Consider splitting large projects into sections

**Cause 2: Complex Geometry**
```
Walls with many curves/arcs slow processing
```
**Solution:**
- Simplify wall geometry where possible
- Process complex walls separately
- Enable debug mode to identify slow elements

## Debug Mode Usage

### Enabling Debug Mode

```python
# In script.py, change:
DEBUG_MODE = True  # Enable detailed debug output
```

### Interpreting Debug Output

#### Parameter Extraction Debug
```
[WALL_DEBUG] ID:2637683 Type:'Basic Wall' - === STARTING CLASSIFICATION EXTRACTION ===
[WALL_DEBUG] ID:2637683 Type:'Basic Wall' - Step 1: Checking instance parameter
[WALL_DEBUG] ID:2637683 Type:'Basic Wall' - Instance parameter found: HasValue=True, StorageType=String
DEBUG get_parameter_value: Raw string value = 'W1'
[WALL_DEBUG] ID:2637683 Type:'Basic Wall' - Instance parameter RAW value: 'W1' (type: <type 'str'>)
[WALL_DEBUG] ID:2637683 Type:'Basic Wall' - String processing: 'W1' -> 'W1' after strip
[WALL_DEBUG] ID:2637683 Type:'Basic Wall' - Returning valid classification: 'W1'
```

**What to check:**
- Parameter found at correct level (instance/type)
- Storage type is String
- Value is not None/empty after processing

#### View Creation Debug
```
DEBUG: Creating plan view 'Basic Wall-W5-L16 FL' at level 'L16 FL'
DEBUG: ViewPlan created successfully, Id: 3515431
DEBUG: Calculated bounding box:
Min: (106.09, 77.54, 251.62)
Max: (116.68, 100.60, 262.62)
DEBUG: Crop region applied successfully
```

**What to check:**
- View name generation works
- View creation succeeds
- Bounding box coordinates are reasonable
- Crop region application succeeds

## Advanced Troubleshooting

### Using Revit Built-in Tools

#### 1. Check Parameter Values
- Use **Schedule** to view parameter values
- Filter for walls with empty classifications
- Sort by classification to see distribution

#### 2. Validate Geometry
- Use **Warnings** dialog to check geometry issues
- Select problematic walls and check properties
- Use **Section Box** to verify 3D extents

#### 3. Monitor Performance
- Use **Task Manager** to monitor memory usage
- Check **Revit Performance Advisor** for recommendations
- Close unnecessary views and families

### Script-Level Debugging

#### 1. Isolate Components
```python
# Test individual components
from wall_classifier import WallClassifier
classifier = WallClassifier(selected_walls)
groups = classifier.classify_walls()
print("Classification results:", groups)
```

#### 2. Step-by-Step Execution
```python
# Run script sections individually
# 1. Test parameter extraction
# 2. Test classification logic
# 3. Test view creation
# 4. Test crop region setting
```

### Common Parameter Issues

#### Shared Parameter Problems
```python
# Check if shared parameter is loaded
shared_params = FilteredElementCollector(doc)\
    .OfClass(SharedParameterElement)\
    .ToElements()

for param in shared_params:
    if param.Name == "Wall Scheme Classification":
        print("Parameter found:", param.GuidValue)
```

#### Parameter Binding Issues
```python
# Check parameter binding
param_elem = find_parameter_element(doc, "Wall Scheme Classification")
if param_elem:
    definition = param_elem.GetDefinition()
    print("Parameter binding:", definition.ParameterGroup)
    print("Categories:", [cat.Name for cat in definition.Categories])
```

## Recovery Procedures

### 1. Clean Restart
1. Close Revit completely
2. Restart Revit
3. Reload pyRevit extension
4. Test with small wall selection first

### 2. Parameter Reset
1. Create backup of current parameter values
2. Clear problematic parameter values
3. Re-run script to re-populate
4. Restore values if needed

### 3. View Cleanup
1. Delete failed views manually
2. Check for naming conflicts
3. Verify level existence
4. Re-run script with clean state

## Prevention Best Practices

### 1. Parameter Management
- Use consistent parameter naming
- Set up parameters before running script
- Validate parameter values regularly
- Document parameter requirements

### 2. Model Quality
- Maintain clean wall geometry
- Avoid overly complex wall shapes
- Use consistent level naming
- Regular model audit and cleanup

### 3. Script Usage
- Test with small selections first
- Enable debug mode for new projects
- Keep backup before batch operations
- Monitor performance with large selections

## Support Resources

### Documentation
- **README.md**: Complete user guide
- **CHANGELOG.md**: Version history and known issues
- **This file**: Troubleshooting guide

### Related Files
- `logic-library/sources/Element Section Generator by EF/`: Analysis documentation
- `wall_classifier.py`: Classification logic details
- `wall_plan_generator.py`: View creation logic details

### Community Support
- Check pyRevit forums for similar issues
- Review Revit API documentation
- Consult BIM standards documentation

---

*For persistent issues not covered here, enable debug mode and include the full debug output when seeking support.*