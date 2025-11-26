# Wall Plan Generator - Implementation Plan & Code Structure

## 🎯 Implementation Strategy

Berdasarkan analisis lengkap, kita akan mengimplementasikan Wall Plan Generator dengan pendekatan **modular** dan **incremental**, memanfaatkan komponen reusable dari EF script.

## 📁 Project Structure

```
PrasKaaPyKit.tab/
├── Wall_Plan_Generator.panel/
│   └── WallPlanGenerator.pushbutton/
│       ├── script.py                 # Main script
│       ├── wall_classifier.py        # Wall classification logic
│       ├── wall_plan_generator.py    # Plan view generation
│       ├── level_selector.py         # Level management
│       └── utils.py                  # Shared utilities
```

## 🚀 Phase-by-Phase Implementation

### **Phase 1: Foundation Setup (1-2 days)**

#### **1.1 Create Project Structure**
```python
# script.py - Main entry point
__title__ = "Wall Plan Generator"
__version__ = "1.0.0"

# Import all modules
from wall_classifier import WallClassifier
from wall_plan_generator import WallPlanGenerator
from level_selector import LevelSelector
from utils import *
```

#### **1.2 Setup Reusable Components**
```python
# Copy proven components from EF script
class EF_SelectionFilter(ISelectionFilter):
    """Direct copy from EF script"""

def flatten_list(lst):
    """Utility function from EF script"""

# Transaction management pattern
def execute_with_transaction(doc, operation_name, operation_func):
    """Adapted transaction pattern from EF"""
```

### **Phase 2: Core Classes Development (3-4 days)**

#### **2.1 WallClassifier Class**
```python
class WallClassifier:
    """Groups walls by classification parameter"""

    def __init__(self, walls):
        self.walls = walls
        self.classification_param = "Wall Scheme Classification"

    def classify_walls(self):
        """Main classification method"""
        from logic_library.active.utilities.parameters.definitive_extraction import extract_parameter_by_name

        groups = defaultdict(list)
        for wall in self.walls:
            classification = extract_parameter_by_name(wall, self.classification_param)
            if classification:
                groups[classification].append(wall)
        return groups

    def validate_classifications(self):
        """Check if all walls have valid classifications"""
        # Implementation for validation
        pass
```

#### **2.2 WallPlanGenerator Class**
```python
class WallPlanGenerator:
    """Handles plan view creation for wall groups"""

    def __init__(self, doc):
        self.doc = doc

    def calculate_wall_mid_height(self, wall):
        """Calculate mid-height elevation for wall"""
        # Implementation for elevation calculation
        pass

    def calculate_group_bounding_box(self, walls, target_elevation):
        """Calculate 2D bounding box for wall group"""
        # Implementation for bounding box calculation
        pass

    def create_plan_view_for_wall_group(self, walls, classification, level_name):
        """Main method to create plan view"""
        # Implementation for view creation
        pass
```

#### **2.3 LevelSelector Class**
```python
class LevelSelector:
    """Handles level selection and validation"""

    def __init__(self, doc):
        self.doc = doc

    def select_target_levels(self):
        """Present level selection dialog"""
        # Implementation for level selection UI
        pass

    def validate_level_selection(self, selected_levels):
        """Validate selected levels"""
        # Implementation for level validation
        pass
```

### **Phase 3: Main Workflow Integration (2-3 days)**

#### **3.1 Main Function Structure**
```python
def wall_plan_generator_main():
    """
    Main function for Wall Plan Generator
    """

    # 1. Wall Selection
    selected_walls = select_walls_for_plan_generation()
    if not selected_walls:
        forms.alert("No walls selected.", title="Selection Cancelled")
        return

    # 2. Classification
    classifier = WallClassifier(selected_walls)
    is_valid, unclassified_walls = classifier.validate_classifications()

    if not is_valid:
        show_unclassified_walls_warning(unclassified_walls)
        if not forms.alert("Continue with classified walls only?", yes=True, no=True):
            return

    wall_groups = classifier.classify_walls()

    # 3. Level Selection
    level_selector = LevelSelector(doc)
    target_levels = level_selector.select_target_levels()

    if not level_selector.validate_level_selection(target_levels):
        return

    # 4. Plan Generation
    plan_generator = WallPlanGenerator(doc)
    results = generate_wall_plans_with_progress(
        plan_generator, wall_groups, target_levels
    )

    # 5. Results Display
    display_generation_results(results)
```

