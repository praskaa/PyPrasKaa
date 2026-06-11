# -*- coding: utf-8 -*-

__doc__ = u'''Version: 1.5
Date    = 04.03.2026
_____________________________________________________________________
Description:
Creates dimension lines between selected grid lines in a single row.
The tool uses box selection to pick multiple grids and automatically creates
a chain dimension with proper reference ordering.

Supports both vertical grids (X-spacing) and horizontal grids (Y-spacing)
in plan views and elevation/section views.
_____________________________________________________________________
How-to:
1. Open a Plan View, Elevation, or Section in Revit
2. Click the Dimension Grids button
3. Box-select a row of grid lines
4. Pick a point to place the dimension line (above or below grids)
5. Dimension chain is automatically created

Tips:
- Works with vertical grids (dimensioning X-spacing)
- Works with horizontal grids (dimensioning Y-spacing)
- Curved grids are automatically skipped
- Duplicate grid positions are handled gracefully
_____________________________________________________
Last update:
- 04.03.2026 - 1.5 Enhanced dimension line computation
- Fixed horizontal grid dimension showing "0" - now uses horizontal
  dimension line instead of vertical for proper Y-spacing
- Added proper dimension line orientation (perpendicular to grids)
- 15.02.2026 - 1.4 Grid sorting by position
- Added orientation detection for vertical/horizontal grids
- Fixed Revit 2024-2026 compatibility
- 10.02.2026 - 1.3 Fixed reference acquisition
- Now uses get_Geometry() with ComputeReferences=True
- Fixed dimension line span from actual grid coordinates
- 05.02.2026 - 1.2 Added duplicate coordinate detection
- Skips grids at same position to prevent zero-length segments
- 01.02.2026 - 1.1 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
'''

__title__ = 'Dimension\nGrids'

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from pyrevit import revit, DB, forms
from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import (
    Options, Line, ReferenceArray, Reference,
    XYZ, Plane, SketchPlane, Transaction, TransactionGroup
)
from Snippets._selection import ISelectionFilter_Categories

doc  = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = revit.active_view

# -----------------------------------------
#  REVIT API COMPATIBILITY (2024-2026)
# -----------------------------------------

def get_element_id_value(element_id):
    """Returns integer value of ElementId.

    Revit 2024+ uses .Value (long); older versions use .IntegerValue.
    """
    try:
        return element_id.Value          # Revit 2024+
    except AttributeError:
        return element_id.IntegerValue   # Revit 2023 and earlier


# -----------------------------------------
#  UNIT HELPERS
# -----------------------------------------

def mm_to_ft(mm):
    return mm / 304.8

def ft_to_mm(ft):
    return ft * 304.8


# -----------------------------------------
#  VIEW TYPE DETECTION
# -----------------------------------------

view_family_name = doc.GetElement(active_view.GetTypeId()).FamilyName
is_plan = view_family_name in ['Floor Plan', 'Ceiling Plan', 'Area Plan', 'Site Plan']


# -----------------------------------------
#  GRID REFERENCE ACQUISITION
# -----------------------------------------

def get_grid_ref(grid, view):
    """Returns a valid geometry Reference from a Grid element.

    IMPORTANT: UniqueId is NOT a valid stable representation for dimensioning.
    We must extract the Reference from the actual geometry Line inside the Grid,
    obtained via get_Geometry() with ComputeReferences=True.

    This reference is associative — if the grid moves, the dimension updates.

    Args:
        grid: Revit Grid element
        view: active view (needed for geometry options)

    Returns:
        Reference object, or None if not found
    """
    try:
        opt = Options()
        opt.ComputeReferences = True        # mandatory for dimensioning
        opt.IncludeNonVisibleObjects = True
        opt.View = view

        geo = grid.get_Geometry(opt)
        if not geo:
            return None

        for item in geo:
            # The grid's geometry is a Line — grab its Reference directly
            if isinstance(item, Line) and item.Reference:
                return item.Reference

        # Fallback: try grid.Curve.Reference
        crv = grid.Curve
        if crv and crv.Reference:
            return crv.Reference

    except Exception:
        pass

    return None


# -----------------------------------------
#  GRID ORIENTATION & SORTING
# -----------------------------------------

def get_grid_orientation(grid):
    """Returns 'vertical', 'horizontal', or 'other'.

    Vertical grid  → runs along Y → dimensioned along X axis
    Horizontal grid → runs along X → dimensioned along Y axis
    """
    crv = grid.Curve
    p0  = crv.GetEndPoint(0)
    p1  = crv.GetEndPoint(1)
    dx  = abs(p1.X - p0.X)
    dy  = abs(p1.Y - p0.Y)

    if dy > dx:
        return "vertical"    # line goes up/down → X spacing matters
    elif dx > dy:
        return "horizontal"  # line goes left/right → Y spacing matters
    else:
        return "other"


