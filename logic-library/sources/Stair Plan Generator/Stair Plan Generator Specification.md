# Stair Plan Generator - Technical Specification & Planning

## Overview
**Stair Plan Generator** adalah script pyRevit yang secara otomatis membuat plan views untuk multi-story stairs pada level-level tertentu. Script ini akan membuat denah tangga yang menunjukkan step tangga, landing, dan orientasi yang tepat untuk setiap level yang dipilih user.

## Concept Analysis

### Stair Plan Visualization Requirements

#### **Typical Stair Plan Views**
1. **Floor Level Plans**: Menampilkan tangga yang terlihat dari atas
   - Step tangga yang turun ke level bawah
   - Landing/bordes di level tersebut (meskipun secara fisik landing berada di antara level)
   - Step tangga yang naik ke level atas (terbatas)

2. **Visual Requirements per Level**:
   ```
   Level 16 Stair Plan:
   ├── Shows: Steps going DOWN to Level 15 (full visibility)
   ├── Shows: Landing at Level 16 (meskipun landing fisik berada antara L15-L16)
   ├── Shows: Steps going UP to Level 17 (partial, usually not full landing)
   └── Shows: Stair direction and handrail indications
   ```

3. **Landing Position Reality**:
   ```
   Physical Reality:
   ├── Level 15 Floor: 50.00' elevation
   ├── Landing between L15-L16: ~50.50' - 51.50' elevation (midway)
   ├── Level 16 Floor: 53.00' elevation

   Plan View Convention:
   ├── Level 16 Plan shows landing as if it's at Level 16
   ├── Landing represented in plan view of the level it serves
   ├── Visual convention, not physical accuracy
   ```

#### **Key Challenges vs Wall Plans**
- **Non-rectangular geometry**: Stairs have complex L-shaped or U-shaped footprints
- **Multi-level visibility**: Need to show stairs connecting multiple levels
- **Directional information**: Stair direction (up/down) must be clear
- **Landing representation**: Landings appear at different levels
- **Safety elements**: Handrails, guardrails may need representation

## Technical Requirements Analysis

### Stair Geometry Understanding

#### **Stair Components in Revit**
```python
# Main stair components:
stair = Stair  # Main stair object
stair_runs = stair.GetStairRuns()  # Individual runs between landings
stair_landings = stair.GetStairLandings()  # Landing platforms
stair_supports = stair.GetStairSupports()  # Stringers, carriages
stair_railings = stair.GetStairRailings()  # Handrails, guardrails
```

#### **Stair Run Properties**
```python
run = stair_run
run.BaseElevation      # Starting elevation
run.TopElevation       # Ending elevation
run.ActualRunWidth     # Width of the run
run.ActualRiserHeight  # Individual riser height
run.ActualTreadDepth   # Individual tread depth
run.NumberOfRisers     # Count of risers
run.NumberOfTreads     # Count of treads
```

#### **Stair Landing Properties**
```python
landing = stair_landing
landing.BaseElevation  # Elevation of landing
landing.Width         # Landing width
landing.Length        # Landing length
landing.Shape         # Landing shape/geometry
```

### Plan View Creation Strategy

#### **Level-Based Stair Visibility**

**Algorithm for Stair Plan at Specific Level:**

```python
def calculate_stair_plan_visibility(stair, target_level_elevation):
    """
    Calculate what parts of stair are visible in plan at target level
    """
    visible_elements = {
        'runs_below': [],      # Runs going down from this level
        'runs_above': [],      # Runs going up from this level (partial)
        'landing_here': None,  # Landing at this level
        'direction_indicators': [],  # Up/down arrows, direction lines
        'safety_elements': []  # Handrails visible in plan
    }

    # Find landing at target level (note: landings are typically between levels)
    # In plan view convention, show landing if it's associated with this level
    for landing in stair.GetStairLandings():
        # Landing is considered "at this level" if it's the landing this level's floor connects to
        # This is a architectural convention, not physical reality
        if is_landing_associated_with_level(landing, target_level_elevation):
            visible_elements['landing_here'] = landing
            break

    # Find runs connected to this landing
    for run in stair.GetStairRuns():
        if run.TopElevation == target_level_elevation:
            # Run ends at this level (coming up to landing)
            visible_elements['runs_below'].append(run)
        elif run.BaseElevation == target_level_elevation:
            # Run starts at this level (going down from landing)
            visible_elements['runs_above'].append(run)

    return visible_elements
```

#### **Crop Region Calculation for Stairs**