#### **3.2 Progress Tracking Implementation**
```python
def generate_wall_plans_with_progress(plan_generator, wall_groups, target_levels):
    """Generate wall plans with progress bar"""

    total_operations = len(wall_groups) * len(target_levels)
    results = []

    with ProgressBar(cancellable=True, title="Generating Wall Plans") as pb:
        operation_count = 0

        for classification, walls in wall_groups.items():
            for level in target_levels:
                if pb.cancelled:
                    break

                operation_count += 1
                pb.update_progress(operation_count, total_operations)
                pb.title = f"Creating plan for {classification} at {level.Name}"

                try:
                    plan_view = plan_generator.create_plan_view_for_wall_group(
                        walls, classification, level.Name
                    )

                    results.append({
                        'classification': classification,
                        'level': level.Name,
                        'view': plan_view,
                        'wall_count': len(walls),
                        'status': 'success' if plan_view else 'failed'
                    })

                except Exception as e:
                    results.append({
                        'classification': classification,
                        'level': level.Name,
                        'view': None,
                        'wall_count': len(walls),
                        'status': 'error',
                        'error': str(e)
                    })

    return results
```

### **Phase 4: Detailed Method Implementations (4-5 days)**

#### **4.1 Wall Elevation Calculation**
```python
def calculate_wall_mid_height(self, wall):
    """Calculate mid-height elevation for wall"""
    try:
        # Get wall base constraint level
        base_param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
        if base_param and base_param.AsElementId() != ElementId.InvalidElementId:
            base_level = self.doc.GetElement(base_param.AsElementId())
            base_elevation = base_level.Elevation
        else:
            # Fallback to bounding box
            bb = wall.get_BoundingBox(None)
            if bb:
                base_elevation = bb.Min.Z
            else:
                return 0.0

        # Get wall height
        height_param = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
        if height_param and height_param.HasValue:
            wall_height = height_param.AsDouble()
        else:
            # Fallback to bounding box height
            if bb:
                wall_height = bb.Max.Z - bb.Min.Z
            else:
                return base_elevation

        # Calculate mid-height
        return base_elevation + (wall_height / 2)

    except Exception as e:
        print(f"Error calculating wall elevation: {e}")
        return 0.0
```

#### **4.2 Bounding Box Calculation**
```python
def calculate_group_bounding_box(self, walls, target_elevation):
    """Calculate 2D bounding box for wall group at elevation"""
    if not walls:
        return None

    # Initialize with first wall
    first_bb = self.calculate_wall_2d_bounds_at_elevation(walls[0], target_elevation)
    if not first_bb:
        return None

    min_x, max_x, min_y, max_y = first_bb

    # Expand for other walls
    for wall in walls[1:]:
        wall_bb = self.calculate_wall_2d_bounds_at_elevation(wall, target_elevation)
        if wall_bb:
            min_x = min(min_x, wall_bb[0])
            max_x = max(max_x, wall_bb[1])
            min_y = min(min_y, wall_bb[2])
            max_y = max(max_y, wall_bb[3])

    # Add padding (10% of dimensions)
    width = max_x - min_x
    height = max_y - min_y
    padding_x = width * 0.1
    padding_y = height * 0.1

    return {
        'min_x': min_x - padding_x,
        'max_x': max_x + padding_x,
        'min_y': min_y - padding_y,
        'max_y': max_y + padding_y
    }

def calculate_wall_2d_bounds_at_elevation(self, wall, elevation):
    """Calculate wall footprint bounds at specific elevation"""
    try:
        # Get wall curve
        wall_curve = wall.Location.Curve
        if not wall_curve:
            return None

        # Get wall thickness
        width_param = wall.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
        wall_thickness = width_param.AsDouble() if width_param else 1.0

        # Get curve endpoints
        start_point = wall_curve.GetEndPoint(0)
        end_point = wall_curve.GetEndPoint(1)

        # Calculate wall direction vector
        wall_vector = end_point - start_point
        wall_length = wall_vector.GetLength()

        if wall_length == 0:
            return None

        # Calculate perpendicular vector for wall thickness
        perp_vector = XYZ(-wall_vector.Y, wall_vector.X, 0).Normalize()
        half_thickness = wall_thickness / 2

        # Calculate corner points of wall footprint
        p1 = start_point + (perp_vector * half_thickness)
        p2 = start_point - (perp_vector * half_thickness)
        p3 = end_point - (perp_vector * half_thickness)
        p4 = end_point + (perp_vector * half_thickness)

        # Extract X and Y coordinates
        x_coords = [p1.X, p2.X, p3.X, p4.X]
        y_coords = [p1.Y, p2.Y, p3.Y, p4.Y]

        return min(x_coords), max(x_coords), min(y_coords), max(y_coords)

    except Exception as e:
        print(f"Error calculating wall bounds: {e}")
        return None
```

