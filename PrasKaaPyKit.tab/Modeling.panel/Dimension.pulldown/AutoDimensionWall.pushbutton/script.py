
# -*- coding: utf-8 -*-
"""
Auto Dimensioning Walls - Automatic Wall Dimensioning Script
Automatically creates dimensions for selected walls with minimal errors
"""

import clr
import sys
import math
import json
import os
from collections import defaultdict

# Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

# pyRevit
from pyrevit import revit, forms, script

# Transaction for pyRevit
from Autodesk.Revit.DB import Transaction

# Windows Forms for modifier keys and advanced dialogs
import System.Windows.Forms as WinForms
from System.Windows.Forms import (
    Form, Button, Label, ListView, View, ColumnHeader,
    ListViewItem, ColumnHeaderStyle, HorizontalAlignment,
    FormBorderStyle, DockStyle, AnchorStyles, FormStartPosition,
    TextBox, DialogResult
)
from System.Drawing import Point, Size, Font, FontStyle, Color

# Import wall level filtering logic
import sys
# Import wall orientation logic from lib

# Fallback implementation if wall_level_filtering is not available
class FallbackWallLevelFilter:
    """Fallback implementation for wall level filtering"""

    def __init__(self, doc):
        self.doc = doc

    def should_tag_wall_in_view(self, wall, view_level):
        """Simple fallback: always return True"""
        return True

    def get_view_level(self, view):
        """Get view level"""
        try:
            return view.GenLevel
        except:
            return None

# Try to import, use fallback if not available
try:
    from wall_level_filtering import WallLevelFilter
except ImportError:
    WallLevelFilter = FallbackWallLevelFilter

try:
    from wall_orientation_logic import WallOrientationHandler
except ImportError:
    # Fallback for WallOrientationHandler
    class FallbackWallOrientationHandler:
        def __init__(self, doc):
            self.doc = doc

        def get_wall_orientation(self, wall):
            """Fallback: return wall.Orientation directly"""
            try:
                return wall.Orientation
            except:
                return None

    WallOrientationHandler = FallbackWallOrientationHandler

