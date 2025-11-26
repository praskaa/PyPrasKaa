# Wall Plan Generator - Implementation Guide

## ✅ Confirmed Requirements

Berdasarkan klarifikasi user, berikut adalah spesifikasi final:

### **View Scope:**
- ✅ **Satu plan view** untuk semua dinding dengan classification yang sama di satu level
- ✅ **Combined display**: Semua dinding dengan classification tertentu di level tersebut

### **Level Logic:**
- ✅ **Mid-height approach**: Ambil tengah bentang tinggi dari dinding
- ✅ **Wall-based elevation**: Tidak menggunakan level elevation langsung

### **Sheet Creation:**
- ✅ **No auto-sheet creation**: Fokus pada view naming dan organization
- ✅ **Manual sheet placement**: User place views ke sheet sesuai kebutuhan

### **Parameter Handling:**
- ✅ **Existing parameter**: "Wall Scheme Classification" sudah ada di template
- ✅ **Integration planning**: Gunakan logic-library untuk ekstraksi parameter

## 🏗️ Implementation Architecture

### **Core Classes Design**

#### **1. WallClassifier - Classification Engine**
```python
class WallClassifier:
    """Handles wall classification and grouping logic"""

    def __init__(self, walls):
        self.walls = walls
        self.classification_param = "Wall Scheme Classification"

    def classify_walls(self):
        """Group walls by classification parameter"""
        from logic_library.active.utilities.parameters.definitive_extraction import extract_parameter_by_name

        groups = defaultdict(list)
        for wall in self.walls:
            classification = extract_parameter_by_name(wall, self.classification_param)
            if classification:
                groups[classification].append(wall)
        return groups

    def validate_classifications(self):
        """Ensure all walls have valid classifications"""
        unclassified = []
        for wall in self.walls:
            if not extract_parameter_by_name(wall, self.classification_param):
                unclassified.append(wall)

        if unclassified:
            # Show warning and option to continue or cancel
            return False, unclassified
        return True, []
```