#### **4.3 Plan View Creation**
```python
def create_plan_view_for_wall_group(self, walls, classification, level_name):
    """Create plan view for wall group"""
    try:
        # Calculate target elevation
        target_elevation = self.calculate_wall_mid_height(walls[0])

        # Generate view name
        view_name = self.generate_view_name(walls[0], classification, level_name)
        view_name = self.ensure_unique_view_name(view_name)

        # Get or create level at elevation
        target_level = self.get_or_create_level_at_elevation(target_elevation)

        # Create plan view
        plan_view = ViewPlan.Create(self.doc, target_level.Id, view_name)

        # Calculate and set crop box
        crop_region = self.calculate_group_bounding_box(walls, target_elevation)
        if crop_region:
            self.set_view_crop_box(plan_view, crop_region, target_elevation)

        return plan_view

    except Exception as e:
        print(f"Error creating plan view: {e}")
        return None

def get_or_create_level_at_elevation(self, elevation):
    """Find existing level or create new one"""
    levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()
    tolerance = 0.1  # 100mm tolerance

    for level in levels:
        if abs(level.Elevation - elevation) < tolerance:
            return level

    # Create new level
    level_name = f"Wall Plan Level - {elevation:.2f}"
    level_name = self.ensure_unique_level_name(level_name)

    new_level = Level.Create(self.doc, elevation)
    new_level.Name = level_name

    return new_level

def set_view_crop_box(self, view, crop_region, elevation):
    """Set view crop box to focus on wall group"""
    try:
        crop_box = view.CropBox
        crop_box.Min = XYZ(crop_region['min_x'], crop_region['min_y'], elevation - 0.5)
        crop_box.Max = XYZ(crop_region['max_x'], crop_region['max_y'], elevation + 0.5)
        view.CropBox = crop_box

        view.CropBoxVisible = True
        view.CropBoxActive = True

    except Exception as e:
        print(f"Error setting crop box: {e}")
```

### **Phase 5: UI & Integration (2-3 days)**

#### **5.1 Wall Selection Interface**
```python
def select_walls_for_plan_generation():
    """Present wall selection interface"""
    wall_categories = [BuiltInCategory.OST_Walls]

    selection_filter = EF_SelectionFilter(wall_categories)

    try:
        with forms.WarningBar(title='Select walls for plan generation and click "Finish"'):
            ref_selected_walls = uidoc.Selection.PickObjects(
                ObjectType.Element, selection_filter
            )

        selected_walls = [doc.GetElement(ref) for ref in ref_selected_walls]
        return selected_walls

    except:
        return []
```

#### **5.2 Level Selection Interface**
```python
def select_target_levels(self):
    """Present level selection dialog"""
    levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()

    level_options = {}
    for level in levels:
        elevation_text = f"{level.Elevation * 3.28084:.2f}'"  # Convert to feet
        display_name = f"{level.Name} ({elevation_text})"
        level_options[display_name] = level

    selected_names = select_from_dict(
        level_options,
        title="Select Target Levels",
        label="Choose levels where wall plan details should be created:",
        SelectMultiple=True
    )

    if not selected_names:
        return []

    return [level_options[name] for name in selected_names]
```

#### **5.3 Results Display**
```python
def display_generation_results(results):
    """Display generation results"""
    output = script.get_output()

    output.print_md("# Wall Plan Generation Results")

    table_data = []
    success_count = 0

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

        if result['status'] == 'success':
            success_count += 1

    output.print_md(f"**Successful:** {success_count} | **Total:** {len(results)}")
    output.print_table(
        table_data=table_data,
        title="Generation Results",
        columns=["Classification", "Level", "Wall Count", "Status", "View"]
    )
```

### **Phase 6: Testing & Refinement (2-3 days)**

#### **6.1 Unit Testing**
- Test parameter extraction
- Test elevation calculations
- Test bounding box calculations
- Test view creation

#### **6.2 Integration Testing**
- Test with real Revit project
- Test with various wall types
- Test with different classifications
- Test error scenarios

#### **6.3 Performance Testing**
- Test with large wall selections
- Test with multiple levels
- Monitor memory usage
- Optimize bottlenecks

## 📋 Development Checklist

### **Week 1: Foundation**
- [ ] Create project structure
- [ ] Copy reusable components from EF
- [ ] Setup basic class skeletons
- [ ] Implement parameter extraction integration

### **Week 2: Core Logic**
- [ ] Complete WallClassifier
- [ ] Complete elevation calculation
- [ ] Complete bounding box calculation
- [ ] Complete plan view creation

### **Week 3: UI & Workflow**
- [ ] Implement wall selection UI
- [ ] Implement level selection UI
- [ ] Implement progress tracking
- [ ] Implement results display

### **Week 4: Testing & Polish**
- [ ] Unit testing all methods
- [ ] Integration testing
- [ ] Error handling refinement
- [ ] Performance optimization

### **Week 5: Documentation & Deployment**
- [ ] Code documentation
- [ ] User guide creation
- [ ] Final testing
- [ ] Deployment to pyRevit

## 🎯 Success Metrics

- **Functionality**: All specified features working
- **Performance**: < 5 seconds for typical project
- **Reliability**: > 95% success rate
- **Usability**: Intuitive workflow
- **Maintainability**: Clean, documented code

## 🔧 Technical Dependencies

- `logic-library.active.utilities.parameters.definitive_extraction`
- `Snippets._vectors` (if needed for vector calculations)
- `GUI.forms.select_from_dict`
- `pyrevit.forms.ProgressBar`

---

*This implementation plan provides a structured approach to building the Wall Plan Generator, leveraging proven components while implementing new functionality efficiently.*