# ============================================================================
# SELECTION FILTER
# ============================================================================
class WallSelectionFilter(ISelectionFilter):
    """Selection filter to allow only walls during selection"""

    def AllowElement(self, elem):
        """Allow only Walls during selection"""
        try:
            # Primary check: category name (most reliable)
            if hasattr(elem, "Category") and elem.Category:
                cat_name = elem.Category.Name.lower()
                if 'wall' in cat_name or 'dinding' in cat_name:
                    return True

            # Secondary check: built-in category ID
            if hasattr(elem, "Category") and elem.Category:
                cat_id = elem.Category.Id.Value
                if cat_id == int(BuiltInCategory.OST_Walls):
                    return True

            # Tertiary check: element type
            if isinstance(elem, Wall):
                return True

            # Debug: print what we're rejecting (only for debugging)
            # Uncomment if needed: print("Rejected: {}".format(elem.Category.Name if hasattr(elem, "Category") and elem.Category else "No Category"))

        except Exception as e:
            # Silent fail for selection filter
            pass
        return False

    def AllowReference(self, refer, point):
        return False


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Centralized configuration"""
    VERBOSE_OUTPUT = False  # Set to True for detailed debugging output
    DEFAULT_OFFSET_MM = 10
    DEFAULT_TEXT_OFFSET_MM = 30  # Offset untuk reposition text dimension
    DEFAULT_LENGTH_DIM_TYPE_NAME = "Arrow - 2.5mm Swis721 BT - Dimensi Dinding"
    DEFAULT_WIDTH_DIM_TYPE_NAME = "Arrow - 2.5mm Swis721 BT - Dimensi Dinding"
    DIM_LINE_LENGTH = 10  # feet

    # Wall categories
    WALL_CATEGORIES = [
        BuiltInCategory.OST_Walls
    ]


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================
class ConfigurationManager:
    """Manages configuration persistence for pyRevit scripts"""

    def __init__(self, script_dir=None, config_filename="config.json"):
        self.script_dir = script_dir or os.path.dirname(__file__)
        self.config_filename = config_filename
        self.config_path = os.path.join(self.script_dir, config_filename)
        self.config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default configuration
                self.config = self._get_default_config()
                self._save_config()
        except Exception as e:
            print("Warning: Could not load config file: {}".format(str(e)))
            # Use defaults if loading fails
            self.config = self._get_default_config()

    def _save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print("Error: Could not save config file: {}".format(str(e)))
            WinForms.MessageBox.Show(
                "Could not save configuration: {}".format(str(e)),
                "Configuration Error",
                WinForms.MessageBoxButtons.OK,
                WinForms.MessageBoxIcon.Warning
            )

    def _get_default_config(self):
        """Get default configuration values"""
        return {
            'offset_mm': Config.DEFAULT_OFFSET_MM,
            'text_offset_mm': Config.DEFAULT_TEXT_OFFSET_MM,
            'length_dimension_type_name': Config.DEFAULT_LENGTH_DIM_TYPE_NAME,
            'width_dimension_type_name': Config.DEFAULT_WIDTH_DIM_TYPE_NAME,
            'dimension_both': True,
            'verbose_output': False
        }

    def get_value(self, key, default=None):
        """Get configuration value with optional default"""
        return self.config.get(key, default)

    def set_value(self, key, value):
        """Set configuration value and save"""
        self.config[key] = value
        self._save_config()

    def get_offset_mm(self):
        """Get saved offset in millimeters"""
        return self.get_value('offset_mm', Config.DEFAULT_OFFSET_MM)

    def set_offset_mm(self, offset_mm):
        """Set offset in millimeters"""
        self.set_value('offset_mm', offset_mm)

    def get_length_dimension_type_name(self):
        """Get saved length dimension type name"""
        return self.get_value('length_dimension_type_name', Config.DEFAULT_LENGTH_DIM_TYPE_NAME)

    def set_length_dimension_type_name(self, name):
        """Set length dimension type name"""
        self.set_value('length_dimension_type_name', name)

    def get_width_dimension_type_name(self):
        """Get saved width dimension type name"""
        return self.get_value('width_dimension_type_name', Config.DEFAULT_WIDTH_DIM_TYPE_NAME)

    def set_width_dimension_type_name(self, name):
        """Set width dimension type name"""
        self.set_value('width_dimension_type_name', name)

    def get_dimension_both(self):
        """Get whether to dimension both length and width"""
        return self.get_value('dimension_both', True)

    def set_dimension_both(self, value):
        """Set whether to dimension both length and width"""
        self.set_value('dimension_both', value)

    def get_verbose_output(self):
        """Get verbose output setting"""
        return self.get_value('verbose_output', False)

    def set_verbose_output(self, value):
        """Set verbose output setting"""
        self.set_value('verbose_output', value)

    def get_text_offset_mm(self):
        """Get saved text offset in millimeters"""
        return self.get_value('text_offset_mm', Config.DEFAULT_TEXT_OFFSET_MM)

    def set_text_offset_mm(self, offset_mm):
        """Set text offset in millimeters"""
        self.set_value('text_offset_mm', offset_mm)

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._get_default_config()
        self._save_config()


# ============================================================================
# ADVANCED MULTI-SELECT DIALOG
# ============================================================================
class AdvancedMultiSelectDialog(Form):
    """Advanced multi-selection dialog dengan keyboard shortcuts dan search"""

    def __init__(self, items, title="Select Items", item_display_func=None, preselected_items=None):
        """
        Parameters:
        - items: List of objects
        - title: Dialog title
        - item_display_func: Function to get display name from item (optional)
        - preselected_items: List of items that should be pre-selected (optional)
        """
        self.items = items
        self.selected_items = []
        self.filtered_items = items[:]
        self.item_display_func = item_display_func or (lambda x: str(x))
        self.preselected_items = preselected_items or []

        self.InitializeComponent()
        self.Text = title

    def InitializeComponent(self):
        """Setup UI components"""
        self.Size = Size(500, 600)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        # Search section
        self.setup_search_section()

        # ListView section
        self.setup_list_view()

        # Buttons section
        self.setup_buttons()

    def setup_search_section(self):
        """Setup search functionality"""
        y_pos = 20

        # Search label
        search_label = Label()
        search_label.Text = "Search:"
        search_label.Location = Point(20, y_pos)
        search_label.Size = Size(50, 20)
        self.Controls.Add(search_label)

        # Search textbox
        self.search_box = TextBox()
        self.search_box.Location = Point(80, y_pos)
        self.search_box.Size = Size(300, 20)
        self.search_box.TextChanged += self.on_search_text_changed
        self.Controls.Add(self.search_box)

        # Clear button
        clear_btn = Button()
        clear_btn.Text = "Clear"
        clear_btn.Location = Point(390, y_pos)
        clear_btn.Size = Size(50, 25)
        clear_btn.Click += self.on_clear_search
        self.Controls.Add(clear_btn)

        # Search tip
        y_pos += 25
        search_tip = Label()
        search_tip.Text = "Tip: Type to filter, Shift+Click for range, Ctrl+Click for individual"
        search_tip.Location = Point(20, y_pos)
        search_tip.Size = Size(450, 15)
        search_tip.Font = Font("Segoe UI", 8, FontStyle.Italic)
        search_tip.ForeColor = Color.Gray
        self.Controls.Add(search_tip)

    def setup_list_view(self):
        """Setup ListView dengan advanced multi-select"""
        y_pos = 70

        self.list_view = ListView()
        self.list_view.Location = Point(20, y_pos)
        self.list_view.Size = Size(460, 400)
        self.list_view.View = View.Details
        self.list_view.CheckBoxes = True
        self.list_view.MultiSelect = True  # Enables Shift+Click and Ctrl+Click
        self.list_view.FullRowSelect = True
        self.list_view.GridLines = False

        # Hide headers for clean appearance
        self.list_view.HeaderStyle = ColumnHeaderStyle.Nonclickable
        self.list_view.Columns.Add("", 440, HorizontalAlignment.Left)

        # Populate items
        self.populate_list_view()

        self.Controls.Add(self.list_view)

    def setup_buttons(self):
        """Setup control buttons"""
        y_pos = 480

        # Select All button
        select_all_btn = Button()
        select_all_btn.Text = "Select All"
        select_all_btn.Location = Point(20, y_pos)
        select_all_btn.Size = Size(100, 30)
        select_all_btn.Click += self.on_select_all
        self.Controls.Add(select_all_btn)

        # Deselect All button
        deselect_all_btn = Button()
        deselect_all_btn.Text = "Deselect All"
        deselect_all_btn.Location = Point(130, y_pos)
        deselect_all_btn.Size = Size(100, 30)
        deselect_all_btn.Click += self.on_deselect_all
        self.Controls.Add(deselect_all_btn)

        # OK button
        ok_btn = Button()
        ok_btn.Text = "OK"
        ok_btn.Location = Point(300, y_pos)
        ok_btn.Size = Size(80, 30)
        ok_btn.Click += self.on_ok_click
        self.Controls.Add(ok_btn)

        # Cancel button
        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(390, y_pos)
        cancel_btn.Size = Size(80, 30)
        cancel_btn.Click += self.on_cancel_click
        self.Controls.Add(cancel_btn)

    def populate_list_view(self, items=None):
        """Populate ListView dengan items"""
        if items is None:
            items = self.filtered_items

        self.list_view.Items.Clear()

        for item in items:
            display_name = self.item_display_func(item)
            list_item = ListViewItem(display_name)
            list_item.Tag = item  # Store original object

            # Pre-select items that were previously selected
            if item in self.preselected_items:
                list_item.Checked = True

            self.list_view.Items.Add(list_item)

    # Event Handlers
    def on_search_text_changed(self, sender, args):
        """Filter items berdasarkan search text"""
        search_text = self.search_box.Text.lower().strip()

        if not search_text:
            self.filtered_items = self.items[:]
            self.populate_list_view()
        else:
            self.filtered_items = []
            for item in self.items:
                display_name = self.item_display_func(item).lower()
                if search_text in display_name:
                    self.filtered_items.append(item)
            self.populate_list_view()

    def on_clear_search(self, sender, args):
        """Clear search"""
        self.search_box.Text = ""

    def on_select_all(self, sender, args):
        """Select all visible items"""
        for item in self.list_view.Items:
            item.Checked = True

    def on_deselect_all(self, sender, args):
        """Deselect all visible items"""
        for item in self.list_view.Items:
            item.Checked = False

    def on_ok_click(self, sender, args):
        """Process selection dan close"""
        self.selected_items = []
        for item in self.list_view.CheckedItems:
            original_item = item.Tag
            self.selected_items.append(original_item)

        if not self.selected_items:
            WinForms.MessageBox.Show(
                "Please select at least one item.",
                "No Selection",
                WinForms.MessageBoxButtons.OK,
                WinForms.MessageBoxIcon.Warning
            )
            return

        self.DialogResult = DialogResult.OK
        self.Close()

    def on_cancel_click(self, sender, args):
        """Cancel selection"""
        self.DialogResult = DialogResult.Cancel
        self.Close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_view_display_name(view):
    """Custom display function untuk views"""
    level_name = view.GenLevel.Name if view.GenLevel else "No Level"
    return "{} ({})".format(view.Name, level_name)


class Utils:
    """Utility functions for common operations"""

    @staticmethod
    def mm_to_feet(mm):
        """Convert millimeters to feet"""
        return mm / 304.8

    @staticmethod
    def get_view_scale_factor(view):
        """Get scale factor safely"""
        try:
            scale = view.Scale
            if scale <= 0:
                forms.alert("Warning: View scale is invalid. Using scale 1:100")
                return 100
            return scale
        except:
            return 100

    @staticmethod
    def safe_get_parameter(element, param_name):
        """Safely get parameter value"""
        try:
            param = element.LookupParameter(param_name)
            if param and param.HasValue:
                if param.StorageType == StorageType.String:
                    return param.AsString()
                elif param.StorageType == StorageType.Double:
                    return param.AsDouble()
                elif param.StorageType == StorageType.Integer:
                    return param.AsInteger()
                elif param.StorageType == StorageType.ElementId:
                    return param.AsElementId()
        except:
            pass
        return None

    @staticmethod
    def is_wall(element):
        """Check if element is a wall"""
        if element is None:
            return False

        try:
            # Check category
            if hasattr(element, 'Category') and element.Category:
                cat_id = element.Category.Id.Value
                if cat_id in [int(cat) for cat in Config.WALL_CATEGORIES]:
                    return True

                cat_name = element.Category.Name
                if any(keyword in cat_name for keyword in ['Wall', 'Dinding', 'wall']):
                    return True

            # Check element type
            if isinstance(element, Wall):
                return True
        except:
            pass

        return False

    @staticmethod
    def should_dimension_wall(wall, view, doc):
        """
        Check if wall continues above current level
        Returns True if wall should be dimensioned (continues upward)
        """
        try:
            # Use wall level filtering logic
            filter = WallLevelFilter(doc)
            view_level = filter.get_view_level(view)
            return filter.should_tag_wall_in_view(wall, view_level)
        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error checking wall level: {}".format(e))
            return True  # Default: include if error


# ============================================================================
# WALL REFERENCE HANDLER
# ============================================================================
class WallReferenceHandler:
    """Handle getting references from walls"""

    def __init__(self, doc, view):
        self.doc = doc
        self.view = view

    def get_wall_references(self, wall):
        """
        Get all references (length_start, length_end, width_exterior, width_interior) from wall
        Returns: dict with references or None if failed
        """
        refs = {}

        if Config.VERBOSE_OUTPUT:
            print("Getting wall references for wall ID: {}".format(wall.Id))

        # Method 1: Try edge references (LocationCurve endpoints)
        if Config.VERBOSE_OUTPUT:
            print("Trying method 1: edge references")
        refs = self._get_length_references(wall)
        if Config.VERBOSE_OUTPUT:
            print("Length references: {}".format(refs))
        if self._validate_length_references(refs):
            # Method 2: Try face references for width
            if Config.VERBOSE_OUTPUT:
                print("Length references valid, getting width references")
            width_refs = self._get_width_references(wall)
            if Config.VERBOSE_OUTPUT:
                print("Width references: {}".format(width_refs))
            if width_refs:
                refs.update(width_refs)
            return refs

        # Method 2: Try geometry references (using local orientation)
        if Config.VERBOSE_OUTPUT:
            print("Trying method 2: geometry references")
        refs = self._get_geometry_references(wall)
        if Config.VERBOSE_OUTPUT:
            print("Geometry references: {}".format(refs))
        if self._validate_references(refs):
            return refs

        # Method 3: Try faces (using local orientation)
        if Config.VERBOSE_OUTPUT:
            print("Trying method 3: face references")
        refs = self._get_face_references(wall)
        if Config.VERBOSE_OUTPUT:
            print("Face references: {}".format(refs))
        if self._validate_references(refs):
            return refs

        if Config.VERBOSE_OUTPUT:
            print("All reference methods failed - no references found")
        return None

    def _get_length_references(self, wall):
        """Get references from wall LocationCurve endpoints"""
        refs = {}

        try:
            location = wall.Location
            if not isinstance(location, LocationCurve):
                return refs

            curve = location.Curve

            # Handle different curve types (Line, Arc, PolyLine for L-shaped walls)
            if isinstance(curve, Line):
                # Simple straight wall
                start_point = curve.GetEndPoint(0)
                end_point = curve.GetEndPoint(1)

                # Get geometry options
                geo_options = Options()
                geo_options.ComputeReferences = True
                geo_options.View = self.view
                geo_options.IncludeNonVisibleObjects = False

                # Get wall geometry
                geo_element = wall.get_Geometry(geo_options)
                if not geo_element:
                    return refs

                for geo_obj in geo_element:
                    solid = None

                    if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                        solid = geo_obj
                    elif isinstance(geo_obj, GeometryInstance):
                        inst_geo = geo_obj.GetInstanceGeometry()
                        for inst_obj in inst_geo:
                            if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                                solid = inst_obj
                                break

                    if solid:
                        for edge in solid.Edges:
                            if edge.Reference:
                                # Check if edge is near start or end point
                                edge_curve = edge.AsCurve()
                                if edge_curve:
                                    # Check distance to start point
                                    dist_to_start = edge_curve.Distance(start_point)
                                    dist_to_end = edge_curve.Distance(end_point)

                                    if dist_to_start < 0.01:  # Within 1cm
                                        refs['length_start'] = edge.Reference
                                    elif dist_to_end < 0.01:  # Within 1cm
                                        refs['length_end'] = edge.Reference

            elif hasattr(curve, 'GetEndPoint') and hasattr(curve, 'Length'):
                # Handle other curve types (Arc, etc.)
                start_point = curve.GetEndPoint(0)
                end_point = curve.GetEndPoint(1)

                # Get geometry options
                geo_options = Options()
                geo_options.ComputeReferences = True
                geo_options.View = self.view
                geo_options.IncludeNonVisibleObjects = False
    
                # Get wall geometry
                geo_element = wall.get_Geometry(geo_options)
                if not geo_element:
                    return refs

                for geo_obj in geo_element:
                    solid = None

                    if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                        solid = geo_obj
                    elif isinstance(geo_obj, GeometryInstance):
                        inst_geo = geo_obj.GetInstanceGeometry()
                        for inst_obj in inst_geo:
                            if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                                solid = inst_obj
                                break

                    if solid:
                        for edge in solid.Edges:
                            if edge.Reference:
                                # Check if edge is near start or end point
                                edge_curve = edge.AsCurve()
                                if edge_curve:
                                    # Check distance to start point
                                    dist_to_start = edge_curve.Distance(start_point)
                                    dist_to_end = edge_curve.Distance(end_point)

                                    if dist_to_start < 0.01:  # Within 1cm
                                        refs['length_start'] = edge.Reference
                                    elif dist_to_end < 0.01:  # Within 1cm
                                        refs['length_end'] = edge.Reference

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting length references: {}".format(e))

        return refs

    def _get_width_references(self, wall):
        """Get width references from wall faces using Wall.Orientation"""
        refs = {}

        try:
            # Get wall orientation
            orientation = wall.Orientation
            if not orientation:
                return refs

            # Get geometry options
            geo_options = Options()
            geo_options.ComputeReferences = True
            geo_options.View = self.view
            geo_options.IncludeNonVisibleObjects = False

            geo_element = wall.get_Geometry(geo_options)
            if not geo_element:
                return refs

            faces_data = []

            for geo_obj in geo_element:
                solid = None

                if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                    solid = geo_obj
                elif isinstance(geo_obj, GeometryInstance):
                    inst_geo = geo_obj.GetInstanceGeometry()
                    for inst_obj in inst_geo:
                        if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                            solid = inst_obj
                            break

                if solid:
                    for face in solid.Faces:
                        if isinstance(face, PlanarFace) and face.Reference:
                            normal = face.FaceNormal
                            # Only vertical faces (perpendicular to Z)
                            if abs(normal.Z) < 0.1:
                                faces_data.append({
                                    'reference': face.Reference,
                                    'normal': normal,
                                    'center': face.Origin
                                })

            if len(faces_data) < 2:
                return refs

            # Identify exterior vs interior using Wall.Orientation
            # Exterior face normal should align with Wall.Orientation
            exterior_faces = []
            interior_faces = []

            for face_data in faces_data:
                normal = face_data['normal']
                # Dot product with orientation
                dot_product = normal.DotProduct(orientation)

                if dot_product > 0.9:  # Facing same direction as orientation
                    exterior_faces.append(face_data)
                elif dot_product < -0.9:  # Facing opposite direction
                    interior_faces.append(face_data)

            # Get the closest faces to center (most representative)
            if exterior_faces:
                refs['width_exterior'] = exterior_faces[0]['reference']
            if interior_faces:
                refs['width_interior'] = interior_faces[0]['reference']

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting width references: {}".format(e))

        return refs

    def _get_geometry_references(self, wall):
        """Get references from geometry edges - finds opposing faces using LOCAL column orientation"""
        refs = {}

        try:
            # Get wall orientation and location
            orientation = wall.Orientation
            location = wall.Location

            if not isinstance(location, LocationCurve):
                return refs

            curve = location.Curve
            center = curve.Evaluate(0.5, True)

            # Create local coordinate system
            direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
            x_axis = direction
            y_axis = XYZ.BasisZ.CrossProduct(x_axis).Normalize()

            geo_options = Options()
            geo_options.ComputeReferences = True
            geo_options.View = self.view
            geo_options.IncludeNonVisibleObjects = False
            geo_options.DetailLevel = ViewDetailLevel.Fine

            geo_element = wall.get_Geometry(geo_options)
            if not geo_element:
                return refs

            # Collect all planar faces with their normals
            faces_data = []

            for geo_obj in geo_element:
                solid = None

                if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                    solid = geo_obj
                elif isinstance(geo_obj, GeometryInstance):
                    inst_geo = geo_obj.GetInstanceGeometry()
                    for inst_obj in inst_geo:
                        if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                            solid = inst_obj
                            break

                if solid:
                    for face in solid.Faces:
                        if isinstance(face, PlanarFace) and face.Reference:
                            normal = face.FaceNormal
                            # Only get vertical faces (perpendicular to Z)
                            if abs(normal.Z) < 0.1:  # Nearly horizontal normal = vertical face
                                faces_data.append({
                                    'reference': face.Reference,
                                    'normal': normal,
                                    'center': face.Origin
                                })

            if len(faces_data) < 4:
                if Config.VERBOSE_OUTPUT:
                    print("Not enough planar faces found: {}".format(len(faces_data)))
                return refs

            # Find pairs of opposite faces using LOCAL orientation
            # X direction: faces perpendicular to LOCAL x_axis (normal parallel to y_axis)
            # Y direction: faces perpendicular to LOCAL y_axis (normal parallel to x_axis)

            x_faces = []  # Faces perpendicular to LOCAL X axis
            y_faces = []  # Faces perpendicular to LOCAL Y axis

            for face_data in faces_data:
                normal = face_data['normal']

                # Project normal onto local axes using dot product
                dot_x = abs(normal.DotProduct(x_axis))  # How parallel to local x_axis
                dot_y = abs(normal.DotProduct(y_axis))  # How parallel to local y_axis

                # SWAPPED: Vertical faces (normal parallel to X) measure horizontal distance (Y)
                # Horizontal faces (normal parallel to Y) measure vertical distance (X)
                if dot_x > dot_y:  # Normal more aligned with X axis = vertical faces
                    y_faces.append(face_data)  # For Y dimension (horizontal measurement)
                else:  # Normal more aligned with Y axis = horizontal faces
                    x_faces.append(face_data)  # For X dimension (vertical measurement)

            # Get opposing X faces (perpendicular to local x_axis)
            if len(x_faces) >= 2:
                # Sort by position projected onto local x_axis
                x_faces.sort(key=lambda f: (f['center'] - center).DotProduct(x_axis))
                refs['length_start'] = x_faces[0]['reference']  # Face on negative x_axis side
                refs['length_end'] = x_faces[-1]['reference']  # Face on positive x_axis side

            # Get opposing Y faces (perpendicular to local y_axis)
            if len(y_faces) >= 2:
                # Sort by position projected onto local y_axis
                y_faces.sort(key=lambda f: (f['center'] - center).DotProduct(y_axis))
                refs['width_interior'] = y_faces[0]['reference']  # Face on negative y_axis side
                refs['width_exterior'] = y_faces[-1]['reference']  # Face on positive y_axis side

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting geometry references: {}".format(e))

        return refs

    def _get_face_references(self, wall):
        """Get references from faces - finds opposing faces using LOCAL orientation"""
        refs = {}

        try:
            # Get wall orientation and location
            orientation = wall.Orientation
            location = wall.Location

            if not isinstance(location, LocationCurve):
                return refs

            curve = location.Curve
            center = curve.Evaluate(0.5, True)

            # Create local coordinate system
            direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
            x_axis = direction
            y_axis = XYZ.BasisZ.CrossProduct(x_axis).Normalize()

            geo_options = Options()
            geo_options.ComputeReferences = True
            geo_options.View = self.view
            geo_options.DetailLevel = ViewDetailLevel.Fine

            geo_element = wall.get_Geometry(geo_options)
            if not geo_element:
                return refs

            # Collect planar faces
            faces_data = []
            for geo_obj in geo_element:
                if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                    for face in solid.Faces:
                        if isinstance(face, PlanarFace) and face.Reference:
                            normal = face.FaceNormal
                            # Only vertical faces
                            if abs(normal.Z) < 0.1:
                                faces_data.append({
                                    'reference': face.Reference,
                                    'normal': normal,
                                    'center': face.Origin
                                })

            if len(faces_data) < 4:
                return refs

            # Separate X and Y aligned faces using LOCAL orientation
            x_faces = []  # Faces perpendicular to LOCAL X axis
            y_faces = []  # Faces perpendicular to LOCAL Y axis

            for face_data in faces_data:
                normal = face_data['normal']

                # Project normal onto local axes
                dot_x = abs(normal.DotProduct(x_axis))
                dot_y = abs(normal.DotProduct(y_axis))

                # SWAPPED: Vertical faces (normal parallel to X) measure horizontal distance (Y)
                # Horizontal faces (normal parallel to Y) measure vertical distance (X)
                if dot_x > dot_y:  # Normal parallel to x_axis = vertical faces
                    y_faces.append(face_data)  # For Y dimension (horizontal measurement)
                else:  # Normal parallel to y_axis = horizontal faces
                    x_faces.append(face_data)  # For X dimension (vertical measurement)

            # Get opposing faces using LOCAL coordinate system
            if len(x_faces) >= 2:
                # Sort by position projected onto local x_axis
                x_faces.sort(key=lambda f: (f['center'] - center).DotProduct(x_axis))
                refs['length_start'] = x_faces[0]['reference']
                refs['length_end'] = x_faces[-1]['reference']

            if len(y_faces) >= 2:
                # Sort by position projected onto local y_axis
                y_faces.sort(key=lambda f: (f['center'] - center).DotProduct(y_axis))
                refs['width_interior'] = y_faces[0]['reference']
                refs['width_exterior'] = y_faces[-1]['reference']

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting face references: {}".format(e))

        return refs

    def _validate_length_references(self, refs):
        """Check if we have length references"""
        return 'length_start' in refs and 'length_end' in refs

    def _validate_references(self, refs):
        """Check if we have all 4 valid references"""
        required_keys = ['length_start', 'length_end', 'width_interior', 'width_exterior']
        return all(key in refs and refs[key] is not None for key in required_keys)


# ============================================================================
# WALL PROCESSOR
# ============================================================================
class WallProcessor:
    """Process individual wall for dimensioning"""

    def __init__(self, doc, view, length_dim_type, width_dim_type, offset_internal, text_offset_internal):
        self.doc = doc
        self.view = view
        self.length_dim_type = length_dim_type
        self.width_dim_type = width_dim_type
        self.offset_internal = offset_internal
        self.text_offset_internal = text_offset_internal
        self.orientation_handler = WallOrientationHandler(doc)
        self.ref_handler = WallReferenceHandler(doc, view)

    def process(self, wall, dimension_both=True):
        """
        Process one wall and create dimensions
        Returns: tuple (success, dimension_ids, error_message, method_name)
        """
        try:
            if Config.VERBOSE_OUTPUT:
                print("Processing wall ID: {}".format(wall.Id))

            # Get references
            refs = self.ref_handler.get_wall_references(wall)
            if Config.VERBOSE_OUTPUT:
                print("Wall references: {}".format(refs))
            if not refs:
                return False, [], "Could not get references from wall", None

            # Get location and orientation
            location_data = self._get_wall_location_data(wall)
            if Config.VERBOSE_OUTPUT:
                print("Wall location data: {}".format(location_data))
            if not location_data:
                return False, [], "Could not get wall location", None

            center = location_data['center']
            direction = location_data['direction']
            orientation = location_data['orientation']

            # Create dimensions
            dim_ids = []
            created_dimensions = []

            # Length dimension (along LocationCurve)
            if self.length_dim_type and ('length_start' in refs and 'length_end' in refs):
                if Config.VERBOSE_OUTPUT:
                    print("Creating length dimension...")
                dim_length = self._create_length_dimension(wall, refs, center, direction, orientation)
                if dim_length:
                    dim_ids.append(dim_length.Id)
                    created_dimensions.append(dim_length)
                    if Config.VERBOSE_OUTPUT:
                        print("Length dimension created: {}".format(dim_length.Id))
                else:
                    if Config.VERBOSE_OUTPUT:
                        print("Failed to create length dimension")
            else:
                if Config.VERBOSE_OUTPUT:
                    print("Skipping length dimension - missing refs or dim type")

            # Width dimension (perpendicular, using orientation)
            if dimension_both and self.width_dim_type and ('width_interior' in refs and 'width_exterior' in refs):
                if Config.VERBOSE_OUTPUT:
                    print("Creating width dimension...")
                dim_width = self._create_width_dimension(wall, refs, center, direction, orientation)
                if dim_width:
                    dim_ids.append(dim_width.Id)
                    created_dimensions.append(dim_width)
                    if Config.VERBOSE_OUTPUT:
                        print("Width dimension created: {}".format(dim_width.Id))
                else:
                    if Config.VERBOSE_OUTPUT:
                        print("Failed to create width dimension")
            else:
                if Config.VERBOSE_OUTPUT:
                    print("Skipping width dimension - missing refs, dim type, or dimension_both=False")

            # Reposition text only for width dimension (to avoid wall overlap)
            if 'dim_width' in locals() and dim_width:
                self._reposition_dimension_text(dim_width, wall, direction, orientation)

            if len(dim_ids) > 0:
                if Config.VERBOSE_OUTPUT:
                    print("Successfully created {} dimensions".format(len(dim_ids)))
                return True, dim_ids, None, 'geometry_references'
            else:
                if Config.VERBOSE_OUTPUT:
                    print("No dimensions were created")
                return False, [], "Failed to create dimensions", 'geometry_references'

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Exception in wall processing: {}".format(str(e)))
                import traceback
                traceback.print_exc()
            return False, [], str(e), None

    def _get_wall_segments(self, wall):
        """Get individual segments of a wall (for L-shaped walls)"""
        segments = []

        try:
            location = wall.Location
            if not isinstance(location, LocationCurve):
                return [wall]  # Return wall itself as single segment

            curve = location.Curve

            # Check if it's a PolyLine (L-shaped wall)
            if hasattr(curve, 'GetCoordinates'):
                # This is a PolyLine - L-shaped wall
                try:
                    coords = curve.GetCoordinates()
                    if len(coords) > 2:  # More than 2 points = L-shaped
                        # Create virtual segments
                        for i in range(len(coords) - 1):
                            segment = {
                                'start_point': coords[i],
                                'end_point': coords[i + 1],
                                'direction': (coords[i + 1] - coords[i]).Normalize(),
                                'length': coords[i].DistanceTo(coords[i + 1])
                            }
                            segments.append(segment)
                    else:
                        # Regular line
                        segments.append({
                            'start_point': coords[0],
                            'end_point': coords[1],
                            'direction': (coords[1] - coords[0]).Normalize(),
                            'length': coords[0].DistanceTo(coords[1])
                        })
                except:
                    # Fallback for other curve types
                    segments.append({
                        'start_point': curve.GetEndPoint(0),
                        'end_point': curve.GetEndPoint(1),
                        'direction': (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize(),
                        'length': curve.Length
                    })
            else:
                # Single curve (Line, Arc, etc.)
                segments.append({
                    'start_point': curve.GetEndPoint(0),
                    'end_point': curve.GetEndPoint(1),
                    'direction': (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize(),
                    'length': curve.Length
                })

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting wall segments: {}".format(e))
            # Fallback: treat as single segment
            segments.append(wall)

        return segments

    def _process_wall_segment(self, wall, segment, dimension_both=True):
        """
        Process a single wall segment and create dimensions
        Use wall's overall references instead of segment-specific ones
        """
        try:
            # Get references from the entire wall (not segment-specific)
            refs = self.ref_handler.get_wall_references(wall)
            if Config.VERBOSE_OUTPUT:
                print("Wall references for segment: {}".format(refs))
            if not refs:
                return False, [], "Could not get references from wall", None

            # Get location and orientation for this segment
            center = segment['start_point'].Add(segment['direction'].Multiply(segment['length'] * 0.5))
            direction = segment['direction']
            orientation = wall.Orientation  # Use wall's overall orientation

            # Create dimensions
            dim_ids = []
            created_dimensions = []

            # Length dimension (along segment)
            if self.length_dim_type and ('length_start' in refs and 'length_end' in refs):
                if Config.VERBOSE_OUTPUT:
                    print("Creating length dimension for segment...")
                dim_length = self._create_segment_length_dimension(wall, segment, refs, center, direction, orientation)
                if dim_length:
                    dim_ids.append(dim_length.Id)
                    created_dimensions.append(dim_length)
                    if Config.VERBOSE_OUTPUT:
                        print("Length dimension created for segment: {}".format(dim_length.Id))
                else:
                    if Config.VERBOSE_OUTPUT:
                        print("Failed to create length dimension for segment")

            # Width dimension (perpendicular, using orientation)
            if dimension_both and self.width_dim_type and ('width_interior' in refs and 'width_exterior' in refs):
                if Config.VERBOSE_OUTPUT:
                    print("Creating width dimension for segment...")
                dim_width = self._create_segment_width_dimension(wall, segment, refs, center, direction, orientation)
                if dim_width:
                    dim_ids.append(dim_width.Id)
                    created_dimensions.append(dim_width)
                    if Config.VERBOSE_OUTPUT:
                        print("Width dimension created for segment: {}".format(dim_width.Id))
                else:
                    if Config.VERBOSE_OUTPUT:
                        print("Failed to create width dimension for segment")
            else:
                if Config.VERBOSE_OUTPUT:
                    print("Skipping width dimension - missing refs, dim type, or dimension_both=False")

            # Reposition text only for width dimension (to avoid wall overlap)
            if 'dim_width' in locals() and dim_width:
                self._reposition_dimension_text(dim_width, wall, direction, orientation)

            if len(dim_ids) > 0:
                if Config.VERBOSE_OUTPUT:
                    print("Successfully created {} dimensions for segment".format(len(dim_ids)))
                return True, dim_ids, None, 'segment_geometry'
            else:
                if Config.VERBOSE_OUTPUT:
                    print("No dimensions were created for segment")
                return False, [], "Failed to create dimensions for segment", 'segment_geometry'

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Exception in segment processing: {}".format(str(e)))
                import traceback
                traceback.print_exc()
            return False, [], str(e), None

    def _get_wall_location_data(self, wall):
        """Get wall center point, direction, and orientation"""
        try:
            location = wall.Location
            if not isinstance(location, LocationCurve):
                return None

            curve = location.Curve
            center = curve.Evaluate(0.5, True)
            direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
            orientation = wall.Orientation

            return {
                'center': center,
                'direction': direction,
                'orientation': orientation
            }

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting wall location data: {}".format(e))
            return None

    def _get_segment_references(self, wall, segment):
        """Get references for a specific wall segment - DEPRECATED: Use wall-level references instead"""
        # This method is no longer used since we switched to wall-level references
        # Keeping for compatibility but it delegates to wall-level reference handler
        return self.ref_handler.get_wall_references(wall)

    def _create_segment_length_dimension(self, wall, segment, refs, center, direction, orientation):
        """Create dimension line parallel to segment (length)"""
        try:
            # Get segment endpoints
            start_point = segment['start_point']
            end_point = segment['end_point']

            # Get perpendicular offset direction (Wall.Orientation) using WallOrientationHandler
            offset_direction = self.orientation_handler.get_wall_orientation(wall)

            # Calculate dimension line position
            midpoint = start_point.Add(direction.Multiply(segment['length'] * 0.5))
            offset_vec = offset_direction.Multiply(self.offset_internal)

            # Create dimension line parallel to segment
            line_start = start_point.Add(offset_vec)
            line_end = end_point.Add(offset_vec)
            dim_line = Line.CreateBound(line_start, line_end)

            # Create dimension with start & end references
            ref_array = ReferenceArray()
            ref_array.Append(refs['length_start'])
            ref_array.Append(refs['length_end'])

            # Try creating dimension, if it fails due to non-linear type, try without specifying type
            try:
                dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array, self.length_dim_type)
                return dimension
            except Exception as type_error:
                if "non-linear dimension type" in str(type_error):
                    if Config.VERBOSE_OUTPUT:
                        print("Dimension type is non-linear, trying without type specification")
                    # Try without specifying dimension type (uses default)
                    dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array)
                    return dimension
                else:
                    raise type_error

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error creating segment length dimension: {}".format(e))
            return None

    def _create_segment_width_dimension(self, wall, segment, refs, center, direction, orientation):
        """Create dimension line perpendicular to segment (width)"""
        try:
            # Get segment midpoint
            midpoint = segment['start_point'].Add(direction.Multiply(segment['length'] * 0.5))

            # Get wall direction & orientation using WallOrientationHandler
            orientation = self.orientation_handler.get_wall_orientation(wall)  # Perpendicular to wall

            # Calculate dimension line position
            # Offset parallel to segment (at midpoint + offset)
            offset_vec = direction.Multiply(self.offset_internal)
            base_point = midpoint.Add(offset_vec)

            # Create dimension line perpendicular to segment
            # Line direction = Wall.Orientation
            # Estimate wall thickness for line length
            wall_thickness = self._get_wall_thickness(wall)
            line_vec = orientation.Multiply(wall_thickness + 2.0)  # Add extra length
            line_start = base_point.Subtract(line_vec)
            line_end = base_point.Add(line_vec)
            dim_line = Line.CreateBound(line_start, line_end)

            # Create dimension with interior & exterior face references
            ref_array = ReferenceArray()
            ref_array.Append(refs['width_interior'])
            ref_array.Append(refs['width_exterior'])

            # Try creating dimension, if it fails due to non-linear type, try without specifying type
            try:
                dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array, self.width_dim_type)
                return dimension
            except Exception as type_error:
                if "non-linear dimension type" in str(type_error):
                    if Config.VERBOSE_OUTPUT:
                        print("Width dimension type is non-linear, trying without type specification")
                    # Try without specifying dimension type (uses default)
                    dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array)
                    return dimension
                else:
                    raise type_error

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error creating segment width dimension: {}".format(e))
            return None

    def _create_length_dimension(self, wall, refs, center, direction, orientation):
        """Create dimension line parallel to wall (length)"""
        try:
            # Get LocationCurve
            location_curve = wall.Location.Curve

            # Get wall direction (tangent)
            direction = (location_curve.GetEndPoint(1) -
                         location_curve.GetEndPoint(0)).Normalize()

            # Get perpendicular offset direction (Wall.Orientation) using WallOrientationHandler
            offset_direction = self.orientation_handler.get_wall_orientation(wall)

            # Calculate dimension line position
            midpoint = location_curve.Evaluate(0.5, True)
            offset_vec = offset_direction.Multiply(self.offset_internal)

            # Create dimension line parallel to wall
            line_start = location_curve.GetEndPoint(0).Add(offset_vec)
            line_end = location_curve.GetEndPoint(1).Add(offset_vec)
            dim_line = Line.CreateBound(line_start, line_end)

            # Create dimension with start & end references
            ref_array = ReferenceArray()
            ref_array.Append(refs['length_start'])
            ref_array.Append(refs['length_end'])

            # Try creating dimension, if it fails due to non-linear type, try without specifying type
            try:
                dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array, self.length_dim_type)
                return dimension
            except Exception as type_error:
                if "non-linear dimension type" in str(type_error):
                    if Config.VERBOSE_OUTPUT:
                        print("Dimension type is non-linear, trying without type specification")
                    # Try without specifying dimension type (uses default)
                    dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array)
                    return dimension
                else:
                    raise type_error

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error creating length dimension: {}".format(e))
            return None

    def _create_width_dimension(self, wall, refs, center, direction, orientation):
        """Create dimension line perpendicular to wall (width)"""
        try:
            # Get wall midpoint
            location_curve = wall.Location.Curve
            midpoint = location_curve.Evaluate(0.5, True)

            # Get wall direction & orientation using WallOrientationHandler
            direction = (location_curve.GetEndPoint(1) -
                         location_curve.GetEndPoint(0)).Normalize()
            orientation = self.orientation_handler.get_wall_orientation(wall)  # Perpendicular to wall

            # Calculate dimension line position
            # Offset parallel to wall (at midpoint + offset)
            offset_vec = direction.Multiply(self.offset_internal)
            base_point = midpoint.Add(offset_vec)

            # Create dimension line perpendicular to wall
            # Line direction = Wall.Orientation
            # Estimate wall thickness for line length
            wall_thickness = self._get_wall_thickness(wall)
            line_vec = orientation.Multiply(wall_thickness + 2.0)  # Add extra length
            line_start = base_point.Subtract(line_vec)
            line_end = base_point.Add(line_vec)
            dim_line = Line.CreateBound(line_start, line_end)

            # Create dimension with interior & exterior face references
            ref_array = ReferenceArray()
            ref_array.Append(refs['width_interior'])
            ref_array.Append(refs['width_exterior'])

            # Try creating dimension, if it fails due to non-linear type, try without specifying type
            try:
                dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array, self.width_dim_type)
                return dimension
            except Exception as type_error:
                if "non-linear dimension type" in str(type_error):
                    if Config.VERBOSE_OUTPUT:
                        print("Width dimension type is non-linear, trying without type specification")
                    # Try without specifying dimension type (uses default)
                    dimension = self.doc.Create.NewDimension(self.view, dim_line, ref_array)
                    return dimension
                else:
                    raise type_error

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error creating width dimension: {}".format(e))
            return None

    def _get_wall_thickness(self, wall):
        """Get wall thickness from parameters or geometry"""
        try:
            # Try parameter first
            thickness_param = wall.LookupParameter("Width")
            if thickness_param and thickness_param.HasValue:
                return thickness_param.AsDouble()

            # Try geometry
            geo_options = Options()
            geo_options.ComputeReferences = False
            geo_options.View = self.view

            geo_element = wall.get_Geometry(geo_options)
            if geo_element:
                for geo_obj in geo_element:
                    solid = None
                    if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                        solid = geo_obj
                    elif isinstance(geo_obj, GeometryInstance):
                        inst_geo = geo_obj.GetInstanceGeometry()
                        for inst_obj in inst_geo:
                            if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                                solid = inst_obj
                                break

                    if solid:
                        bbox = solid.GetBoundingBox()
                        if bbox:
                            return bbox.Max.X - bbox.Min.X

            return 0.2  # Default 200mm

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error getting wall thickness: {}".format(e))
            return 0.2  # Default 200mm

    def _reposition_dimension_text(self, dimension, wall, direction, orientation):
        """Reposition dimension text diagonally 45° to avoid wall overlap"""
        try:
            # Calculate diagonal movement vector (45° from wall direction)
            # For walls, we want to move text away from the wall geometry
            # Diagonal vector combines wall direction + perpendicular component

            # Get wall direction (normalized)
            wall_dir = direction.Normalize()

            # Create 45° diagonal vector: (direction + perpendicular)
            # Perpendicular to wall direction in XY plane
            perp_vector = XYZ(-wall_dir.Y, wall_dir.X, 0).Normalize()

            # Diagonal = direction + perpendicular (45° angle)
            diagonal_vector = (wall_dir.Add(perp_vector)).Normalize()

            # Apply text offset distance
            move_vector = diagonal_vector.Multiply(self.text_offset_internal)

            # Get current text position and move it
            current_pos = dimension.TextPosition
            new_pos = current_pos.Add(move_vector)

            # Set new text position
            dimension.TextPosition = new_pos

            if Config.VERBOSE_OUTPUT:
                print("Repositioned dimension text from ({:.3f}, {:.3f}) to ({:.3f}, {:.3f})".format(
                    current_pos.X, current_pos.Y, new_pos.X, new_pos.Y))

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error repositioning dimension text: {}".format(e))
            # Silently continue if repositioning fails


# ============================================================================
# MAIN CONTROLLER
# ============================================================================
class AutoDimensionWallController:
    """Main controller for auto dimensioning walls"""

    def __init__(self):
        self.doc = revit.doc
        self.uidoc = revit.uidoc
        self.active_view = self.doc.ActiveView
        self.output = script.get_output()

    def get_all_plan_views(self):
        """Get all plan views (floor and structural) in the project, sorted by elevation"""
        try:
            collector = FilteredElementCollector(self.doc).OfClass(ViewPlan)
            plan_views = []

            for view in collector:
                # Skip template views and non-printable views
                if not view.IsTemplate and view.CanBePrinted:
                    # Check if it's a plan view (floor, structural, etc.)
                    view_family_type = self.doc.GetElement(view.GetTypeId())
                    if view_family_type:
                        family_name = view_family_type.get_Parameter(
                            BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                        if family_name:
                            name_lower = family_name.lower()
                            # Include floor plans, structural plans, and any plan views
                            if ('floor' in name_lower or
                                'lantai' in name_lower or
                                'structural' in name_lower or
                                'struktur' in name_lower or
                                'plan' in name_lower):
                                plan_views.append(view)

            # Sort by level elevation
            plan_views.sort(key=lambda v: v.GenLevel.Elevation if v.GenLevel else 0)
            return plan_views

        except Exception as e:
            print("Error getting plan views: {}".format(e))
            return []

    def get_walls_in_view(self, view):
        """Get all walls visible in a specific view"""
        try:
            # Get all walls in project
            collector = FilteredElementCollector(self.doc)
            walls = collector.OfCategory(BuiltInCategory.OST_Walls).ToElements()

            # Filter walls that are visible in this view
            visible_walls = []

            for wall in walls:
                if self.is_wall_visible_in_view(wall, view):
                    visible_walls.append(wall)

            return visible_walls

        except Exception as e:
            print("Error getting walls in view: {}".format(e))
            return []

    def is_wall_visible_in_view(self, wall, view):
        """Check if wall is visible in the given view"""
        try:
            # Get view level
            view_level = view.GenLevel
            if not view_level:
                return False

            # Use wall level filtering logic
            filter = WallLevelFilter(self.doc)
            view_level = filter.get_view_level(view)
            return filter.should_tag_wall_in_view(wall, view_level)

        except Exception as e:
            print("Error checking wall visibility: {}".format(e))
            return False

    def show_settings_dialog(self):
        """Show settings dialog for configuring default values"""
        config = ConfigurationManager()

        # Get current values
        current_offset = config.get_offset_mm()
        current_text_offset = config.get_text_offset_mm()
        current_length_dim_type = config.get_length_dimension_type_name()
        current_width_dim_type = config.get_width_dimension_type_name()
        current_dimension_both = config.get_dimension_both()
        current_verbose = config.get_verbose_output()

        # Ask for offset
        offset_str = forms.ask_for_string(
            prompt="Enter default offset distance in millimeters:",
            default=str(current_offset),
            title="Default Offset Distance"
        )

        if not offset_str:
            return False

        try:
            offset_mm = float(offset_str)
            if offset_mm <= 0:
                forms.alert("Offset must be a positive number.", title="Invalid Input")
                return False
        except ValueError:
            forms.alert("Invalid offset value. Please enter a valid number.", title="Invalid Input")
            return False

        # Ask for text offset
        text_offset_str = forms.ask_for_string(
            prompt="Enter text repositioning offset in millimeters (diagonal 45° movement):",
            default=str(current_text_offset),
            title="Text Repositioning Offset"
        )

        if not text_offset_str:
            return False

        try:
            text_offset_mm = float(text_offset_str)
            if text_offset_mm < 0:
                forms.alert("Text offset cannot be negative.", title="Invalid Input")
                return False
        except ValueError:
            forms.alert("Invalid text offset value. Please enter a valid number.", title="Invalid Input")
            return False

        # Get available dimension types
        dim_types = self._get_available_dimension_types()

        if not dim_types:
            forms.alert("No dimension types found in project.", title="No Dimension Types")
            return False

        # Ask for length dimension type
        selected_length_dim_type = forms.SelectFromList.show(
            dim_types,
            title="Select Default Length Dimension Type",
            button_name="Select",
            multiselect=False,
            default=current_length_dim_type if current_length_dim_type in dim_types else None
        )

        if not selected_length_dim_type:
            return False

        # Ask for width dimension type
        selected_width_dim_type = forms.SelectFromList.show(
            dim_types,
            title="Select Default Width Dimension Type",
            button_name="Select",
            multiselect=False,
            default=current_width_dim_type if current_width_dim_type in dim_types else None
        )

        if not selected_width_dim_type:
            return False

        # Ask for dimension both
        dimension_both_options = ["Dimension both length and width", "Dimension length only"]
        dimension_both_choice = forms.CommandSwitchWindow.show(
            dimension_both_options,
            message='Select dimensioning mode:'
        )

        if dimension_both_choice == "Dimension both length and width":
            dimension_both = True
        else:
            dimension_both = False

        # Ask for verbose output
        verbose_options = ["Normal output", "Verbose output"]
        verbose_choice = forms.CommandSwitchWindow.show(
            verbose_options,
            message='Select output mode:'
        )

        verbose_output = (verbose_choice == "Verbose output")

        # Save settings
        config.set_offset_mm(offset_mm)
        config.set_text_offset_mm(text_offset_mm)
        config.set_length_dimension_type_name(selected_length_dim_type)
        config.set_width_dimension_type_name(selected_width_dim_type)
        config.set_dimension_both(dimension_both)
        config.set_verbose_output(verbose_output)

        forms.alert("Settings saved successfully!\n\nOffset: {} mm\nText Repositioning: {} mm\nLength Dimension Type: {}\nWidth Dimension Type: {}\nDimension Both: {}\nVerbose Output: {}".format(
            offset_mm, text_offset_mm, selected_length_dim_type, selected_width_dim_type, dimension_both, verbose_output), title="Settings Saved")
        return True

    def _get_available_dimension_types(self):
        """Get list of available LINEAR dimension type names"""
        try:
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            dim_type_names = []

            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name and self._is_linear_dimension_type(dt):
                        dim_type_names.append(name)
                except:
                    continue

            if not dim_type_names:
                print("Warning: No linear dimension types found in project")
            else:
                print("Found {} linear dimension types".format(len(dim_type_names)))

            return sorted(dim_type_names) if dim_type_names else []
        except Exception as e:
            print("Error getting dimension types: {}".format(e))
            return []

    def run(self):
        """Main execution flow - supports both single view and batch processing with Shift+Click settings"""
        # Check for modifier keys
        if WinForms.Control.ModifierKeys == WinForms.Keys.Shift:
            self.show_settings_dialog()
            return

        # Set verbose output based on config
        config = ConfigurationManager()
        Config.VERBOSE_OUTPUT = config.get_verbose_output()

        # Check for Ctrl+Click (verbose mode)
        modifier_keys = WinForms.Control.ModifierKeys

        if modifier_keys == WinForms.Keys.Control:
            Config.VERBOSE_OUTPUT = True
        elif modifier_keys == (WinForms.Keys.Control | WinForms.Keys.Shift):
            Config.VERBOSE_OUTPUT = True

        # Normal execution - ask user for processing mode
        processing_mode = forms.CommandSwitchWindow.show(
            ['Current View Only', 'Batch Process in Selected Plan Views'],
            message='Select processing mode:'
        )

        print("Selected processing mode: {}".format(processing_mode))

        if not processing_mode:
            print("No processing mode selected - exiting")
            return

        if processing_mode == 'Current View Only':
            # Original single view processing
            print("Starting single view processing")
            self._run_single_view()
        else:
            # Batch processing all plan views (floor and structural)
            print("Starting batch processing")
            self._run_batch_processing()

    def _run_single_view(self):
        """Process walls in current view only"""
        # Step 1: Validate view
        if not self._validate_view():
            return

        # Step 2: Get user inputs
        config = self._get_user_inputs()
        if not config:
            return

        # Step 3: Get and validate walls
        walls = self._get_selected_walls()
        if not walls:
            return

        # Step 4: Process walls
        results = self._process_walls(walls, config)

        # Step 5: Show results
        self._show_results(results)

    def _run_batch_processing(self):
        """Batch process selected floor plan views"""
        # Get all plan views (floor and structural)
        plan_views = self.get_all_plan_views()
        if not plan_views:
            forms.alert("No plan views found in project.", title="No Plan Views")
            return

        # Store previously selected views for pre-selection when looping
        previous_selection = []

        # Loop for plan selection and confirmation
        while True:
            # Show advanced multi-select dialog for plan views
            dialog = AdvancedMultiSelectDialog(
                plan_views,
                "Select Plan Views to Process",
                item_display_func=get_view_display_name,
                preselected_items=previous_selection
            )
            result = dialog.ShowDialog()

            if result != DialogResult.OK:
                return  # User canceled selection

            selected_views = dialog.selected_items
            previous_selection = selected_views[:]  # Remember this selection

            # Show confirmation with selected plans
            message = "Selected {} plan views to process:\n\n".format(len(selected_views))
            selected_names = [get_view_display_name(view) for view in selected_views]
            message += "\n".join(selected_names)
            message += "\n\nProcess these plan views?"

            if forms.alert(message, title="Confirm Selection", yes=True, no=True):
                break  # User confirmed, exit loop and proceed

        # Get user inputs for selected plans
        config = self._get_user_inputs()
        if not config:
            return

        # Process each selected plan view
        total_processed = 0
        total_dimensions = 0
        plan_results = []

        if Config.VERBOSE_OUTPUT:
            print("Starting batch processing of {} selected plan views...".format(len(selected_views)))

        for plan_view in selected_views:
            if Config.VERBOSE_OUTPUT:
                print("\n=== Processing plan: {} ===".format(plan_view.Name))

            # Get walls visible in this view
            walls = self.get_walls_in_view(plan_view)
            if not walls:
                if Config.VERBOSE_OUTPUT:
                    print("No walls found in plan: {}".format(plan_view.Name))
                continue

            if Config.VERBOSE_OUTPUT:
                print("Found {} walls in plan".format(len(walls)))

            # Filter walls that continue upward from this level
            filtered_walls = []
            skipped_count = 0

            for wall in walls:
                if Utils.should_dimension_wall(wall, plan_view, self.doc):
                    filtered_walls.append(wall)
                else:
                    skipped_count += 1
                    if Config.VERBOSE_OUTPUT:
                        print("Skipped: Wall {} stops at current level".format(wall.Id.Value))

            if skipped_count > 0 and Config.VERBOSE_OUTPUT:
                print("Filtered out {} walls that stop at current level".format(skipped_count))

            if not filtered_walls:
                if Config.VERBOSE_OUTPUT:
                    print("No walls to dimension in plan: {}".format(plan_view.Name))
                continue

            if Config.VERBOSE_OUTPUT:
                print("Processing {} walls that continue upward".format(len(filtered_walls)))

            # Process walls for this view
            try:
                results = self._process_walls_for_view(filtered_walls, plan_view, config)
            except Exception as e:
                print("Error processing view {}: {}".format(plan_view.Name, e))
                results = {'success': [], 'failed': [{'element': None, 'name': 'All', 'id': 0, 'error': str(e)}], 'total': len(filtered_walls)}

            plan_result = {
                'view_name': plan_view.Name,
                'walls_processed': len(filtered_walls),
                'dimensions_created': len(results['success']) * 2,  # 2 dimensions per wall
                'success_count': len(results['success']),
                'failed_count': len(results['failed'])
            }
            plan_results.append(plan_result)

            total_processed += len(filtered_walls)
            total_dimensions += len(results['success']) * 2

            if Config.VERBOSE_OUTPUT:
                print("Completed plan {}: {} walls, {} dimensions created".format(
                    plan_view.Name, len(filtered_walls), len(results['success']) * 2))

        # Show final summary
        self._show_batch_results(plan_results, total_processed, total_dimensions)

    def _validate_view(self):
        """Validate that current view supports dimensions"""
        if not isinstance(self.active_view, ViewPlan):
            forms.alert(
                "Active view '{}' is not a plan view.\n"
                "Please switch to a floor plan or ceiling plan.".format(
                    self.active_view.Name
                ),
                title="Invalid View Type"
            )
            return False
        return True

    def _get_user_inputs(self):
        """Get configuration, automatically using saved settings"""
        config = ConfigurationManager()

        # Load saved settings
        offset_mm = config.get_offset_mm()
        text_offset_mm = config.get_text_offset_mm()
        length_dim_type_name = config.get_length_dimension_type_name()
        width_dim_type_name = config.get_width_dimension_type_name()
        dimension_both = config.get_dimension_both()

        # Find dimension types by name
        length_dim_type = self._find_dimension_type_by_name(length_dim_type_name)
        width_dim_type = self._find_dimension_type_by_name(width_dim_type_name)

        # If no dimension types found, prompt user to configure
        if not length_dim_type or not width_dim_type:
            forms.alert("Saved dimension types not found. Please configure settings using Shift+Click.", title="Configuration Needed")
            return None

        # Calculate internal offsets
        offset_feet = Utils.mm_to_feet(offset_mm)
        text_offset_feet = Utils.mm_to_feet(text_offset_mm)
        scale = Utils.get_view_scale_factor(self.active_view)
        offset_internal = offset_feet * scale
        text_offset_internal = text_offset_feet * scale

        return {
            'offset_mm': offset_mm,
            'text_offset_mm': text_offset_mm,
            'offset_internal': offset_internal,
            'text_offset_internal': text_offset_internal,
            'length_dim_type': length_dim_type,
            'width_dim_type': width_dim_type,
            'dimension_both': dimension_both
        }

    def _select_dimension_type_name(self):
        """Let user select dimension type name"""
        try:
            # Get all dimension types
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            dim_type_names = []

            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name:
                        dim_type_names.append(name)
                except:
                    continue

            if not dim_type_names:
                forms.alert("No dimension types found. Using default.")
                return Config.DEFAULT_LENGTH_DIM_TYPE_NAME

            # Sort names
            sorted_names = sorted(dim_type_names)

            # Select
            selected_name = forms.SelectFromList.show(
                sorted_names,
                title="Select Dimension Type",
                button_name="Select",
                multiselect=False
            )

            if selected_name:
                return selected_name
            else:
                return Config.DEFAULT_LENGTH_DIM_TYPE_NAME

        except Exception as e:
            print("Error selecting dimension type: {}".format(e))
            return Config.DEFAULT_LENGTH_DIM_TYPE_NAME

    def _find_dimension_type_by_name(self, type_name):
        """Find dimension type by name - ensure it's a linear dimension type"""
        try:
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)

            # First try exact match
            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name == type_name:
                        # Check if it's a linear dimension type
                        if self._is_linear_dimension_type(dt):
                            return dt
                        else:
                            print("Warning: Found dimension type '{}' but it's not linear".format(name))
                except:
                    continue

            # If exact match not found, try partial match
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name and Config.DEFAULT_LENGTH_DIM_TYPE_NAME in name:
                        if self._is_linear_dimension_type(dt):
                            return dt
                        else:
                            print("Warning: Found partial match '{}' but it's not linear".format(name))
                except:
                    continue

            # Return first available dimension type regardless of type (emergency fallback)
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    print("Using emergency fallback dimension type: {}".format(name or "Unnamed"))
                    print("WARNING: This may not be a linear dimension type!")
                except:
                    print("Using emergency fallback dimension type")
                return dt

            print("Error: No linear dimension types found in project")
            return None

        except Exception as e:
            print("Error finding dimension type: {}".format(e))
            return None

    def _is_linear_dimension_type(self, dimension_type):
        """Check if dimension type is linear (not angular, radial, etc.)"""
        try:
            # Check dimension style - try different parameter names
            style_params = [
                BuiltInParameter.DIM_STYLE_DIM_TYPE,
                BuiltInParameter.ALL_MODEL_TYPE_NAME
            ]

            for param_id in style_params:
                try:
                    style_param = dimension_type.get_Parameter(param_id)
                    if style_param and style_param.HasValue:
                        if param_id == BuiltInParameter.DIM_STYLE_DIM_TYPE:
                            dim_type_value = style_param.AsInteger()
                            # Linear dimension types are typically 0 (linear), others are angular, radial, etc.
                            return dim_type_value == 0
                        elif param_id == BuiltInParameter.ALL_MODEL_TYPE_NAME:
                            name = style_param.AsString()
                            # Check if name contains angular/radial keywords
                            if name and any(keyword in name.lower() for keyword in ['angular', 'radial', 'diameter', 'radius']):
                                return False
                            return True
                except Exception as param_error:
                    # Silently continue to next parameter
                    continue

            # Alternative: check dimension type name for common patterns
            try:
                name_param = dimension_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
                if name_param and name_param.HasValue:
                    name = name_param.AsString()
                    if name:
                        # Common non-linear dimension names
                        non_linear_keywords = ['angular', 'radial', 'diameter', 'radius', 'ordinate']
                        if any(keyword in name.lower() for keyword in non_linear_keywords):
                            return False
                        # Common linear dimension names
                        linear_keywords = ['linear', 'aligned', 'horizontal', 'vertical', 'arrow', 'tick']
                        if any(keyword in name.lower() for keyword in linear_keywords):
                            return True
            except Exception as name_error:
                # Silently continue
                pass

            # Default: assume it's linear if we can't determine
            return True

        except Exception as e:
            # Silently return True - don't print errors for every dimension type check
            return True  # Default to true

    def _get_selected_walls(self):
        """Get selected walls from Revit, with interactive selection if none selected"""
        selection = revit.get_selection()

        if not selection:
            # No pre-selection, prompt user to select walls
            try:
                selection_filter = WallSelectionFilter()

                # Prompt user to select walls
                selected_refs = self.uidoc.Selection.PickObjects(
                    ObjectType.Element,
                    selection_filter,
                    "Select walls to dimension (ESC to finish)"
                )

                if not selected_refs:
                    forms.alert("No walls selected.", title="Selection Cancelled")
                    return None

                # Convert references to elements
                walls = []
                processed_ids = set()

                for ref in selected_refs:
                    element = self.doc.GetElement(ref.ElementId)
                    if element and element.Id.Value not in processed_ids:
                        if Utils.is_wall(element):
                            walls.append(element)
                            processed_ids.add(element.Id.Value)

            except Exception as e:
                forms.alert(
                    "Selection cancelled or failed: {}".format(str(e)),
                    title="Selection Error"
                )
                return None
        else:
            # Filter existing selection
            walls = []
            processed_ids = set()

            for element in selection:
                if not element or element.Id.Value in processed_ids:
                    continue

                if Utils.is_wall(element):
                    walls.append(element)
                    processed_ids.add(element.Id.Value)

        if not walls:
            forms.alert(
                "No walls found in selection.\n"
                "Please select walls.",
                title="No Walls Found"
            )
            return None

        if Config.VERBOSE_OUTPUT:
            print("Found {} walls in selection".format(len(walls)))

        # Filter walls that continue above current level
        filtered_walls = []
        skipped_count = 0

        for wall in walls:
            if Utils.should_dimension_wall(wall, self.active_view, self.doc):
                filtered_walls.append(wall)
            else:
                skipped_count += 1
                if Config.VERBOSE_OUTPUT:
                    print("Skipped: Wall {} stops at current level".format(wall.Id.Value))

        if skipped_count > 0 and Config.VERBOSE_OUTPUT:
            print("Filtered out {} walls that stop at current level".format(skipped_count))

        if not filtered_walls:
            forms.alert(
                "All selected walls stop at current level.\n"
                "No walls to dimension.",
                title="No Walls to Dimension"
            )
            return None

        if Config.VERBOSE_OUTPUT:
            print("Processing {} walls that continue upward".format(len(filtered_walls)))
        return filtered_walls

    def _process_walls(self, walls, config):
        """Process all walls and create dimensions"""
        return self._process_walls_for_view(walls, self.active_view, config)

    def _process_walls_for_view(self, walls, view, config):
        """Process walls for a specific view"""
        # Make view active for dimension creation
        self.uidoc.ActiveView = view

        # Recalculate offsets for this view's scale
        scale = Utils.get_view_scale_factor(view)
        offset_feet = Utils.mm_to_feet(config['offset_mm'])
        offset_internal = offset_feet * scale

        text_offset_feet = Utils.mm_to_feet(config['text_offset_mm'])
        text_offset_internal = text_offset_feet * scale

        processor = WallProcessor(
            self.doc,
            view,
            config['length_dim_type'],
            config['width_dim_type'],
            offset_internal,
            text_offset_internal
        )

        results = {
            'success': [],
            'failed': [],
            'total': len(walls)
        }

        # Use standard Revit Transaction
        t = Transaction(self.doc, "Auto Dimension Walls - {}".format(view.Name))
        t.Start()
        try:
            for wall in walls:
                success, dim_ids, error, method = processor.process(wall, config['dimension_both'])

                wall_id = wall.Id.Value
                wall_name = "Wall {}".format(wall_id)

                try:
                    if hasattr(wall, 'Name') and wall.Name:
                        wall_name = wall.Name
                except:
                    pass

                if success:
                    results['success'].append({
                        'element': wall,
                        'name': wall_name,
                        'id': wall_id,
                        'dimensions': len(dim_ids),
                        'method': method
                    })
                    if Config.VERBOSE_OUTPUT:
                        print("✓ {} - {} dimensions created using {}".format(wall_name, len(dim_ids), method))
                else:
                    results['failed'].append({
                        'element': wall,
                        'name': wall_name,
                        'id': wall_id,
                        'error': error
                    })
                    if Config.VERBOSE_OUTPUT:
                        print("✗ {} - Failed: {}".format(wall_name, error))
        except Exception as e:
            t.RollBack()
            raise e
        else:
            t.Commit()

        return results

    def _show_results(self, results):
        """Show summary of results"""
        success_count = len(results['success'])
        failed_count = len(results['failed'])
        total = results['total']

        message = "Dimension Creation Complete\n\n"
        message += "Total walls: {}\n".format(total)
        message += "Success: {}\n".format(success_count)
        message += "Failed: {}\n".format(failed_count)

        if success_count > 0:
            message += "\nSuccessful walls:\n"
            for item in results['success']:
                method_display = item.get('method', 'unknown').replace('_', ' ')
                message += "- {} (ID: {}): {} dimensions using {}\n".format(
                    item['name'], item['id'], item['dimensions'], method_display
                )

        if failed_count > 0:
            message += "\nFailed walls:\n"
            for item in results['failed']:
                message += "- {} (ID: {}): {}\n".format(
                    item['name'], item['id'], item['error']
                )

        forms.alert(message, title="Auto Dimension Walls Results")

    def _show_batch_results(self, plan_results, total_walls, total_dimensions):
        """Show summary of batch processing results in console"""
        print("\n" + "="*60)
        print("BATCH PROCESSING COMPLETE!")
        print("="*60)
        print("Summary:")
        print("- Floor plans processed: {}".format(len(plan_results)))
        print("- Total walls processed: {}".format(total_walls))
        print("- Total dimensions created: {}".format(total_dimensions))

        if plan_results:
            print("\nResults by floor plan:")
            print("-" * 50)

            for result in plan_results:
                print("{}:".format(result['view_name']))
                print("  Walls: {} | Dimensions: {} | Success: {} | Failed: {}".format(
                    result['walls_processed'],
                    result['dimensions_created'],
                    result['success_count'],
                    result['failed_count']
                ))

        # Show detailed results if there were failures
        failed_plans = [r for r in plan_results if r['failed_count'] > 0]
        if failed_plans:
            print("\nPlans with failures:")
            for plan in failed_plans:
                print("- {}: {} failed".format(plan['view_name'], plan['failed_count']))

        print("="*60)


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    controller = AutoDimensionWallController()
    controller.run()