def sort_grids(grids):
    """Sorts grids by position so ReferenceArray order matches spatial order.

    Vertical grids   → sort by X coordinate (left to right)
    Horizontal grids → sort by Y coordinate (bottom to top)
    Mixed orientations → sort by X as fallback

    Correct ordering ensures dimension segments read naturally
    and prevents Revit from producing crossed/scrambled chains.
    """
    if not grids:
        return grids

    orientation = get_grid_orientation(grids[0])

    if orientation == "vertical":
        return sorted(grids, key=lambda g: (
            g.Curve.GetEndPoint(0).X + g.Curve.GetEndPoint(1).X) / 2.0)
    elif orientation == "horizontal":
        return sorted(grids, key=lambda g: (
            g.Curve.GetEndPoint(0).Y + g.Curve.GetEndPoint(1).Y) / 2.0)
    else:
        return sorted(grids, key=lambda g: (
            g.Curve.GetEndPoint(0).X + g.Curve.GetEndPoint(1).X) / 2.0)


# -----------------------------------------
#  DIMENSION LINE COMPUTATION
# -----------------------------------------

def compute_dimension_line(grids, orientation, pick_point, is_plan):
    """Computes the start and end points of the dimension line.

    CRITICAL RULE: The dimension line must INTERSECT (cross) every grid
    reference — not run parallel to them. Parallel lines never intersect,
    so Revit cannot attach references and produces value=None.

    Vertical grids   (run along Y, spaced in X):
        → dimension line must be HORIZONTAL (along X) → crosses all vertical grids
        → placed at Y = safe offset from grid extents

    Horizontal grids (run along X, spaced in Y):
        → dimension line must be VERTICAL (along Y) → crosses all horizontal grids
        → placed at X = safe offset from grid extents

    pick_point is used ONLY to determine which side (left/right or above/below).
    It is never used directly as a coordinate because Revit snaps pick points
    to nearby grids, which would place the line on top of a reference → value=None.

    Args:
        grids:       sorted list of Grid elements
        orientation: 'vertical' or 'horizontal'
        pick_point:  XYZ point picked by user (side detection only)
        is_plan:     bool, True if plan view

    Returns:
        (Line, perp_direction XYZ) tuple
    """
    padding = 1.0  # extend line 1 foot beyond outer grids on each side
    offset  = mm_to_ft(800)  # clearance from outermost grid

    if not is_plan:
        xs = [(g.Curve.GetEndPoint(0).X + g.Curve.GetEndPoint(1).X) / 2.0
              for g in grids]
        lo, hi = min(xs), max(xs)
        p0 = XYZ(lo - padding, pick_point.Y, pick_point.Z)
        p1 = XYZ(hi + padding, pick_point.Y, pick_point.Z)
        return Line.CreateBound(p0, p1), XYZ.BasisY

    # Collect full extents of all grids
    all_x, all_y = [], []
    for g in grids:
        all_x += [g.Curve.GetEndPoint(0).X, g.Curve.GetEndPoint(1).X]
        all_y += [g.Curve.GetEndPoint(0).Y, g.Curve.GetEndPoint(1).Y]
    x_lo, x_hi = min(all_x), max(all_x)
    y_lo, y_hi = min(all_y), max(all_y)

    if orientation == "vertical":
        # Vertical grids run along Y, spaced in X
        # Dimension line must be HORIZONTAL (along X) to CROSS/INTERSECT them
        # Safe Y: outside grid body extent so line never sits on a reference
        y_mid = (y_lo + y_hi) / 2.0
        dim_y = (y_hi + offset) if pick_point.Y >= y_mid else (y_lo - offset)
        p0 = XYZ(x_lo - padding, dim_y, 0)
        p1 = XYZ(x_hi + padding, dim_y, 0)
        return Line.CreateBound(p0, p1), XYZ.BasisY

    else:
        # Horizontal grids run along X, spaced in Y
        # Dimension line must be VERTICAL (along Y) to CROSS/INTERSECT them
        # Safe X: outside grid body extent so line never sits on a reference
        x_mid = (x_lo + x_hi) / 2.0
        dim_x = (x_hi + offset) if pick_point.X >= x_mid else (x_lo - offset)
        p0 = XYZ(dim_x, y_lo - padding, 0)
        p1 = XYZ(dim_x, y_hi + padding, 0)
        return Line.CreateBound(p0, p1), XYZ.BasisX


# -----------------------------------------
#  MAIN FLOW
# -----------------------------------------

# 1. Select grids via rectangle selection
try:
    with forms.WarningBar(title="Box-select a row of grid lines, then press Enter"):
        grids_raw = uidoc.Selection.PickElementsByRectangle(
            ISelectionFilter_Categories([DB.BuiltInCategory.OST_Grids]),
            "Select Grids"
        )
except Exceptions.OperationCanceledException:
    forms.alert("Cancelled.", ok=True, exitscript=True)
except Exception as e:
    forms.alert("Selection error: {}".format(str(e)), ok=True, exitscript=True)