#### **2. WallPlanGenerator - View Creation Engine**
```python
class WallPlanGenerator:
    """Handles plan view creation for wall groups"""

    def __init__(self, doc):
        self.doc = doc

    def calculate_wall_mid_height(self, wall):
        """Calculate mid-height elevation for wall"""
        try:
            # Get wall height parameter
            height_param = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
            if height_param and height_param.HasValue:
                wall_height = height_param.AsDouble()

                # Get wall base elevation
                base_param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
                if base_param:
                    base_level = self.doc.GetElement(base_param.AsElementId())
                    base_elevation = base_level.Elevation

                    # Calculate mid-height
                    mid_height = base_elevation + (wall_height / 2)
                    return mid_height
        except:
            pass

        # Fallback: use wall bounding box center
        bb = wall.get_BoundingBox(None)
        if bb:
            return (bb.Min.Z + bb.Max.Z) / 2

        return 0.0  # Default fallback

    def calculate_group_bounding_box(self, walls, target_elevation):
        """Calculate 2D bounding box for wall group at specific elevation"""
        if not walls:
            return None

        # Initialize with first wall
        first_bb = self.calculate_wall_bounding_box_at_elevation(walls[0], target_elevation)
        if not first_bb:
            return None

        min_x, max_x = first_bb[0], first_bb[1]
        min_y, max_y = first_bb[2], first_bb[3]

        # Expand for other walls
        for wall in walls[1:]:
            wall_bb = self.calculate_wall_bounding_box_at_elevation(wall, target_elevation)
            if wall_bb:
                min_x = min(min_x, wall_bb[0])
                max_x = max(max_x, wall_bb[1])
                min_y = min(min_y, wall_bb[2])
                max_y = max(max_y, wall_bb[3])

        return min_x, max_x, min_y, max_y

    def calculate_wall_bounding_box_at_elevation(self, wall, elevation):
        """Calculate wall footprint at specific elevation"""
        try:
            # Get wall curve
            wall_curve = wall.Location.Curve

            # Get wall width (thickness)
            width_param = wall.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
            wall_width = width_param.AsDouble() if width_param else 1.0

            # Calculate wall centerline at elevation
            start_point = wall_curve.GetEndPoint(0)
            end_point = wall_curve.GetEndPoint(1)

            # Create wall profile at elevation
            wall_vector = end_point - start_point
            wall_length = wall_vector.GetLength()

            if wall_length > 0:
                # Calculate perpendicular vector for wall thickness
                perp_vector = XYZ(-wall_vector.Y, wall_vector.X, 0).Normalize()
                half_width = wall_width / 2

                # Calculate corner points
                p1 = start_point + (perp_vector * half_width)
                p2 = start_point - (perp_vector * half_width)
                p3 = end_point - (perp_vector * half_width)
                p4 = end_point + (perp_vector * half_width)

                # Get bounding box coordinates
                x_coords = [p1.X, p2.X, p3.X, p4.X]
                y_coords = [p1.Y, p2.Y, p3.Y, p4.Y]

                return min(x_coords), max(x_coords), min(y_coords), max(y_coords)

        except Exception as e:
            print(f"Error calculating wall bounding box: {e}")

        return None

    def create_plan_view_for_wall_group(self, walls, classification, level_name):
        """Create plan view for wall group at calculated elevation"""

        if not walls:
            return None

        try:
            # Calculate target elevation (mid-height of first wall)
            target_elevation = self.calculate_wall_mid_height(walls[0])

            # Calculate group bounding box
            group_bb = self.calculate_group_bounding_box(walls, target_elevation)
            if not group_bb:
                return None

            # Create plan view name
            wall_type = self.get_wall_type_name(walls[0])
            view_name = f"{wall_type}-{classification}-{level_name}"

            # Ensure unique name
            view_name = self.ensure_unique_view_name(view_name)

            # Create plan view
            plan_view = self.create_plan_view_at_elevation(target_elevation, view_name)

            # Set crop box to group bounding box
            self.set_view_crop_box(plan_view, group_bb, target_elevation)

            return plan_view

        except Exception as e:
            print(f"Error creating plan view for {classification}: {e}")
            return None

    def create_plan_view_at_elevation(self, elevation, view_name):
        """Create a plan view at specific elevation"""
        try:
            # Find or create appropriate level for this elevation
            target_level = self.find_or_create_level_for_elevation(elevation)

            # Create plan view
            plan_view = ViewPlan.Create(self.doc, target_level.Id, view_name)

            return plan_view

        except Exception as e:
            print(f"Error creating plan view: {e}")
            return None

    def find_or_create_level_for_elevation(self, elevation):
        """Find existing level or create new one at elevation"""
        # First, try to find existing level at this elevation
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()

        tolerance = 0.1  # 100mm tolerance

        for level in levels:
            if abs(level.Elevation - elevation) < tolerance:
                return level

        # Create new level if not found
        level_name = f"Wall Plan Level - {elevation:.2f}"
        new_level = Level.Create(self.doc, elevation)
        new_level.Name = self.ensure_unique_level_name(level_name)

        return new_level

    def set_view_crop_box(self, view, bounding_box, elevation):
        """Set view crop box to focus on wall group"""
        try:
            # Unpack bounding box
            min_x, max_x, min_y, max_y = bounding_box

            # Add padding (10% of dimensions)
            width = max_x - min_x
            height = max_y - min_y
            padding_x = width * 0.1
            padding_y = height * 0.1

            # Create crop box points
            crop_min = XYZ(min_x - padding_x, min_y - padding_y, elevation - 1)
            crop_max = XYZ(max_x + padding_x, max_y + padding_y, elevation + 1)

            # Set crop box
            crop_box = view.CropBox
            crop_box.Min = crop_min
            crop_box.Max = crop_max
            view.CropBox = crop_box

            # Enable crop box
            view.CropBoxVisible = True
            view.CropBoxActive = True

        except Exception as e:
            print(f"Error setting crop box: {e}")

    def get_wall_type_name(self, wall):
        """Get wall type name for naming convention"""
        try:
            wall_type = self.doc.GetElement(wall.GetTypeId())
            return wall_type.Name
        except:
            return "Wall"

    def ensure_unique_view_name(self, base_name):
        """Ensure view name is unique"""
        existing_views = FilteredElementCollector(self.doc).OfClass(View).ToElements()
        existing_names = [v.Name for v in existing_views]

        counter = 1
        unique_name = base_name
        while unique_name in existing_names:
            unique_name = f"{base_name}_{counter}"
            counter += 1

        return unique_name

    def ensure_unique_level_name(self, base_name):
        """Ensure level name is unique"""
        existing_levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()
        existing_names = [l.Name for l in existing_levels]

        counter = 1
        unique_name = base_name
        while unique_name in existing_names:
            unique_name = f"{base_name}_{counter}"
            counter += 1

        return unique_name
```