**Simplified Rectangular Approach:**
Karena kompleksitas geometry tangga yang bervariasi (L-shape, U-shape, spiral), kita gunakan pendekatan simplified:
- Hitung bounding box persegi panjang dari seluruh stair element
- Gunakan panjang dan lebar maksimal dari stair footprint
- Tambahkan margin untuk clarity
- Abaikan bentuk kompleks dan gunakan rectangle sederhana

**Algorithm:**
```python
def calculate_stair_crop_region(stair, target_level_elevation):
    """
    Calculate rectangular crop region for stair plan view
    Simplified approach: rectangular bounding box regardless of stair shape
    """
    # Get stair's overall bounding box
    stair_bbox = stair.get_BoundingBox(None)

    if not stair_bbox:
        return None

    # Calculate dimensions at plan level
    width = abs(stair_bbox.Max.X - stair_bbox.Min.X)
    height = abs(stair_bbox.Max.Y - stair_bbox.Min.Y)

    # Create rectangular crop region centered on stair
    center_x = (stair_bbox.Max.X + stair_bbox.Min.X) / 2
    center_y = (stair_bbox.Max.Y + stair_bbox.Min.Y) / 2

    # Add margin (3 feet / ~1 meter on each side)
    margin = 3.0
    crop_min_x = center_x - (width / 2) - margin
    crop_max_x = center_x + (width / 2) + margin
    crop_min_y = center_y - (height / 2) - margin
    crop_max_y = center_y + (height / 2) + margin

    return {
        'min_x': crop_min_x,
        'max_x': crop_max_x,
        'min_y': crop_min_y,
        'max_y': crop_max_y
    }
```

## Implementation Planning

### Core Components Needed

#### **1. Stair Analyzer Module**
```python
class StairAnalyzer:
    def __init__(self, stair):
        self.stair = stair

    def get_stair_structure(self):
        """Analyze complete stair structure"""
        return {
            'runs': self.stair.GetStairRuns(),
            'landings': self.stair.GetStairLandings(),
            'supports': self.stair.GetStairSupports(),
            'railings': self.stair.GetStairRailings(),
            'min_elevation': min(run.BaseElevation for run in self.stair.GetStairRuns()),
            'max_elevation': max(run.TopElevation for run in self.stair.GetStairRuns())
        }

    def get_level_visibility(self, level_elevation):
        """Get stair elements visible at specific level"""
        # Implementation as above
        pass
```

#### **2. Stair Plan Generator Module**
```python
class StairPlanGenerator:
    def __init__(self, doc):
        self.doc = doc

    def create_stair_plan_at_level(self, stair, level, view_name, template=None):
        """Create plan view for stair at specific level"""
        # 1. Analyze stair visibility at level
        # 2. Calculate crop region
        # 3. Create plan view
        # 4. Set crop box
        # 5. Apply template if specified
        pass
```

#### **3. Level Stair Mapper**
```python
class LevelStairMapper:
    def __init__(self, stair, selected_levels):
        self.stair = stair
        self.selected_levels = selected_levels

    def map_stair_to_levels(self):
        """Map which levels should show which stair parts"""
        level_mappings = {}

        for level in self.selected_levels:
            visibility = self.calculate_visibility_at_level(level.Elevation)
            if visibility['has_visible_elements']:
                level_mappings[level] = visibility

        return level_mappings
```

### User Interface Flow

#### **Step 1: Stair Selection**
- User selects multi-story stair element
- Script validates it's a valid stair with multiple levels

#### **Step 2: Naming Input**
- User provides base name (e.g., "STAIRS-02")
- Script will append level info automatically

#### **Step 3: Level Selection**
- Show all levels where stair has elements
- Allow multi-selection of target levels
- Show preview of what will be visible at each level

#### **Step 4: Template Selection (Optional)**
- User selects view template for generated plans
- Option to use default template

#### **Step 5: Generation**
- Create plan views for each selected level
- Apply appropriate crop regions
- Generate unique names: "STAIRS-02_Level16", "STAIRS-02_Level17", etc.

### Technical Challenges & Solutions

#### **Challenge 1: Stair Geometry Complexity**
**Problem**: Stairs have complex 3D geometry, not simple 2D footprints
**Solution**:
- Use Revit's stair analysis API to get run and landing geometries
- Project 3D geometry to 2D plan view
- Calculate composite bounding box

#### **Challenge 2: Multi-Level Visibility**
**Problem**: Need to show stair elements across multiple levels in single plan
**Solution**:
- Analyze stair connectivity (which runs connect to which landings)
- Determine visibility rules per level
- Use level elevation to filter visible elements