if not grids_raw:
    forms.alert("No grids selected.", ok=True, exitscript=True)

# 2. Filter out curved grids (can't be dimensioned with a straight line)
grids_linear = [g for g in grids_raw if not g.IsCurved]
if not grids_linear:
    forms.alert("No valid (non-curved) grids found.", ok=True, exitscript=True)

# 3. Sort grids spatially so ReferenceArray order = spatial order
grids_sorted = sort_grids(grids_linear)
orientation  = get_grid_orientation(grids_sorted[0])

# 4. Build ReferenceArray using geometry-based references
#    (NOT UniqueId — that is not a valid stable representation for dimensions)
#
#    IMPORTANT: Deduplicate by coordinate before building ReferenceArray.
#    If two grids share the same coordinate (e.g. grid 19 and 21 both at Y=42),
#    Revit creates a zero-length segment which corrupts the entire dimension —
#    all segments become blank/None even if the rest are valid.

def _grid_sort_coord(g, orient):
    crv = g.Curve
    if orient == "vertical":
        return round((crv.GetEndPoint(0).X + crv.GetEndPoint(1).X) / 2.0, 6)
    else:
        return round((crv.GetEndPoint(0).Y + crv.GetEndPoint(1).Y) / 2.0, 6)

ref_array   = ReferenceArray()
skipped     = []
duplicates  = []
seen_coords = set()

for gr in grids_sorted:
    coord = _grid_sort_coord(gr, orientation)
    if coord in seen_coords:
        duplicates.append(gr.Name)
        continue
    seen_coords.add(coord)

    ref = get_grid_ref(gr, active_view)
    if ref:
        ref_array.Append(ref)
    else:
        skipped.append(gr.Name)

if duplicates:
    forms.alert(
        "Warning: {} grid(s) skipped — duplicate position (same coordinate "
        "as another grid): {}\n\nDimension will be created without them.".format(
            len(duplicates), ", ".join(duplicates)),
        ok=True
    )

if ref_array.Size < 2:
    forms.alert(
        "Need at least 2 valid grid references to create a dimension.\n"
        "Skipped (no ref): {}\nSkipped (duplicate): {}".format(
            ", ".join(skipped) if skipped else "none",
            ", ".join(duplicates) if duplicates else "none"),
        ok=True, exitscript=True
    )

if skipped:
    forms.alert(
        "Warning: {} grid(s) skipped (no valid reference): {}".format(
            len(skipped), ", ".join(skipped)),
        ok=True
    )

# 5. For elevation/section: set sketch plane so dimension can be placed
if not is_plan:
    with revit.Transaction("Dim Grids - Set Sketch Plane", doc=doc):
        origin         = active_view.Origin
        view_direction = active_view.ViewDirection
        plane          = Plane.CreateByNormalAndOrigin(view_direction, origin)
        sp             = SketchPlane.Create(doc, plane)
        active_view.SketchPlane = sp
        doc.Regenerate()

# 6. User picks placement point (where the dimension line will sit)
pick_point = None
try:
    pick_point = uidoc.Selection.PickPoint(
        "Pick a point to place the dimension line"
    )
except Exceptions.OperationCanceledException:
    forms.alert("Cancelled.", ok=True, exitscript=True)
except Exception as e:
    forms.alert("Pick point error: {}".format(str(e)), ok=True, exitscript=True)

if pick_point is None:
    forms.alert("No point selected.", ok=True, exitscript=True)

# 7. Compute dimension line spanning all grids at the picked position
dim_line, _ = compute_dimension_line(
    grids_sorted, orientation, pick_point, is_plan
)

# 8. Create dimension
#    Mirrors the transaction pattern from AutoDimensionColumn:
#    - Outer TransactionGroup wraps everything
#    - Inner Transaction 1: regenerate model so all geometry references
#      are fully resolved before dimensioning
#    - Inner Transaction 2: create the actual dimension
#
#    Without the Regenerate() step, Revit may have stale geometry data
#    from the ComputeReferences pass, causing NewDimension() to succeed
#    structurally but fail to resolve segment values (shows blank/None).

dim = None
tg = TransactionGroup(doc, "Dimension Grids")
tg.Start()

try:
    # Transaction 1: force geometry regeneration
    t1 = Transaction(doc, "Regenerate")
    t1.Start()
    doc.Regenerate()
    t1.Commit()

    # Transaction 2: create dimension
    t2 = Transaction(doc, "Create Dimension")
    t2.Start()
    dim = doc.Create.NewDimension(active_view, dim_line, ref_array)
    t2.Commit()

    tg.Assimilate()

except Exception as e:
    tg.RollBack()
    forms.alert("Error creating dimension:\n{}".format(str(e)), ok=True, exitscript=True)

if dim:
    print("✅ Dimension created with {} segments across {} grids.".format(
        ref_array.Size - 1, ref_array.Size))
else:
    forms.alert(
        "Dimension was not created. This may happen if the line does not "
        "intersect all grid references.",
        ok=True
    )