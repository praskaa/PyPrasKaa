# Plan View Parameters Analysis - Wall Plan Generator

## 🎯 Understanding SectionGenerator vs Plan View Creation

### **EF SectionGenerator Parameters (for Sections):**
```python
# Section views require 3D spatial parameters
origin: Titik pusat untuk section plane
vector: Arah utama elemen (orientation)
width: Lebar view crop region
height: Tinggi view crop region
offset: Jarak section plane dari origin
depth: Kedalaman view (3D cropping)
depth_offset: Offset untuk depth cropping
```

**Why these parameters for sections:**
- **Section Plane Definition**: Origin + vector + offset = section plane location/orientation
- **3D Cropping**: Width + height + depth + depth_offset = view volume
- **Spatial Positioning**: All parameters needed for 3D section geometry

## 🏗️ Plan View Parameters - What We Actually Need

### **Core Parameters for Plan View Creation:**

#### **1. Elevation (Z-coordinate)**
```python
# The only spatial parameter we need for plan views
target_elevation = float  # Z-coordinate where plan view is created
```
**Purpose:** Defines the horizontal cutting plane elevation

#### **2. View Name**
```python
# Naming convention for organization
view_name = "Type-Classification-Level"  # e.g., "Basic Wall-W5-Level 1"
```
**Purpose:** Unique identification and organization

#### **3. Crop Region (2D Bounding Box)**
```python
# 2D rectangular region for view cropping
crop_box = {
    'min_x': float,
    'max_x': float,
    'min_y': float,
    'max_y': float
}
```
**Purpose:** Focus view on relevant wall group area

### **Derived Parameters (Calculated, Not Input):**

#### **4. Level Reference**
```python
# May need to create/find level at target elevation
target_level = Level  # Revit Level object at target_elevation
```
**Purpose:** Plan views are associated with levels in Revit

#### **5. View Template (Optional)**
```python
# Optional visual settings
view_template = View  # Predefined view template
```
**Purpose:** Consistent visual appearance

## 🔍 Parameter Mapping: SectionGenerator → Plan View

| SectionGenerator Parameter | Plan View Equivalent | Why Different |
|---------------------------|---------------------|---------------|
| `origin` (XYZ) | `target_elevation` (float) | Plan = horizontal cut, only Z matters |
| `vector` (XYZ) | N/A | Plan views are always horizontal |
| `width` | `crop_box.width` | 2D crop region instead of 3D volume |
| `height` | `crop_box.height` | 2D crop region instead of 3D volume |
| `offset` | N/A | Plan at exact elevation, no offset |
| `depth` | N/A | Plan views are 2D projections |
| `depth_offset` | N/A | No 3D cropping needed |

## 📐 Plan View Creation Algorithm

### **Minimal Parameter Set:**
```python
def create_wall_plan_view(walls, classification, level_name):
    """
    Create plan view for wall group - minimal parameters needed
    """

    # 1. Calculate target elevation (mid-height of walls)
    target_elevation = calculate_wall_group_elevation(walls)

    # 2. Generate view name
    view_name = generate_plan_view_name(walls, classification, level_name)

    # 3. Calculate 2D crop region
    crop_region = calculate_wall_group_crop_region(walls, target_elevation)

    # 4. Create plan view (these are the actual parameters needed)
    plan_view = ViewPlan.Create(
        doc=doc,
        level=get_or_create_level_at_elevation(target_elevation),
        view_name=view_name
    )

    # 5. Set crop box
    set_plan_view_crop_box(plan_view, crop_region)

    return plan_view
```

### **Actual Revit API Parameters for Plan Views:**
```python
# ViewPlan.Create() parameters:
doc: Document          # Document context
level: Level          # Associated level (we create/find this)
view_name: str        # View name

# Additional settings (not creation parameters):
crop_box: BoundingBoxXYZ  # Set after creation
view_template: View       # Optional, applied after creation
```

## 🎨 Visual Comparison: Section vs Plan

### **Section View (3D Spatial):**
```
              ↑ height
             ┌─────────────────┐
             │                 │
        ← width →  Section Plane (at origin + offset)
             │                 │
             └─────────────────┘
                    ↓ depth
                    (depth_offset)
```