#### **3. LevelSelector - Level Management**
```python
class LevelSelector:
    """Handles level selection and validation"""

    def __init__(self, doc):
        self.doc = doc

    def select_target_levels(self):
        """Present level selection dialog to user"""
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()

        # Create level options dictionary
        level_options = {}
        for level in levels:
            elevation_text = f"{level.Elevation * 3.28084:.2f}'"  # Convert to feet for display
            display_name = f"{level.Name} ({elevation_text})"
            level_options[display_name] = level

        # Use select_from_dict for multi-selection
        selected_display_names = select_from_dict(
            level_options,
            title="Select Target Levels",
            label="Choose levels where wall plan details should be created:",
            SelectMultiple=True
        )

        if not selected_display_names:
            return []

        # Return actual level objects
        return [level_options[name] for name in selected_display_names]

    def validate_level_selection(self, selected_levels):
        """Validate selected levels"""
        if not selected_levels:
            forms.alert("No levels selected. Please select at least one level.", title="Selection Error")
            return False

        # Check for duplicate elevations (within tolerance)
        elevations = [level.Elevation for level in selected_levels]
        tolerance = 0.1  # 100mm

        for i, elev1 in enumerate(elevations):
            for j, elev2 in enumerate(elevations[i+1:], i+1):
                if abs(elev1 - elev2) < tolerance:
                    forms.alert(f"Selected levels are too close in elevation: {selected_levels[i].Name} and {selected_levels[j].Name}",
                              title="Level Validation Error")
                    return False

        return True
```

## 🔄 Main Workflow Implementation

### **Main Function**
```python
def wall_plan_generator_main():
    """
    Main function for Wall Plan Generator
    """

    # 1. Select walls
    selected_walls = select_walls_for_plan_generation()
    if not selected_walls:
        forms.alert("No walls selected.", title="Selection Cancelled")
        return

    # 2. Initialize classifier and validate
    classifier = WallClassifier(selected_walls)
    is_valid, unclassified_walls = classifier.validate_classifications()

    if not is_valid:
        # Show unclassified walls and ask user
        show_unclassified_walls_warning(unclassified_walls)
        if not forms.alert("Continue with classified walls only?", yes=True, no=True):
            return

    # 3. Get wall groups
    wall_groups = classifier.classify_walls()

    if not wall_groups:
        forms.alert("No valid wall classifications found.", title="Classification Error")
        return

    # 4. Show classification summary
    show_classification_summary(wall_groups)

    # 5. Select target levels
    level_selector = LevelSelector(doc)
    target_levels = level_selector.select_target_levels()

    if not level_selector.validate_level_selection(target_levels):
        return

    # 6. Initialize plan generator
    plan_generator = WallPlanGenerator(doc)

    # 7. Generate plans with progress tracking
    results = generate_wall_plans_with_progress(
        plan_generator, wall_groups, target_levels
    )

    # 8. Display results
    display_generation_results(results)
```

