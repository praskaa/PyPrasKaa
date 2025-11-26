# Reusable Components from EF Element Sections Generator

## 🎯 Overview
Analisis komponen-komponen dari script EF yang bisa diadopsi untuk Wall Plan Generator, dengan fokus pada reusability dan adaptation.

## 🔧 Core Reusable Components

### **1. Selection Filter System**

#### **EF_SelectionFilter Class**
```python
class EF_SelectionFilter(ISelectionFilter):
    def __init__(self, list_types_or_cats):
        """ ISelectionFilter made to filter with types
        :param allowed_types: list of allowed Types"""

        # Convert BuiltInCategories to ElementIds, Keep Types the Same.
        self.list_types_or_cats = [ElementId(i) if type(i) == BuiltInCategory else i for i in list_types_or_cats]

    def AllowElement(self, element):
        if element.ViewSpecific:
            return False

        #🅰️ Check if Element's Type in Allowed List
        if type(element) in self.list_types_or_cats:
            return True

        #🅱️ Check if Element's Category in Allowed List
        elif element.Category.Id in self.list_types_or_cats:
            return True
```

**Adaptation for Wall Plan Generator:**
```python
# Direct adoption with wall-specific categories
wall_categories = [BuiltInCategory.OST_Walls]
selection_filter = EF_SelectionFilter(wall_categories)
```

**Benefits:**
- ✅ **Proven filtering logic** untuk BuiltInCategory dan Type
- ✅ **View-specific exclusion** (important untuk wall selection)
- ✅ **Flexible input** (accepts both categories dan types)
- ✅ **Error-resistant** dengan proper type checking

### **2. Element Properties Extraction Framework**

#### **ElementProperties Class Structure**
```python
class ElementProperties():
    """Helper Class to get necessary parameters based on the type of elements"""
    origin = None #type: XYZ
    vector = None #type: XYZ
    width  = None #type: float
    height = None #type: float

    def __init__(self, el):
        self.el = el
        if type(el) == Wall:
            self.get_wall_properties()
        else:
            self.get_generic_properties()
```

**Adaptation Strategy:**
```python
class WallProperties():
    """Adapted for wall-specific plan generation"""

    def __init__(self, wall):
        self.wall = wall
        self.mid_height = None
        self.bounding_box_2d = None
        self.classification = None

        self.extract_wall_properties()

    def extract_wall_properties(self):
        """Extract wall properties for plan generation"""
        # Adopt wall height calculation logic
        # Adapt bounding box calculation for 2D projection
        # Add classification parameter extraction
```

**Reusable Logic:**
- ✅ **Type-based dispatch** pattern
- ✅ **Property initialization** structure
- ✅ **Error handling** dengan try-catch blocks
- ✅ **Fallback mechanisms** untuk missing parameters

### **3. Progress Tracking System**

#### **Progress Bar Implementation**
```python
counter = 0
max_value = len(selected_elems)
with ProgressBar(cancellable=True) as pb:
    for el in selected_elems:
        if pb.cancelled:
            break

        counter +=1
        pb.update_progress(counter, max_value)
        # Process element
```

**Direct Adoption:**
```python
def generate_wall_plans_with_progress(plan_generator, wall_groups, target_levels):
    total_operations = len(wall_groups) * len(target_levels)

    with ProgressBar(cancellable=True, title="Generating Wall Plans") as pb:
        operation_count = 0

        for classification, walls in wall_groups.items():
            for level in target_levels:
                if pb.cancelled:
                    break

                operation_count += 1
                pb.update_progress(operation_count, total_operations)
                pb.title = f"Creating plan for {classification} at {level.Name}"

                # Generate plan view
                plan_view = plan_generator.create_plan_view_for_wall_group(
                    walls, classification, level.Name
                )
```

**Benefits:**
- ✅ **Cancellable operations** - user dapat stop process
- ✅ **Real-time feedback** - progress title updates
- ✅ **Error resilience** - continue on individual failures
- ✅ **User experience** - professional progress indication

### **4. Transaction Management Pattern**

#### **EF Transaction Pattern**
```python
t = Transaction(doc, 'EF_Section Generator')
t.Start()

try:
    # All operations here
    # View creation, sheet placement, etc.

    t.Commit()
except Exception as e:
    t.RollBack()
    forms.alert(f"Error: {e}")
```

**Adaptation for Wall Plan Generator:**
```python
def generate_wall_plans_batch(plan_generator, wall_groups, target_levels):
    """Batch generation with proper transaction management"""

    t = Transaction(doc, 'Wall Plan Generator')
    t.Start()

    try:
        results = []

        for classification, walls in wall_groups.items():
            for level in target_levels:
                try:
                    plan_view = plan_generator.create_plan_view_for_wall_group(
                        walls, classification, level.Name
                    )

                    results.append({
                        'classification': classification,
                        'level': level.Name,
                        'view': plan_view,
                        'status': 'success' if plan_view else 'failed'
                    })

                except Exception as e:
                    results.append({
                        'classification': classification,
                        'level': level.Name,
                        'view': None,
                        'status': 'error',
                        'error': str(e)
                    })

        t.Commit()
        return results

    except Exception as e:
        t.RollBack()
        forms.alert(f"Critical error during generation: {e}")
        return []
```

**Benefits:**
- ✅ **Atomic operations** - all or nothing approach
- ✅ **Error recovery** - rollback on critical failures
- ✅ **Resource management** - proper transaction lifecycle
- ✅ **Exception handling** - comprehensive error management