### **Plan View (2D Horizontal):**
```
             Horizontal Cutting Plane (at target_elevation)
             ──────────────────────────────────────────
             │                                         │
             │           Wall Group Crop Region        │
             │           (min_x, min_y) to (max_x, max_y) │
             │                                         │
             ──────────────────────────────────────────
```

## 🔧 Parameter Calculation Logic

### **1. Target Elevation Calculation:**
```python
def calculate_wall_group_elevation(walls):
    """Calculate representative elevation for plan view"""
    if not walls:
        return 0.0

    # Use first wall as representative
    first_wall = walls[0]

    # Get wall base elevation
    base_level = get_wall_base_level(first_wall)
    base_elevation = base_level.Elevation if base_level else 0.0

    # Get wall height
    height_param = first_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
    wall_height = height_param.AsDouble() if height_param else 0.0

    # Calculate mid-height
    return base_elevation + (wall_height / 2)
```

### **2. Crop Region Calculation:**
```python
def calculate_wall_group_crop_region(walls, elevation):
    """Calculate 2D bounding box for wall group at elevation"""
    if not walls:
        return None

    # Initialize with first wall
    min_x, max_x, min_y, max_y = get_wall_2d_bounds_at_elevation(walls[0], elevation)

    # Expand for all walls
    for wall in walls[1:]:
        wall_bounds = get_wall_2d_bounds_at_elevation(wall, elevation)
        if wall_bounds:
            min_x = min(min_x, wall_bounds[0])
            max_x = max(max_x, wall_bounds[1])
            min_y = min(min_y, wall_bounds[2])
            max_y = max(max_y, wall_bounds[3])

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
```

### **3. Level Management:**
```python
def get_or_create_level_at_elevation(elevation):
    """Find existing level or create new one at elevation"""

    # Search existing levels
    levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    tolerance = 0.1  # 100mm tolerance

    for level in levels:
        if abs(level.Elevation - elevation) < tolerance:
            return level

    # Create new level
    level_name = f"Wall Plan Level - {elevation:.2f}"
    new_level = Level.Create(doc, elevation)
    new_level.Name = ensure_unique_level_name(level_name)

    return new_level
```

## 📊 Parameter Summary Table

| Parameter Type | SectionGenerator (3D) | Plan View (2D) | Status |
|----------------|----------------------|----------------|--------|
| **Spatial Definition** | origin (XYZ) + vector (XYZ) + offset | target_elevation (float) | ✅ Simplified |
| **View Bounds** | width + height + depth + depth_offset | crop_box (min_x, max_x, min_y, max_y) | ✅ Simplified |
| **Orientation** | vector determines plane orientation | Always horizontal (XY plane) | ✅ Fixed |
| **Cropping** | 3D volume cropping | 2D rectangular cropping | ✅ Simplified |
| **Level Association** | Not applicable | Required (create/find level) | ➕ Added |
| **View Template** | Optional | Optional | ✅ Same |

## 🚀 Implementation Impact

### **Reduced Complexity:**
- **From 7 parameters** (SectionGenerator) → **3 core parameters** (Plan View)
- **From 3D spatial calculations** → **2D geometric calculations**
- **From complex section planes** → **Simple horizontal cutting planes**

### **New Requirements:**
- **Level management** (create/find levels at elevations)
- **2D bounding box calculations** (wall footprints)
- **Elevation-based logic** (mid-height calculations)

### **Maintained Features:**
- **Progress tracking**
- **Error handling**
- **Results display**
- **Transaction management**

## 💡 Key Insight

**SectionGenerator is overkill for plan views.** Plan views hanya butuh:
1. **Elevation** (Z-coordinate)
2. **Name** (unique identifier)
3. **Crop region** (2D bounds)

Semua parameter 3D spatial lainnya (vector, offset, depth) tidak diperlukan karena plan views selalu horizontal dan 2D.

---

*This analysis shows that plan view creation requires significantly fewer and different parameters compared to section view generation.*