#### **Challenge 3: Stair Direction Indication**
**Problem**: Plan views need to show stair direction clearly
**Solution**:
- Add direction arrows based on run Base/Top elevations
- Use stair run direction vectors
- Include directional annotations

#### **Challenge 4: Landing Representation**
**Problem**: Landings physically exist between levels, but plan views show them as if they're at the level
**Solution**:
- Use architectural convention: show landing in the plan view of the level it serves
- Determine landing association based on stair connectivity, not physical elevation
- Landing between L15-L16 appears in L16 plan view (the level you're arriving at)
- Handle this as visual convention, not physical accuracy requirement

## API Requirements Analysis

### Revit Stair API Usage

#### **Stair Analysis**
```python
# Get stair components
stair_runs = stair.GetStairRuns()
stair_landings = stair.GetStairLandings()
stair_railings = stair.GetStairRailings()

# Analyze run properties
for run in stair_runs:
    base_elev = run.BaseElevation
    top_elev = run.TopElevation
    direction = run.Direction  # Up/down direction
    width = run.ActualRunWidth
```

#### **Geometry Extraction**
```python
# Get run path geometry
run_curve = run.GetPathCurve()

# Get landing boundary
landing_boundary = landing.Shape

# Project to plan view
plan_geometry = project_to_plan_elevation(geometry, target_elevation)
```

### View Creation Strategy

#### **Plan View Creation**
```python
# Create plan view at level
plan_view = ViewPlan.Create(doc, level.Id, view_name)

# Set crop region based on stair geometry
crop_box = calculate_stair_crop_box(stair, level.Elevation)
plan_view.CropBox = crop_box

# Apply view template
if template:
    plan_view.ViewTemplateId = template.Id
```

## Success Criteria

### Functional Requirements
- ✅ Create plan views for stairs at selected levels
- ✅ Automatic crop region calculation
- ✅ Proper naming convention
- ✅ Template application support
- ✅ Multi-level stair support

### Quality Requirements
- ✅ Accurate geometry representation
- ✅ Clear stair direction indication
- ✅ Appropriate scale and visibility
- ✅ Professional output formatting

### Performance Requirements
- ✅ Fast processing for typical stairs
- ✅ Memory efficient for large models
- ✅ Error recovery for edge cases

## Implementation Roadmap

### Phase 1: Core Infrastructure
1. Stair analysis module
2. Basic plan view creation
3. Simple crop region (bounding box)

### Phase 2: Enhanced Geometry
1. Accurate stair geometry projection
2. Landing representation
3. Direction indication

### Phase 3: User Experience
1. Level selection UI
2. Template selection
3. Progress feedback

### Phase 4: Advanced Features
1. Multi-stair support
2. Custom naming schemes
3. Batch processing

## Risk Assessment

### Technical Risks
- **Complex Geometry**: Stair geometry projection may be complex
- **API Limitations**: Revit API may not expose all needed stair data
- **Performance**: Large stairs may impact processing speed

### Mitigation Strategies
- **Prototype First**: Create working prototype with simple geometry
- **API Research**: Thorough testing of Revit stair API capabilities
- **Fallback Options**: Provide simplified view if full geometry fails

## Success Metrics

### User Experience
- Time to create stair plans: < 30 seconds for typical stairs
- Success rate: > 95% for well-modeled stairs
- User satisfaction: Clear, usable plan views

### Technical Quality
- Geometry accuracy: ±1/16" for critical dimensions
- View naming: 100% unique, descriptive names
- Error handling: Graceful failure with clear messages

---

## Claude Implementation Prompt

**Please create a complete Stair Plan Generator script based on this specification. The script should:**

1. **Follow the same architecture as Wall Plan Generator** but adapted for stairs
2. **Use modular design** with separate analyzer, generator, and UI modules
3. **Handle stair-specific geometry** including runs, landings, and direction
4. **Create plan views at selected levels** with appropriate crop regions
5. **Include debug mode** and clean production output
6. **Provide comprehensive error handling** and user feedback
7. **Generate proper naming** like "STAIRS-02_Level16", "STAIRS-02_Level17"
8. **Support view templates** and custom crop regions

**Key differences from Wall Plan Generator:**
- Element type: Stairs instead of walls
- Geometry analysis: Stair runs and landings instead of wall curves
- Visibility logic: Multi-level stair connectivity
- Crop region: Complex stair footprint instead of rectangular wall
- Direction indication: Up/down stair direction arrows

**Deliverables:**
- Complete script files (main script + modules)
- Comprehensive documentation
- Usage examples and troubleshooting guide