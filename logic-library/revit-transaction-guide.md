# Revit API Transaction Management
## Complete Reference Guide for pyRevit Development

---

## Table of Contents
1. [Transaction Fundamentals](#transaction-fundamentals)
2. [Transaction Types](#transaction-types)
3. [Transaction Patterns](#transaction-patterns)
4. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
5. [Best Practices](#best-practices)
6. [Real-World Examples](#real-world-examples)

---

## Transaction Fundamentals

### What is a Transaction?

**Transaction** adalah mekanisme wajib di Revit API untuk memodifikasi dokumen. Semua perubahan pada model Revit HARUS dibungkus dalam transaction.

#### Core Principle
```
NO TRANSACTION = NO MODIFICATION
```

Revit menggunakan transaction untuk:
- **Database Integrity**: Menjaga konsistensi data
- **Undo/Redo**: Memungkinkan user membatalkan perubahan
- **Conflict Resolution**: Mengelola perubahan concurrent di workshared files

### Basic Transaction Anatomy

```python
from Autodesk.Revit.DB import Transaction

# Get document
doc = __revit__.ActiveUIDocument.Document

# Create transaction with descriptive name
t = Transaction(doc, "Transaction Name")

# Start transaction
t.Start()

try:
    # === MODIFICATION ZONE ===
    # All document modifications go here
    element.Parameter.Set(new_value)
    doc.Create.NewWall(...)
    doc.Delete(element_id)
    
    # Commit changes to database
    t.Commit()
    
except Exception as e:
    # If error occurs, rollback all changes
    if t.HasStarted():
        t.RollBack()
    print("Error: {}".format(e))
```

### Transaction Lifecycle States

```
[No Transaction] 
    ↓
    Start()
    ↓
[Transaction Active] ← Modifications allowed
    ↓
    Commit() or RollBack()
    ↓
[Transaction Complete] ← Back to read-only state
```

---

## Transaction Types

### 1. Transaction (Standard)

**Purpose**: Single atomic operation on document

**Characteristics**:
- Most common type
- Cannot be nested directly
- All-or-nothing: commit applies all changes or rollback discards all

**When to Use**:
- Single logical operation
- Simple modifications
- No need for grouping

**Example**:
```python
# Example: Rename multiple elements
from Autodesk.Revit.DB import Transaction, FilteredElementCollector, BuiltInCategory

doc = __revit__.ActiveUIDocument.Document

# Collect all walls
walls = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Walls)\
    .WhereElementIsNotElementType()\
    .ToElements()

# Single transaction for all renames
t = Transaction(doc, "Rename All Walls")
t.Start()

try:
    for i, wall in enumerate(walls):
        name_param = wall.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if name_param and not name_param.IsReadOnly:
            name_param.Set("Wall_{}".format(i+1))
    
    t.Commit()
    print("Renamed {} walls".format(len(walls)))
    
except Exception as e:
    t.RollBack()
    print("Error: {}".format(e))
```

**Key Points**:
- ✅ Use for bulk operations that should succeed or fail together
- ✅ Transaction name appears in Undo list
- ❌ Cannot call `Start()` twice on same transaction
- ❌ Cannot nest transactions directly

---

### 2. SubTransaction

**Purpose**: Nested transaction within a parent Transaction

**Characteristics**:
- MUST be inside an active Transaction
- Can be rolled back independently without affecting parent
- Useful for "try this, if fail, try another approach"
- Does NOT appear in Undo list

**When to Use**:
- Conditional modifications (try different approaches)
- Partial rollback scenarios
- Testing if operation succeeds before committing

**Example**:
```python
from Autodesk.Revit.DB import Transaction, SubTransaction

doc = __revit__.ActiveUIDocument.Document

# Parent transaction
t = Transaction(doc, "Create Family Instance with Fallback")
t.Start()

try:
    # Try placing at preferred location
    sub1 = SubTransaction(doc)
    sub1.Start()
    
    try:
        # Attempt to place instance at location A
        instance = doc.Create.NewFamilyInstance(
            pointA, family_symbol, host, level, StructuralType.NonStructural
        )
        sub1.Commit()  # Success!
        print("Placed at preferred location")
        
    except Exception as e1:
        # Failed at location A, rollback and try location B
        sub1.RollBack()
        print("Location A failed: {}".format(e1))
        
        # Try alternative location
        sub2 = SubTransaction(doc)
        sub2.Start()
        
        try:
            instance = doc.Create.NewFamilyInstance(
                pointB, family_symbol, host, level, StructuralType.NonStructural
            )
            sub2.Commit()
            print("Placed at fallback location")
            
        except Exception as e2:
            sub2.RollBack()
            print("Location B also failed: {}".format(e2))
            raise  # Re-raise to trigger parent rollback
    
    # Commit parent transaction
    t.Commit()
    
except Exception as e:
    t.RollBack()
    print("Operation failed: {}".format(e))
```

**Key Points**:
- ✅ MUST be inside active Transaction
- ✅ Can rollback without affecting parent
- ✅ Perfect for "try-catch" logic
- ❌ Cannot exist without parent Transaction
- ❌ Does not appear in Undo list

**Common Pattern - Try Multiple Approaches**:
```python
t = Transaction(doc, "Smart Element Creation")
t.Start()

approaches = [
    ("Method A", lambda: create_using_method_a()),
    ("Method B", lambda: create_using_method_b()),
    ("Method C", lambda: create_using_method_c())
]

success = False
for method_name, method_func in approaches:
    sub = SubTransaction(doc)
    sub.Start()
    
    try:
        method_func()
        sub.Commit()
        print("Success using {}".format(method_name))
        success = True
        break
    except:
        sub.RollBack()
        print("{} failed, trying next...".format(method_name))

if success:
    t.Commit()
else:
    t.RollBack()
    print("All methods failed")
```

---

### 3. TransactionGroup

**Purpose**: Group multiple Transactions into single undoable operation

**Characteristics**:
- Groups multiple Transaction objects
- Appears as ONE item in Undo list
- All transactions must succeed, or entire group rolls back
- Can contain multiple Transactions but NOT SubTransactions directly

**When to Use**:
- Multi-step operations that should be undone as one
- Complex workflows with multiple logical stages
- When you need separate transactions but want single Undo

**Example**:
```python
from Autodesk.Revit.DB import Transaction, TransactionGroup

doc = __revit__.ActiveUIDocument.Document

# Create transaction group
tg = TransactionGroup(doc, "Complete Room Setup")
tg.Start()

try:
    # TRANSACTION 1: Create rooms
    t1 = Transaction(doc, "Create Rooms")
    t1.Start()
    room1 = doc.Create.NewRoom(level, UV(0, 0))
    room2 = doc.Create.NewRoom(level, UV(10, 10))
    t1.Commit()
    print("Rooms created")
    
    # TRANSACTION 2: Set room properties
    t2 = Transaction(doc, "Set Room Properties")
    t2.Start()
    room1.get_Parameter(BuiltInParameter.ROOM_NAME).Set("Living Room")
    room2.get_Parameter(BuiltInParameter.ROOM_NAME).Set("Bedroom")
    t2.Commit()
    print("Room properties set")
    
    # TRANSACTION 3: Create room tags
    t3 = Transaction(doc, "Create Room Tags")
    t3.Start()
    doc.Create.NewRoomTag(LinkElementId(room1.Id), UV(0, 0), view.Id)
    doc.Create.NewRoomTag(LinkElementId(room2.Id), UV(10, 10), view.Id)
    t3.Commit()
    print("Room tags created")
    
    # Assimilate all transactions into single Undo item
    tg.Assimilate()
    print("Operation complete - appears as ONE undo item")
    
except Exception as e:
    # If any transaction fails, rollback entire group
    tg.RollBack()
    print("Error: {}".format(e))
```

**Key Points**:
- ✅ Multiple Transactions appear as ONE in Undo list
- ✅ Use `Assimilate()` to finalize (not `Commit()`)
- ✅ Great for complex multi-stage operations
- ❌ Cannot nest TransactionGroups
- ❌ All child Transactions must succeed

**TransactionGroup vs Multiple Transactions**:
```python
# WITHOUT TransactionGroup (3 separate Undo items)
t1 = Transaction(doc, "Step 1")
t1.Start()
# ... modifications ...
t1.Commit()

t2 = Transaction(doc, "Step 2")
t2.Start()
# ... modifications ...
t2.Commit()

t3 = Transaction(doc, "Step 3")
t3.Start()
# ... modifications ...
t3.Commit()

# User sees: "Undo Step 3", "Undo Step 2", "Undo Step 1"

# WITH TransactionGroup (1 single Undo item)
tg = TransactionGroup(doc, "Complete Operation")
tg.Start()

t1 = Transaction(doc, "Step 1")
t1.Start()
# ... modifications ...
t1.Commit()

t2 = Transaction(doc, "Step 2")
t2.Start()
# ... modifications ...
t2.Commit()

t3 = Transaction(doc, "Step 3")
t3.Start()
# ... modifications ...
t3.Commit()

tg.Assimilate()

# User sees: "Undo Complete Operation" (undoes all 3 steps at once)
```

---

## Transaction Patterns

### Pattern 1: Simple Transaction (Most Common)

```python
from Autodesk.Revit.DB import Transaction

def simple_modification(doc, elements):
    """Standard pattern for single logical operation."""
    t = Transaction(doc, "Modify Elements")
    t.Start()
    
    try:
        for elem in elements:
            # Modify element
            elem.Parameter.Set(new_value)
        
        t.Commit()
        return True
        
    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        print("Error: {}".format(e))
        return False
```

**Use Cases**:
- Bulk property updates
- Element creation/deletion
- Simple parameter modifications

---

### Pattern 2: Transaction with SubTransaction (Try-Catch Logic)

```python
from Autodesk.Revit.DB import Transaction, SubTransaction

def smart_element_placement(doc, locations):
    """Pattern for conditional operations with fallback."""
    t = Transaction(doc, "Place Elements")
    t.Start()
    
    placed_count = 0
    failed_count = 0
    
    try:
        for location in locations:
            sub = SubTransaction(doc)
            sub.Start()
            
            try:
                # Try to place element
                element = place_element_at(location)
                sub.Commit()
                placed_count += 1
                
            except Exception as e:
                # Failed, rollback this subtransaction only
                sub.RollBack()
                failed_count += 1
                print("Failed at location {}: {}".format(location, e))
        
        # Commit parent transaction
        t.Commit()
        print("Placed: {}, Failed: {}".format(placed_count, failed_count))
        return placed_count
        
    except Exception as e:
        t.RollBack()
        print("Critical error: {}".format(e))
        return 0
```

**Use Cases**:
- Element placement with validation
- Operations that may fail for some items
- Try different approaches sequentially

---

### Pattern 3: TransactionGroup (Multi-Stage Operations)

```python
from Autodesk.Revit.DB import Transaction, TransactionGroup

def complex_workflow(doc):
    """Pattern for grouping multiple logical steps."""
    tg = TransactionGroup(doc, "Complete Workflow")
    tg.Start()
    
    try:
        # STAGE 1: Preparation
        t1 = Transaction(doc, "Stage 1: Prepare")
        t1.Start()
        prepared_data = prepare_elements(doc)
        t1.Commit()
        
        # STAGE 2: Main operation
        t2 = Transaction(doc, "Stage 2: Process")
        t2.Start()
        processed_results = process_elements(prepared_data)
        t2.Commit()
        
        # STAGE 3: Finalization
        t3 = Transaction(doc, "Stage 3: Finalize")
        t3.Start()
        finalize_results(processed_results)
        t3.Commit()
        
        # Assimilate into single undo operation
        tg.Assimilate()
        return True
        
    except Exception as e:
        tg.RollBack()
        print("Workflow failed: {}".format(e))
        return False
```

**Use Cases**:
- Multi-step wizards
- Data import workflows
- Complex element creation sequences

---

### Pattern 4: pyRevit Context Manager (Recommended)

```python
from pyrevit import revit, DB

doc = revit.doc

# pyRevit provides convenient 'with' statement syntax
with revit.Transaction("Modify Elements"):
    for element in elements:
        element.Parameter.Set(new_value)
    # Auto-commits on success, auto-rollbacks on exception

# Equivalent to manual transaction:
# t = DB.Transaction(doc, "Modify Elements")
# t.Start()
# try:
#     ...
#     t.Commit()
# except:
#     t.RollBack()
```

**pyRevit Context Manager Benefits**:
- ✅ Cleaner syntax
- ✅ Automatic commit/rollback
- ✅ Less boilerplate code
- ✅ Pythonic

**pyRevit TransactionGroup**:
```python
from pyrevit import revit

with revit.TransactionGroup("Complete Operation"):
    with revit.Transaction("Step 1"):
        # modifications
        pass
    
    with revit.Transaction("Step 2"):
        # more modifications
        pass
    
    # Auto-assimilates
```

---

## Common Pitfalls & Solutions

### ❌ PITFALL 1: Nested Transactions

**Problem**:
```python
t1 = Transaction(doc, "Outer")
t1.Start()

t2 = Transaction(doc, "Inner")  # ❌ ERROR!
t2.Start()  # Cannot nest Transactions directly
```

**Error**: `InvalidOperationException: Starting a transaction is not permitted when there is any open transaction`

**Solution**: Use SubTransaction
```python
t1 = Transaction(doc, "Outer")
t1.Start()

sub = SubTransaction(doc)  # ✅ CORRECT
sub.Start()
sub.Commit()

t1.Commit()
```

---

### ❌ PITFALL 2: Modifying Document Outside Transaction

**Problem**:
```python
element = doc.GetElement(element_id)
element.Parameter.Set(new_value)  # ❌ ERROR! No active transaction
```

**Error**: `InvalidOperationException: Modification of the document is forbidden`

**Solution**: Wrap in Transaction
```python
t = Transaction(doc, "Modify Element")
t.Start()
element.Parameter.Set(new_value)  # ✅ CORRECT
t.Commit()
```

---

### ❌ PITFALL 3: Forgetting to Check HasStarted()

**Problem**:
```python
t = Transaction(doc, "My Transaction")
t.Start()

try:
    # Some operation that might fail before modifications
    if not validate_data():
        raise Exception("Invalid data")
    
    # Modify document
    element.Parameter.Set(value)
    t.Commit()
    
except Exception as e:
    t.RollBack()  # ❌ Might fail if transaction never started
```

**Error**: `InvalidOperationException: Transaction has not been started`

**Solution**: Always check HasStarted()
```python
try:
    element.Parameter.Set(value)
    t.Commit()
    
except Exception as e:
    if t.HasStarted():  # ✅ CORRECT
        t.RollBack()
```

---

### ❌ PITFALL 4: Operations That Don't Need Transactions

**Problem**:
```python
# Reading operations don't need transactions
t = Transaction(doc, "Get Elements")  # ❌ Unnecessary!
t.Start()

elements = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Walls)\
    .ToElements()

param_value = elements[0].get_Parameter(param_id).AsDouble()

t.Commit()
```

**Solution**: Only use transactions for modifications
```python
# ✅ CORRECT - No transaction needed for reading
elements = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Walls)\
    .ToElements()

param_value = elements[0].get_Parameter(param_id).AsDouble()

# Only start transaction when modifying
t = Transaction(doc, "Modify Elements")
t.Start()
elements[0].get_Parameter(param_id).Set(new_value)
t.Commit()
```

**Operations that DON'T need transactions**:
- ✅ `FilteredElementCollector` - reading elements
- ✅ `get_Parameter()` - reading parameter values
- ✅ `GetElement()` - retrieving elements
- ✅ Geometry extraction - `get_Geometry()`
- ✅ Any read-only operation

**Operations that NEED transactions**:
- ❌ `Set()` - setting parameter values
- ❌ `Create.*` - creating elements
- ❌ `Delete()` - deleting elements
- ❌ `Move()`, `Rotate()` - transforming elements
- ❌ Any modification operation

---

### ❌ PITFALL 5: SaveAs/Save Inside Transaction

**Problem**:
```python
t = Transaction(doc, "Modify and Save")
t.Start()

element.Parameter.Set(value)
doc.Save()  # ❌ ERROR!

t.Commit()
```

**Error**: `InvalidOperationException: Cannot save when transaction is open`

**Solution**: Save AFTER committing
```python
t = Transaction(doc, "Modify Elements")
t.Start()
element.Parameter.Set(value)
t.Commit()

doc.Save()  # ✅ CORRECT - Save after transaction
```

---

### ❌ PITFALL 6: Regenerate Without Transaction

**Problem**:
```python
t = Transaction(doc, "Modify Elements")
t.Start()
element.Parameter.Set(value)
t.Commit()

doc.Regenerate()  # ❌ ERROR! Regenerate needs transaction
```

**Error**: `InvalidOperationException: Modification of the document is forbidden`

**Solution**: Regenerate inside transaction
```python
t = Transaction(doc, "Modify and Regenerate")
t.Start()
element.Parameter.Set(value)
doc.Regenerate()  # ✅ CORRECT
t.Commit()
```

**Or better**: Let Revit auto-regenerate after commit
```python
t = Transaction(doc, "Modify Elements")
t.Start()
element.Parameter.Set(value)
t.Commit()
# Revit auto-regenerates when needed ✅
```

---

## Best Practices

### ✅ DO: Use Descriptive Transaction Names

```python
# ❌ BAD
t = Transaction(doc, "Transaction")
t = Transaction(doc, "Update")

# ✅ GOOD
t = Transaction(doc, "Update Wall Type Parameters")
t = Transaction(doc, "Create Room Tags for Level 1")
t = Transaction(doc, "Rename Structural Framing Elements")
```

**Why**: Transaction names appear in Undo list - help users understand what can be undone.

---

### ✅ DO: Keep Transactions Focused

```python
# ❌ BAD - Too many unrelated operations
t = Transaction(doc, "Do Everything")
t.Start()
create_walls()
delete_old_elements()
update_parameters()
place_tags()
generate_schedules()
t.Commit()

# ✅ GOOD - Separate logical operations
with revit.TransactionGroup("Complete Setup"):
    with revit.Transaction("Create Walls"):
        create_walls()
    
    with revit.Transaction("Delete Old Elements"):
        delete_old_elements()
    
    with revit.Transaction("Update Parameters"):
        update_parameters()
```

**Why**: Easier to debug, better undo granularity (with TransactionGroup).

---

### ✅ DO: Use pyRevit Context Managers When Possible

```python
# ❌ VERBOSE - Manual transaction management
t = DB.Transaction(doc, "Modify Elements")
t.Start()
try:
    element.Parameter.Set(value)
    t.Commit()
except Exception as e:
    if t.HasStarted():
        t.RollBack()
    raise

# ✅ CLEAN - pyRevit context manager
with revit.Transaction("Modify Elements"):
    element.Parameter.Set(value)
```

---

### ✅ DO: Validate Before Starting Transaction

```python
# ✅ GOOD - Validate before transaction
elements = get_elements_to_modify()

if not elements:
    print("No elements to modify")
    return

if not validate_elements(elements):
    print("Invalid elements")
    return

# Only start transaction if validation passes
t = Transaction(doc, "Modify Elements")
t.Start()
for elem in elements:
    elem.Parameter.Set(value)
t.Commit()
```

**Why**: Avoid unnecessary transactions, better performance.

---

### ✅ DO: Use SubTransaction for Recoverable Errors

```python
# ✅ GOOD - Continue processing even if some items fail
t = Transaction(doc, "Batch Process Elements")
t.Start()

success_count = 0
fail_count = 0

for element in elements:
    sub = SubTransaction(doc)
    sub.Start()
    
    try:
        process_element(element)
        sub.Commit()
        success_count += 1
    except Exception as e:
        sub.RollBack()
        fail_count += 1
        logger.warning("Failed on {}: {}".format(element.Id, e))

t.Commit()
print("Success: {}, Failed: {}".format(success_count, fail_count))
```

---

### ✅ DO: Minimize Transaction Scope

```python
# ❌ BAD - Transaction includes unnecessary operations
t = Transaction(doc, "Process Elements")
t.Start()

elements = FilteredElementCollector(doc).ToElements()  # Reading - doesn't need transaction
analysis_data = analyze_elements(elements)  # Calculation - doesn't need transaction
filtered = filter_elements(analysis_data)  # Filtering - doesn't need transaction

for elem in filtered:
    elem.Parameter.Set(value)  # Only THIS needs transaction

t.Commit()

# ✅ GOOD - Transaction only wraps modifications
elements = FilteredElementCollector(doc).ToElements()
analysis_data = analyze_elements(elements)
filtered = filter_elements(analysis_data)

t = Transaction(doc, "Update Parameters")
t.Start()
for elem in filtered:
    elem.Parameter.Set(value)
t.Commit()
```

**Why**: Better performance, shorter lock time on document.

---

## Real-World Examples

### Example 1: Batch Element Creation with Error Recovery

```python
from pyrevit import revit, DB
from System.Collections.Generic import List

def create_multiple_elements_safe(doc, creation_data):
    """
    Create multiple elements with error recovery.
    Returns: (success_count, fail_count, created_ids)
    """
    success_count = 0
    fail_count = 0
    created_ids = List[DB.ElementId]()
    
    t = DB.Transaction(doc, "Batch Create Elements")
    t.Start()
    
    try:
        for i, data in enumerate(creation_data):
            # Use SubTransaction for each element
            sub = DB.SubTransaction(doc)
            sub.Start()
            
            try:
                # Attempt to create element
                new_element = create_element_from_data(doc, data)
                created_ids.Add(new_element.Id)
                sub.Commit()
                success_count += 1
                
            except Exception as e:
                # If creation fails, rollback this subtransaction only
                sub.RollBack()
                fail_count += 1
                print("Failed to create element {}: {}".format(i, e))
        
        # Commit parent transaction
        t.Commit()
        print("Created {} elements, {} failed".format(success_count, fail_count))
        
        return success_count, fail_count, created_ids
        
    except Exception as e:
        # Critical error - rollback everything
        if t.HasStarted():
            t.RollBack()
        print("Critical error: {}".format(e))
        return 0, len(creation_data), List[DB.ElementId]()


# Usage
doc = revit.doc
creation_data = [
    {"type": "wall", "location": point1},
    {"type": "wall", "location": point2},
    # ... more data
]

success, failed, ids = create_multiple_elements_safe(doc, creation_data)
```

---

### Example 2: Multi-Stage Data Import Workflow

```python
from pyrevit import revit, DB

def import_data_from_excel(doc, excel_file):
    """
    Import data from Excel in multiple stages.
    Each stage is separate transaction grouped as one Undo.
    """
    tg = DB.TransactionGroup(doc, "Import Excel Data")
    tg.Start()
    
    try:
        # STAGE 1: Parse Excel file (no transaction needed)
        print("Stage 1: Reading Excel...")
        raw_data = read_excel_file(excel_file)
        
        # STAGE 2: Create or find elements
        print("Stage 2: Creating/Finding elements...")
        t1 = DB.Transaction(doc, "Stage 2: Find Elements")
        t1.Start()
        
        element_mapping = {}
        for row in raw_data:
            element_id = find_or_create_element(doc, row)
            element_mapping[row['id']] = element_id
        
        t1.Commit()
        print("Processed {} elements".format(len(element_mapping)))
        
        # STAGE 3: Update parameters
        print("Stage 3: Updating parameters...")
        t2 = DB.Transaction(doc, "Stage 3: Update Parameters")
        t2.Start()
        
        update_count = 0
        for row in raw_data:
            element_id = element_mapping.get(row['id'])
            if element_id:
                element = doc.GetElement(element_id)
                update_element_parameters(element, row)
                update_count += 1
        
        t2.Commit()
        print("Updated {} elements".format(update_count))
        
        # STAGE 4: Create relationships
        print("Stage 4: Creating relationships...")
        t3 = DB.Transaction(doc, "Stage 4: Create Relationships")
        t3.Start()
        
        relation_count = 0
        for row in raw_data:
            if 'related_to' in row:
                create_relationship(doc, element_mapping, row)
                relation_count += 1
        
        t3.Commit()
        print("Created {} relationships".format(relation_count))
        
        # Assimilate all stages into single Undo
        tg.Assimilate()
        print("Import complete - all stages grouped as one Undo")
        
        return True
        
    except Exception as e:
        # If any stage fails, rollback everything
        tg.RollBack()
        print("Import failed: {}".format(e))
        return False


# Usage
doc = revit.doc
success = import_data_from_excel(doc, "C:/data/import.xlsx")
```

---

### Example 3: Conditional Element Modification

```python
from pyrevit import revit, DB

def modify_elements_conditionally(doc, elements, conditions):
    """
    Apply different modifications based on element properties.
    Uses SubTransaction to test conditions before applying changes.
    """
    t = DB.Transaction(doc, "Conditional Modifications")
    t.Start()
    
    results = {
        'modified': [],
        'skipped': [],
        'failed': []
    }
    
    try:
        for element in elements:
            # Test each condition using SubTransaction
            for condition_name, condition_func, modify_func in conditions:
                sub = DB.SubTransaction(doc)
                sub.Start()
                
                try:
                    # Test if condition applies
                    if condition_func(element):
                        # Apply modification
                        modify_func(element)
                        sub.Commit()
                        results['modified'].append(element.Id)
                        print("Applied '{}' to element {}".format(
                            condition_name, element.Id))
                        break  # Stop testing other conditions
                    else:
                        # Condition doesn't apply, rollback
                        sub.RollBack()
                
                except Exception as e:
                    # Modification failed, rollback and try next
                    sub.RollBack()
                    print("Failed to apply '{}' to {}: {}".format(
                        condition_name, element.Id, e))
            
            else:
                # No condition matched
                results['skipped'].append(element.Id)
        
        # Commit all successful modifications
        t.Commit()
        
        print("\nResults:")
        print("  Modified: {}".format(len(results['modified'])))
        print("  Skipped: {}".format(len(results['skipped'])))
        print("  Failed: {}".format(len(results['failed'])))
        
        return results
        
    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        print("Critical error: {}".format(e))
        return None


# Usage
doc = revit.doc
walls = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Walls)\
    .WhereElementIsNotElementType()\
    .ToElements()

# Define conditions and modifications
conditions = [
    (
        "Exterior Wall",
        lambda e: is_exterior_wall(e),
        lambda e: set_wall_type_exterior(e)
    ),
    (
        "Interior Load-Bearing",
        lambda e: is_load_bearing(e),
        lambda e: set_wall_type_load_bearing(e)
    ),
    (
        "Interior Non-Load-Bearing",
        lambda e: not is_load_bearing(e),
        lambda e: set_wall_type_partition(e)
    )
]

results = modify_elements_conditionally(doc, walls, conditions)
```

---

### Example 4: Performance-Optimized Bulk Updates

```python
from pyrevit import revit, DB, forms
from System.Collections.Generic import List

def bulk_update_parameters_optimized(doc, elements, param_updates):
    """
    Optimized bulk parameter updates with progress tracking.
    Groups updates into single transaction for best performance.
    """
    total = len(elements)
    
    with forms.ProgressBar(title="Updating Parameters ({value} of {max_value})") as pb:
        # Single transaction for all updates (fastest)
        t = DB.Transaction(doc, "Bulk Parameter Update")
        t.Start()
        
        try:
            update_count = 0
            skip_count = 0
            
            for i, element in enumerate(elements):
                # Update progress
                pb.update_progress(i + 1, total)
                
                # Apply all parameter updates to this element
                element_updated = False
                
                for param_name, new_value in param_updates.items():
                    try:
                        # Try built-in parameter first
                        param = element.LookupParameter(param_name)
                        
                        if param and not param.IsReadOnly:
                            # Set value based on storage type
                            if param.StorageType == DB.StorageType.String:
                                param.Set(str(new_value))
                            elif param.StorageType == DB.StorageType.Double:
                                param.Set(float(new_value))
                            elif param.StorageType == DB.StorageType.Integer:
                                param.Set(int(new_value))
                            
                            element_updated = True
                    
                    except Exception as e:
                        # Skip this parameter, continue with others
                        continue
                
                if element_updated:
                    update_count += 1
                else:
                    skip_count += 1
            
            # Commit all changes at once
            t.Commit()
            
            print("\nUpdate Complete:")
            print("  Updated: {} elements".format(update_count))
            print("  Skipped: {} elements".format(skip_count))
            
            return update_count
            
        except Exception as e:
            if t.HasStarted():
                t.RollBack()
            print("Bulk update failed: {}".format(e))
            return 0


# Usage
doc = revit.doc
beams = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_StructuralFraming)\
    .WhereElementIsNotElementType()\
    .ToElements()

param_updates = {
    "Comments": "Updated by script",
    "Mark": "B-",
    "Custom_Parameter": "New Value"
}

updated = bulk_update_parameters_optimized(doc, beams, param_updates)
```

---

### Example 5: Transaction with Cleanup (Context Manager Pattern)

```python
from pyrevit import revit, DB
from System.Collections.Generic import List

class TransactionWithCleanup:
    """
    Custom context manager for transactions with automatic cleanup.
    Useful for operations that create temporary elements.
    """
    
    def __init__(self, doc, name):
        self.doc = doc
        self.name = name
        self.transaction = DB.Transaction(doc, name)
        self.temp_elements = List[DB.ElementId]()
    
    def __enter__(self):
        self.transaction.Start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Success - commit transaction
                self.transaction.Commit()
            else:
                # Exception occurred - rollback
                if self.transaction.HasStarted():
                    self.transaction.RollBack()
        finally:
            # Always cleanup temporary elements
            self.cleanup_temp_elements()
    
    def add_temp_element(self, element_id):
        """Mark element as temporary for cleanup."""
        self.temp_elements.Add(element_id)
    
    def cleanup_temp_elements(self):
        """Delete temporary elements if they still exist."""
        if self.temp_elements.Count > 0:
            cleanup_t = DB.Transaction(self.doc, "Cleanup Temp Elements")
            cleanup_t.Start()
            try:
                for elem_id in self.temp_elements:
                    try:
                        self.doc.Delete(elem_id)
                    except:
                        pass  # Element might already be deleted
                cleanup_t.Commit()
            except:
                cleanup_t.RollBack()


# Usage
doc = revit.doc

with TransactionWithCleanup(doc, "Process with Temp Elements") as txn:
    # Create temporary construction plane
    temp_plane = create_temporary_plane(doc)
    txn.add_temp_element(temp_plane.Id)
    
    # Create temporary reference line
    temp_line = create_temporary_line(doc)
    txn.add_temp_element(temp_line.Id)
    
    # Do main work using temp elements
    final_element = create_final_element_using_temps(doc, temp_plane, temp_line)
    
    # Temp elements will be auto-cleaned up when exiting context

print("Process complete, temp elements cleaned up")
```

---

## Advanced Patterns

### Pattern 5: Transaction Batching for Performance

```python
from pyrevit import revit, DB

def batch_process_with_checkpoints(doc, items, batch_size=100):
    """
    Process large datasets in batches with checkpoint saves.
    Useful for very large operations that might timeout.
    """
    import math
    
    total_batches = int(math.ceil(len(items) / float(batch_size)))
    processed_count = 0
    
    print("Processing {} items in {} batches...".format(len(items), total_batches))
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(items))
        batch = items[start_idx:end_idx]
        
        print("\nBatch {}/{}...".format(batch_num + 1, total_batches))
        
        # Process batch in single transaction
        t = DB.Transaction(doc, "Batch {} of {}".format(batch_num + 1, total_batches))
        t.Start()
        
        try:
            for item in batch:
                process_item(doc, item)
                processed_count += 1
            
            t.Commit()
            print("  Processed {} items".format(len(batch)))
            
        except Exception as e:
            if t.HasStarted():
                t.RollBack()
            print("  Batch failed: {}".format(e))
            break
    
    print("\nTotal processed: {} items".format(processed_count))
    return processed_count


# Usage
doc = revit.doc
all_elements = get_large_element_collection(doc)  # e.g., 10,000 elements

processed = batch_process_with_checkpoints(doc, all_elements, batch_size=500)
```

---

### Pattern 6: Transactional State Machine

```python
from pyrevit import revit, DB

class ElementProcessor:
    """
    State machine for complex element processing with rollback capability.
    """
    
    def __init__(self, doc):
        self.doc = doc
        self.state_stack = []
    
    def save_state(self, state_name, element_ids):
        """Save current state for potential rollback."""
        self.state_stack.append({
            'name': state_name,
            'element_ids': element_ids,
            'timestamp': datetime.now()
        })
    
    def process_with_states(self, elements):
        """Process elements through multiple states."""
        tg = DB.TransactionGroup(self.doc, "Multi-State Processing")
        tg.Start()
        
        try:
            # STATE 1: Validation
            t1 = DB.Transaction(self.doc, "State 1: Validate")
            t1.Start()
            
            valid_elements = []
            for elem in elements:
                if self.validate_element(elem):
                    valid_elements.append(elem)
                    elem.LookupParameter("Status").Set("Validated")
            
            t1.Commit()
            self.save_state("Validation", [e.Id for e in valid_elements])
            print("State 1: {} elements validated".format(len(valid_elements)))
            
            # STATE 2: Transformation
            t2 = DB.Transaction(self.doc, "State 2: Transform")
            t2.Start()
            
            transformed_elements = []
            for elem in valid_elements:
                try:
                    self.transform_element(elem)
                    transformed_elements.append(elem)
                    elem.LookupParameter("Status").Set("Transformed")
                except Exception as e:
                    print("  Skipped {}: {}".format(elem.Id, e))
            
            t2.Commit()
            self.save_state("Transformation", [e.Id for e in transformed_elements])
            print("State 2: {} elements transformed".format(len(transformed_elements)))
            
            # STATE 3: Finalization
            t3 = DB.Transaction(self.doc, "State 3: Finalize")
            t3.Start()
            
            finalized_count = 0
            for elem in transformed_elements:
                self.finalize_element(elem)
                elem.LookupParameter("Status").Set("Complete")
                finalized_count += 1
            
            t3.Commit()
            self.save_state("Finalization", [e.Id for e in transformed_elements])
            print("State 3: {} elements finalized".format(finalized_count))
            
            # Success - assimilate all states
            tg.Assimilate()
            return finalized_count
            
        except Exception as e:
            # Rollback to last known good state
            tg.RollBack()
            print("Processing failed at state {}: {}".format(
                self.state_stack[-1]['name'] if self.state_stack else 'Unknown', 
                e
            ))
            return 0
    
    def validate_element(self, element):
        """Validation logic."""
        return element is not None
    
    def transform_element(self, element):
        """Transformation logic."""
        pass
    
    def finalize_element(self, element):
        """Finalization logic."""
        pass


# Usage
doc = revit.doc
processor = ElementProcessor(doc)
elements = get_elements_to_process(doc)
completed = processor.process_with_states(elements)
```

---

## Transaction Decision Tree

```
Need to modify document?
│
├─ YES
│  │
│  ├─ Single logical operation?
│  │  │
│  │  ├─ YES → Use Transaction
│  │  │         t = Transaction(doc, "Name")
│  │  │         t.Start()
│  │  │         # modify
│  │  │         t.Commit()
│  │  │
│  │  └─ NO → Multiple logical stages?
│  │           │
│  │           ├─ Want grouped as one Undo?
│  │           │  │
│  │           │  └─ YES → Use TransactionGroup
│  │           │           tg = TransactionGroup(doc, "Name")
│  │           │           tg.Start()
│  │           │           # multiple transactions
│  │           │           tg.Assimilate()
│  │           │
│  │           └─ Want separate Undo items?
│  │                    → Use multiple Transactions
│  │
│  └─ Need conditional rollback?
│     │
│     └─ YES → Use SubTransaction (inside Transaction)
│              t = Transaction(doc, "Parent")
│              t.Start()
│              sub = SubTransaction(doc)
│              sub.Start()
│              try:
│                  # modify
│                  sub.Commit()
│              except:
│                  sub.RollBack()
│              t.Commit()
│
└─ NO (Read-only)
   │
   └─ No transaction needed
      elements = FilteredElementCollector(doc).ToElements()
```

---

## Quick Reference Table

| Operation Type | Transaction Needed? | Notes |
|---------------|--------------------:|-------|
| `FilteredElementCollector` | ❌ No | Read-only |
| `get_Parameter()` | ❌ No | Read-only |
| `AsDouble()`, `AsString()` | ❌ No | Read-only |
| `GetElement()` | ❌ No | Read-only |
| `get_Geometry()` | ❌ No | Read-only |
| `Set()` parameter value | ✅ Yes | Modification |
| `doc.Create.*` | ✅ Yes | Creation |
| `doc.Delete()` | ✅ Yes | Deletion |
| `Move()`, `Rotate()` | ✅ Yes | Transformation |
| `doc.Regenerate()` | ✅ Yes | Document update |
| `doc.Save()` | ❌ No | Must be OUTSIDE transaction |
| `doc.SaveAs()` | ❌ No | Must be OUTSIDE transaction |

---

## Transaction vs SubTransaction vs TransactionGroup

| Feature | Transaction | SubTransaction | TransactionGroup |
|---------|------------|----------------|------------------|
| **Can be nested?** | ❌ No | ✅ Yes (inside Transaction) | ❌ No |
| **Appears in Undo?** | ✅ Yes | ❌ No | ✅ Yes (as one item) |
| **Can rollback independently?** | ✅ Yes | ✅ Yes | ✅ Yes (rolls back all) |
| **Use for...** | Single operation | Try-catch logic | Multi-stage workflow |
| **Finalize with...** | `Commit()` | `Commit()` | `Assimilate()` |

---

## Common Error Messages & Solutions

### Error: "Starting a transaction is not permitted"

**Cause**: Trying to start nested Transaction

**Solution**: Use SubTransaction instead
```python
# ❌ BAD
t1 = Transaction(doc, "Outer")
t1.Start()
t2 = Transaction(doc, "Inner")  # ERROR!
t2.Start()

# ✅ GOOD
t1 = Transaction(doc, "Outer")
t1.Start()
sub = SubTransaction(doc)  # OK
sub.Start()
```

---

### Error: "Modification of the document is forbidden"

**Cause**: Trying to modify without active transaction

**Solution**: Wrap modification in Transaction
```python
# ❌ BAD
element.Parameter.Set(value)  # ERROR!

# ✅ GOOD
t = Transaction(doc, "Modify")
t.Start()
element.Parameter.Set(value)
t.Commit()
```

---

### Error: "Cannot save when there is an open transaction"

**Cause**: Trying to Save/SaveAs inside transaction

**Solution**: Save AFTER committing
```python
# ❌ BAD
t = Transaction(doc, "Modify")
t.Start()
element.Parameter.Set(value)
doc.Save()  # ERROR!
t.Commit()

# ✅ GOOD
t = Transaction(doc, "Modify")
t.Start()
element.Parameter.Set(value)
t.Commit()
doc.Save()  # OK
```

---

### Error: "Transaction has not been started"

**Cause**: Calling RollBack() on transaction that never started

**Solution**: Check `HasStarted()` first
```python
# ❌ BAD
try:
    t.Start()
    # operation that might fail before Start()
    element.Parameter.Set(value)
    t.Commit()
except:
    t.RollBack()  # ERROR if Start() never executed!

# ✅ GOOD
try:
    t.Start()
    element.Parameter.Set(value)
    t.Commit()
except:
    if t.HasStarted():  # Check first!
        t.RollBack()
```

---

## Performance Tips

### 1. Minimize Transaction Count

```python
# ❌ SLOW - 1000 transactions
for element in elements:  # 1000 elements
    t = Transaction(doc, "Update")
    t.Start()
    element.Parameter.Set(value)
    t.Commit()

# ✅ FAST - 1 transaction
t = Transaction(doc, "Batch Update")
t.Start()
for element in elements:  # 1000 elements
    element.Parameter.Set(value)
t.Commit()
```

**Result**: ~100x faster for bulk operations

---

### 2. Don't Include Read Operations in Transaction

```python
# ❌ SLOW - unnecessary transaction
t = Transaction(doc, "Process")
t.Start()
elements = FilteredElementCollector(doc).ToElements()  # Reading - no transaction needed!
for elem in elements:
    elem.Parameter.Set(value)
t.Commit()

# ✅ FAST - read outside transaction
elements = FilteredElementCollector(doc).ToElements()
t = Transaction(doc, "Update")
t.Start()
for elem in elements:
    elem.Parameter.Set(value)
t.Commit()
```

---

### 3. Avoid Regenerate Unless Necessary

```python
# ❌ SLOW - unnecessary regenerate
t = Transaction(doc, "Update")
t.Start()
for element in elements:
    element.Parameter.Set(value)
    doc.Regenerate()  # SLOW! Regenerates after EVERY element
t.Commit()

# ✅ FAST - let Revit auto-regenerate
t = Transaction(doc, "Update")
t.Start()
for element in elements:
    element.Parameter.Set(value)
t.Commit()  # Revit regenerates once after commit
```

---

## Summary Checklist

### ✅ Transaction Best Practices Checklist

- [ ] Use descriptive transaction names
- [ ] Keep transactions focused and minimal
- [ ] Validate data BEFORE starting transaction
- [ ] Always check `HasStarted()` before `RollBack()`
- [ ] Use `SubTransaction` for conditional operations
- [ ] Use `TransactionGroup` to group related operations
- [ ] Don't include read operations in transactions
- [ ] Save document OUTSIDE transactions
- [ ] Use pyRevit context managers when possible
- [ ] Batch modifications into single transaction for performance
- [ ] Handle exceptions properly (try-except-finally)
- [ ] Clean up resources in finally blocks
- [ ] Log transaction operations for debugging
- [ ] Test rollback scenarios
- [ ] Document complex transaction flows

---

## Additional Resources

### Official Documentation
- [Revit API Developers Guide - Transactions](https://www.revitapidocs.com/)
- [Autodesk Revit API: Transaction Class](https://www.revitapidocs.com/2024/db_transaction.html)

### pyRevit Documentation
- [pyRevit Transaction Helpers](https://pyrevitlabs.notion.site/Transactions-b2f7)