### **5. Results Display System**

#### **Table Output Pattern**
```python
output = script.get_output()

# Display results table
output.print_table(table_data=table_data,
                  title="New Sections",
                  columns=["Category","TypeName","Element", "Sheet", "Elevation", "Cross", "Plan"])
```

**Adaptation for Wall Plans:**
```python
def display_generation_results(results):
    output = script.get_output()

    output.print_md("# Wall Plan Generation Results")

    table_data = []
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        view_link = output.linkify(result['view'].Id) if result['view'] else "Failed"

        row = [
            result['classification'],
            result['level'],
            result['wall_count'],
            status_icon,
            view_link
        ]
        table_data.append(row)

    output.print_table(
        table_data=table_data,
        title="Generation Results",
        columns=["Classification", "Level", "Wall Count", "Status", "View"]
    )
```

**Benefits:**
- ✅ **Structured output** - easy to read results
- ✅ **Interactive links** - clickable view references
- ✅ **Status indicators** - visual success/failure feedback
- ✅ **Comprehensive reporting** - all operations documented

### **6. Error Handling Patterns**

#### **Debug Mode Error Handling**
```python
try:
    # Operation that might fail
    result = some_operation()
except Exception as e:
    if EXEC_PARAMS.debug_mode:
        import traceback
        print(traceback.format_exc())
    # Continue processing or log error
```

**Benefits:**
- ✅ **Development support** - detailed error info in debug mode
- ✅ **Production stability** - silent failure handling
- ✅ **Flexible logging** - configurable error verbosity
- ✅ **Graceful degradation** - continue processing on errors

### **7. Utility Functions**

#### **Flatten List Function**
```python
def flatten_list(lst):
    new_lst = []
    for i in lst:
        if isinstance(i,list):
            new_lst += i
        else:
            new_lst.append(i)
    return new_lst
```

**Use Case:** Handling nested category selections from multi-select dialogs.

#### **Unique Naming Functions**
```python
# Pattern for ensuring unique names
def ensure_unique_name(base_name, existing_names):
    counter = 1
    unique_name = base_name
    while unique_name in existing_names:
        unique_name = f"{base_name}_{counter}"
        counter += 1
    return unique_name
```

**Benefits:**
- ✅ **Conflict resolution** - automatic unique naming
- ✅ **Consistent pattern** - reusable across different entities
- ✅ **Scalable** - handles large numbers of duplicates

## 🏗️ Architectural Patterns to Adopt

### **1. Class-Based Architecture**
- **Separation of concerns** - different classes untuk different responsibilities
- **Single responsibility principle** - each class has one primary function
- **Composition over inheritance** - flexible component assembly

### **2. Factory Pattern for Element Processing**
```python
# EF uses type-based dispatch
if type(el) == Wall:
    self.get_wall_properties()
else:
    self.get_generic_properties()
```

### **3. Builder Pattern for Complex Objects**
```python
# SectionGenerator builds views step by step
gen = SectionGenerator(doc, origin=E.origin, vector=E.vector, ...)
views = gen.create_sections()
```

### **4. Strategy Pattern for Different Processing Types**
- Different strategies untuk different element types
- Pluggable algorithms untuk property extraction
- Configurable behavior berdasarkan requirements

## 📋 Integration Points with Logic Library

### **Parameter Extraction Integration**
```python
# Adopt proven parameter extraction from logic-library
from logic_library.active.utilities.parameters.definitive_extraction import extract_parameter_by_name

def get_wall_scheme_classification(wall):
    return extract_parameter_by_name(wall, "Wall Scheme Classification")
```

### **Error Handling Standardization**
```python
# Use consistent error handling patterns from logic-library
try:
    result = operation()
except ParameterNotFoundError:
    # Handle missing parameter
except GeometryCalculationError:
    # Handle geometric issues
```

## 🎯 Recommended Adoption Strategy

### **Phase 1: Direct Adoption (Low Risk)**
1. **EF_SelectionFilter** - Copy langsung untuk wall selection
2. **Progress bar pattern** - Adopt untuk user feedback
3. **Transaction management** - Use established pattern
4. **Results display system** - Adapt untuk wall plan results

### **Phase 2: Adaptation (Medium Risk)**
1. **ElementProperties structure** - Adapt untuk wall-specific properties
2. **Error handling patterns** - Customize untuk wall plan context
3. **Naming conventions** - Modify untuk wall plan naming scheme

### **Phase 3: Integration (Higher Risk)**
1. **Logic-library integration** - Connect dengan parameter extraction
2. **Custom algorithms** - Develop wall-specific geometric calculations
3. **Advanced features** - Add wall-specific optimizations

## ⚡ Quick Wins from EF Script

1. **Copy-paste ready components:**
   - Selection filter class
   - Progress bar implementation
   - Transaction pattern
   - Results table display

2. **Adaptable patterns:**
   - Element processing structure
   - Error handling approach
   - Naming conflict resolution

3. **Learning opportunities:**
   - Type-based dispatch
   - Geometric calculations
   - User interface patterns

## 🚀 Implementation Priority

### **High Priority (Essential)**
- EF_SelectionFilter class
- Transaction management pattern
- Progress tracking system
- Results display system

### **Medium Priority (Recommended)**
- ElementProperties structure adaptation
- Error handling patterns
- Utility functions

### **Low Priority (Optional)**
- Advanced geometric algorithms
- Custom UI components
- Performance optimizations

---

*This analysis provides a roadmap for adopting proven components from the EF script while maintaining architectural consistency and code quality.*