### **Progress Tracking Function**
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

                # Update progress message
                pb.title = f"Creating plan for {classification} at {level.Name}"

                try:
                    # Generate plan view
                    plan_view = plan_generator.create_plan_view_for_wall_group(
                        walls, classification, level.Name
                    )

                    if plan_view:
                        results.append({
                            'classification': classification,
                            'level': level.Name,
                            'view': plan_view,
                            'wall_count': len(walls),
                            'status': 'success'
                        })
                    else:
                        results.append({
                            'classification': classification,
                            'level': level.Name,
                            'view': None,
                            'wall_count': len(walls),
                            'status': 'failed',
                            'error': 'View creation failed'
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

## 🎨 User Interface Functions

### **Wall Selection**
```python
def select_walls_for_plan_generation():
    """Present wall selection interface"""

    # Define wall categories
    wall_categories = [BuiltInCategory.OST_Walls]

    # Create selection filter
    selection_filter = EF_SelectionFilter(wall_categories)

    try:
        with forms.WarningBar(title='Select walls for plan generation and click "Finish"'):
            ref_selected_walls = uidoc.Selection.PickObjects(
                ObjectType.Element,
                selection_filter
            )

        selected_walls = [doc.GetElement(ref) for ref in ref_selected_walls]
        return selected_walls

    except:
        return []
```

### **Classification Summary Display**
```python
def show_classification_summary(wall_groups):
    """Display wall classification summary"""

    output = script.get_output()

    output.print_md("# Wall Classification Summary")
    output.print_md("---")

    total_walls = sum(len(walls) for walls in wall_groups.values())
    output.print_md(f"**Total Walls Selected:** {total_walls}")
    output.print_md(f"**Classifications Found:** {len(wall_groups)}")
    output.print_md("")

    for classification, walls in wall_groups.items():
        output.print_md(f"- **{classification}**: {len(walls)} walls")

    output.print_md("---")
```

### **Results Display**
```python
def display_generation_results(results):
    """Display generation results in table format"""

    output = script.get_output()

    output.print_md("# Wall Plan Generation Results")
    output.print_md("---")

    # Prepare table data
    table_data = []
    success_count = 0
    error_count = 0

    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"

        if result['view']:
            view_link = output.linkify(result['view'].Id)
        else:
            view_link = "Failed"

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
        else:
            error_count += 1

    # Display summary
    output.print_md(f"**Successful:** {success_count}")
    output.print_md(f"**Failed:** {error_count}")
    output.print_md("")

    # Display table
    output.print_table(
        table_data=table_data,
        title="Generation Results",
        columns=["Classification", "Level", "Wall Count", "Status", "View"]
    )
```

## 🔧 Technical Implementation Details

### **Coordinate System Handling**
- **Revit Internal Units**: Semua kalkulasi menggunakan feet (internal Revit units)
- **Elevation Calculation**: Mid-height berdasarkan wall base + (height/2)
- **Bounding Box**: 2D projection untuk plan view crop region

### **Error Handling Strategy**
- **Parameter Validation**: Check existence sebelum processing
- **Geometric Calculation**: Fallback methods jika primary method gagal
- **View Creation**: Continue processing jika satu view gagal
- **Naming Conflicts**: Auto-increment untuk unique names

### **Performance Optimizations**
- **Batch Processing**: Process satu classification pada satu waktu
- **Memory Management**: Release object references setelah use
- **Minimal API Calls**: Cache hasil kalkulasi yang bisa di-reuse

## 🚀 Usage Example

```python
# Example usage flow:
# 1. User selects walls with classifications W5, W10, W15
# 2. User selects levels: Level 1, Level 5, Level 10
# 3. Script generates:
#    - "Basic Wall-W5-Level 1" (plan view at mid-height of W5 walls)
#    - "Basic Wall-W5-Level 5" (plan view at mid-height of W5 walls)
#    - "Basic Wall-W5-Level 10" (plan view at mid-height of W5 walls)
#    - "Curtain Wall-W10-Level 1" (plan view at mid-height of W10 walls)
#    - etc.
```

## 📋 Next Steps

1. **Implement Core Classes** - WallClassifier, WallPlanGenerator, LevelSelector
2. **Create UI Functions** - Selection, validation, progress tracking
3. **Test Parameter Integration** - Logic-library parameter extraction
4. **Add Error Handling** - Comprehensive exception management
5. **Performance Testing** - Large wall selections and multiple levels

---

*This implementation guide provides the complete technical specification for the Wall Plan Generator based on clarified requirements.*