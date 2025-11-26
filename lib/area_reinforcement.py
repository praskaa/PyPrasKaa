# -*- coding: utf-8 -*-
"""
Area Reinforcement Library Module
Implementasi dari logic library LOG-UTIL-REBAR-007

Modul ini berisi utilities untuk:
- Multi-layer area reinforcement processing
- Settings processor untuk UI integration
- Geometry conversion utilities
- Parameter override framework
"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *
from Autodesk.Revit.UI import *

# Standard imports
import sys
import traceback
from collections import defaultdict

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_logger_call(logger, method_name, message, *args, **kwargs):
    """Safe logger method call dengan fallback untuk pyRevit compatibility"""
    if logger:
        try:
            method = getattr(logger, method_name)
            return method(message, *args, **kwargs)
        except AttributeError:
            # Fallback ke print biasa untuk pyRevit logger
            print("[{}] {}".format(method_name.upper(), message))
    return None

def find_rebar_bar_type_by_name(doc, name):
    """Find RebarBarType by name (case-insensitive)"""
    if not name:
        return None

    collector = FilteredElementCollector(doc).OfClass(RebarBarType)
    for bar_type in collector:
        try:
            bar_type_name = bar_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            if bar_type_name and bar_type_name.lower() == name.lower():
                return bar_type.Id
        except:
            continue
    return None


def get_bar_diameter_from_rebar_bar_type(bar_type):
    """Extract diameter dari RebarBarType name (format: "D10", "D13", etc.)"""
    if not bar_type or not hasattr(bar_type, 'Name'):
        return 0

    name = bar_type.Name
    if not name.startswith("D"):
        return 0

    try:
        diameter_str = name[1:]  # Remove "D"
        return float(diameter_str)
    except ValueError:
        return 0


def get_max_bar_diameter_from_area_reinforcement(area_reinf):
    """Get maximum bar diameter dari Area Reinforcement element"""
    max_diameter = 0

    # Get semua bar types yang digunakan
    bar_types = get_bar_types_from_area_reinforcement(area_reinf)

    for bar_type in bar_types:
        diameter = get_bar_diameter_from_rebar_bar_type(bar_type)
        max_diameter = max(max_diameter, diameter)

    return max_diameter


def get_bar_types_from_area_reinforcement(area_reinf):
    """Get list of RebarBarType elements used in Area Reinforcement"""
    bar_types = []

    # Check semua bar type parameters
    bar_type_params = [
        "Bottom/Interior Major Bar Type",
        "Bottom/Interior Minor Bar Type",
        "Top/Exterior Major Bar Type",
        "Top/Exterior Minor Bar Type"
    ]

    for param_name in bar_type_params:
        param_value = get_parameter_value_safe(area_reinf, param_name)
        if param_value and param_value != ElementId.InvalidElementId:
            bar_type = area_reinf.Document.GetElement(param_value)
            if bar_type:
                bar_types.append(bar_type)

    return bar_types


def get_parameter_value_safe(element, param_name):
    """Safe parameter value getter"""
    try:
        param = element.LookupParameter(param_name)
        if param and not param.IsReadOnly:
            if param.StorageType == StorageType.String:
                return param.AsString()
            elif param.StorageType == StorageType.Integer:
                return param.AsInteger()
            elif param.StorageType == StorageType.Double:
                return param.AsDouble()
            elif param.StorageType == StorageType.ElementId:
                return param.AsElementId()
    except:
        pass
    return None


def set_parameter_value_safe(element, param_name, value):
    """Safe parameter value setter"""
    try:
        param = element.LookupParameter(param_name)
        if param and not param.IsReadOnly:
            if param.StorageType == StorageType.String and isinstance(value, str):
                param.Set(value)
                return True
            elif param.StorageType == StorageType.Integer and isinstance(value, int):
                param.Set(value)
                return True
            elif param.StorageType == StorageType.Double and isinstance(value, (int, float)):
                param.Set(float(value))
                return True
            elif param.StorageType == StorageType.ElementId and isinstance(value, ElementId):
                param.Set(value)
                return True
    except:
        pass
    return False


# ============================================================================
# GEOMETRY CONVERSION UTILITIES
# ============================================================================

def get_filled_region_boundary(filled_region, view):
    """Get boundary curves from Filled Region"""
    curves = []
    try:
        boundary_segments = filled_region.GetBoundaries()
        for curve_loop in boundary_segments:
            for curve in curve_loop:
                curves.append(curve)
    except Exception as e:
        print("Error getting boundary: {}".format(str(e)))
    return curves


def convert_view_to_model_coordinates(curves, view):
    """Convert curves to model coordinates"""
    model_curves = []
    view_plane = view.SketchPlane.GetPlane() if hasattr(view, 'SketchPlane') and view.SketchPlane else None
    z_elevation = view_plane.Origin.Z if view_plane else 0

    for curve in curves:
        try:
            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            new_start = XYZ(start.X, start.Y, z_elevation)
            new_end = XYZ(end.X, end.Y, z_elevation)

            if isinstance(curve, Line):
                new_curve = Line.CreateBound(new_start, new_end)
            elif isinstance(curve, Arc):
                mid = curve.Evaluate(0.5, True)
                new_mid = XYZ(mid.X, mid.Y, z_elevation)
                new_curve = Arc.Create(new_start, new_end, new_mid)
            else:
                new_curve = curve.CreateTransformed(Transform.Identity)

            model_curves.append(new_curve)
        except Exception as e:
            print("Error converting curve: {}".format(str(e)))
            model_curves.append(curve)

    return model_curves


# ============================================================================
# AREA REINFORCEMENT CREATION - FIXED
# ============================================================================

def create_area_reinforcement_safe(doc, boundary_curves, host_element, major_direction=None,
                                     area_reinforcement_type=None, rebar_bar_type=None,
                                     hook_type_id=None, logger=None):
    """
    Create Area Reinforcement with comprehensive validation and error handling.
    FIXED: Auto-detect correct API signature
    DEBUG MODE: Detailed logging to identify creation failures
    """
    # Input validation with logging
    if not doc:
        safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: doc is None")
        return None

    if not boundary_curves:
        safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: boundary_curves is None")
        return None

    if not host_element:
        safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: host_element is None")
        return None

    if len(boundary_curves) == 0:
        safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: boundary_curves is empty")
        return None

    safe_logger_call(logger, 'info', "✅ Input validation passed - doc: {}, curves: {}, host: {}".format(
        "Valid" if doc else "Invalid",
        len(boundary_curves),
        host_element.Name if hasattr(host_element, 'Name') else str(type(host_element))))

    try:
        # Validate host with logging
        if not (isinstance(host_element, Floor) or
                isinstance(host_element, WallFoundation) or
                isinstance(host_element, Foundation)):
            safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: Invalid host type - {}".format(type(host_element)))
            return None

        safe_logger_call(logger, 'info', "✅ Host validation passed - {}".format(host_element.Name))

        # Get types with logging
        art = area_reinforcement_type or get_default_area_reinforcement_type(doc)
        if not art:
            safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: No AreaReinforcementType found")
            return None

        safe_logger_call(logger, 'info', "✅ AreaReinforcementType found - ID: {}".format(art.Id))

        # Set default direction if not provided
        if not major_direction:
            major_direction = XYZ(1, 0, 0)  # Default X direction

        # Set default hook type
        if not hook_type_id:
            hook_type_id = ElementId.InvalidElementId

        safe_logger_call(logger, 'info', "🔧 Calling create_area_reinforcement_with_transaction...")

        # CRITICAL FIX: Prepare curves correctly
        # Don't prepare as List[Curve] yet - pass raw curves
        result = create_area_reinforcement_with_transaction(
            doc, host_element, boundary_curves, major_direction,
            art.Id, hook_type_id, logger=logger
        )

        if result:
            safe_logger_call(logger, 'info', "✅ Area Reinforcement created successfully - ID: {}".format(result.Id))
        else:
            safe_logger_call(logger, 'error', "❌ create_area_reinforcement_with_transaction returned None")

        return result

    except Exception as e:
        safe_logger_call(logger, 'error', "❌ create_area_reinforcement_safe: Exception - {}".format(str(e)))
        return None


def prepare_boundary_curves(curves):
    """Prepare boundary curves for Area Reinforcement creation"""
    try:
        from System.Collections.Generic import List
        curve_list = List[Curve]()
        for curve in curves:
            curve_list.Add(curve)
        return curve_list
    except Exception as e:
        safe_logger_call(logger, 'error', "Error preparing curves: {}".format(str(e)))
        return None


def get_default_rebar_bar_type(doc):
    """
    Get the first available RebarBarType from the document.
    Required for Revit 2025 API.
    """
    try:
        collector = FilteredElementCollector(doc).OfClass(RebarBarType)
        types = collector.ToElements()
        return types[0] if types else None
    except Exception:
        return None


def get_default_area_reinforcement_type(doc):
    """Get default AreaReinforcementType"""
    collector = FilteredElementCollector(doc).OfClass(AreaReinforcementType)
    types = collector.ToElements()
    return types[0] if types else None


def create_area_reinforcement_with_transaction(doc, host, boundary_curves, direction, art_id, hook_id, logger=None):
    """
    Create Area Reinforcement - DEBUG MODE
    Detailed logging to identify creation failures
    """
    try:
        safe_logger_call(logger, 'info', "🔧 Preparing curves for Area Reinforcement creation...")

        # Prepare curves as IList<Curve>
        from System.Collections.Generic import List
        curve_list = List[Curve]()
        for i, curve in enumerate(boundary_curves):
            curve_list.Add(curve)
            safe_logger_call(logger, 'info', "  • Curve {}: {} - Length: {:.2f}".format(
                i+1, type(curve).__name__,
                curve.Length if hasattr(curve, 'Length') else 'N/A'))

        safe_logger_call(logger, 'info', "✅ Prepared {} curves".format(len(boundary_curves)))

        # Get default RebarBarType if not provided
        default_rbt = get_default_rebar_bar_type(doc)
        rbt_id = default_rbt.Id if default_rbt else ElementId.InvalidElementId
        # Get RebarBarType name using proper parameter access (LOG-UTIL-REBAR-005 pattern)
        rbt_name = "InvalidElementId"
        if default_rbt:
            try:
                type_name_param = default_rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.AsString():
                    rbt_name = type_name_param.AsString()
                else:
                    rbt_name = getattr(default_rbt, 'Name', 'Unnamed')
            except:
                rbt_name = "Error accessing name"
        
        safe_logger_call(logger, 'info', "🔧 RebarBarType: {}".format(rbt_name))

        # NO TRANSACTION MANAGEMENT - ASSUMES EXISTING TRANSACTION
        safe_logger_call(logger, 'info', "🔧 Calling AreaReinforcement.Create (assumes existing transaction)...")
        safe_logger_call(logger, 'info', "🏗️ Calling AreaReinforcement.Create with parameters:")
        safe_logger_call(logger, 'info', "  • Document: {}".format("Valid" if doc else "Invalid"))
        safe_logger_call(logger, 'info', "  • Host: {} (ID: {})".format(
            host.Name if hasattr(host, 'Name') else str(type(host)), host.Id))
        safe_logger_call(logger, 'info', "  • Curves: {} curves".format(len(curve_list)))
        safe_logger_call(logger, 'info', "  • Direction: ({:.2f}, {:.2f}, {:.2f})".format(
            direction.X, direction.Y, direction.Z))
        safe_logger_call(logger, 'info', "  • ART ID: {}".format(art_id))
        safe_logger_call(logger, 'info', "  • RBT ID: {}".format(rbt_id))
        safe_logger_call(logger, 'info', "  • Hook ID: {}".format(hook_id))

        # WORKING METHOD: curves before direction (Revit 2025 compatible)
        area_reinf = AreaReinforcement.Create(
            doc,           # Document
            host,          # Element (Floor/Foundation)
            curve_list,    # IList<Curve> - CURVES COME FIRST!
            direction,     # XYZ - DIRECTION COMES AFTER CURVES!
            art_id,        # ElementId (AreaReinforcementType)
            rbt_id,        # ElementId (RebarBarType)
            hook_id        # ElementId (HookType)
        )

        if area_reinf:
            safe_logger_call(logger, 'info', "✅ AreaReinforcement.Create returned valid element - ID: {}".format(area_reinf.Id))
            safe_logger_call(logger, 'info', "✅ Area Reinforcement created successfully")
            return area_reinf
        else:
            safe_logger_call(logger, 'error', "❌ AreaReinforcement.Create returned None")
            return None

    except Exception as e:
        safe_logger_call(logger, 'error', "❌ Exception in create_area_reinforcement_with_transaction: {}".format(str(e)))
        return None


# ============================================================================
# PARAMETER OVERRIDE FRAMEWORK
# ============================================================================

def override_area_reinforcement_parameters(area_reinforcement, parameter_overrides=None, logger=None):
    """
    Override Area Reinforcement parameters with automatic unit conversion and validation.
    SILENT MODE: No logging during override - return results only
    """
    if not area_reinforcement:
        return {'success': False, 'message': 'Invalid element', 'overrides': []}

    # Default parameter overrides - FIXED parameter names
    default_overrides = {
        'Layout Rule': 3,  # Maximum Spacing
    }

    # Merge with provided overrides
    overrides = default_overrides.copy()
    if parameter_overrides:
        overrides.update(parameter_overrides)

    results = {
        'success': True,
        'message': 'Parameter override completed',
        'overrides': []
    }

    try:
        # Apply each parameter override - DEBUG MODE
        for param_name, value in overrides.items():
            safe_logger_call(logger, 'debug', "🔧 OVERRIDE: Setting parameter '{}' = {}".format(param_name, value))
            success = apply_parameter_override(area_reinforcement, param_name, value, logger=logger)  # DEBUG
            results['overrides'].append({
                'parameter': param_name,
                'value': value,
                'success': success
            })

            if not success:
                results['success'] = False
                results['message'] = 'Some parameter overrides failed'

    except Exception as e:
        results['success'] = False
        results['message'] = 'Error during parameter override: {}'.format(str(e))

    return results


def apply_parameter_override(area_reinforcement, param_name, value, logger=None):
    """Apply single parameter override with proper type conversion - SILENT MODE"""
    try:
        # Handle special parameter conversions
        converted_value = convert_parameter_value(param_name, value, logger=logger)  # DEBUG

        # Try to set on instance first
        success = set_parameter_value_safe(area_reinforcement, param_name, converted_value)

        if success:
            return True

        # If instance setting failed, try on type
        area_reinforcement_type_id = area_reinforcement.GetTypeId()
        art_element = area_reinforcement.Document.GetElement(area_reinforcement_type_id)

        success = set_parameter_value_safe(art_element, param_name, converted_value)

        if success:
            return True

        return False

    except Exception as e:
        return False


def convert_parameter_value(param_name, value, logger=None):
    """Convert parameter values based on parameter type and units - SILENT MODE"""
    # Layout Rule - should be integer
    if param_name == "Layout Rule":
        if isinstance(value, str):
            layout_rules = {
                "Maximum Spacing": 3,
                "Number with Spacing": 2,
                "Fixed Number": 1,
                "Minimum Clear Spacing": 0
            }
            return layout_rules.get(value, int(value))
        return int(value)

    # Spacing parameters - KEEP IN MM (Revit accepts mm directly)
    elif "Spacing" in param_name:
        if isinstance(value, (int, float)):
            safe_logger_call(logger, 'debug', "🔍 SPACING VALUE:")
            safe_logger_call(logger, 'debug', "  • Parameter: '{}'".format(param_name))
            safe_logger_call(logger, 'debug', "  • UI value: {:.2f}".format(value))
            safe_logger_call(logger, 'debug', "  • Using directly (no conversion)")
            return value
        return value

    # Cover offset parameters - convert mm to feet (these need feet)
    elif "Cover Offset" in param_name:
        if isinstance(value, (int, float)):
            feet_value = value / 304.8
            safe_logger_call(logger, 'debug', "🔍 COVER OFFSET VALUE:")
            safe_logger_call(logger, 'debug', "  • Parameter: '{}'".format(param_name))
            safe_logger_call(logger, 'debug', "  • mm value: {:.2f}".format(value))
            safe_logger_call(logger, 'debug', "  • feet value: {:.4f}".format(feet_value))
            return feet_value
        return value

    # Other parameters - return as-is
    return value


# ============================================================================
# MULTI LAYER SETTINGS PROCESSOR
# ============================================================================

def process_multi_layer_area_reinforcement(doc, processor_input, logger=None):
    """
    Process multi layer area reinforcement dari UI settings.
    FIXED: Transaction separation - create AR elements first, then override parameters in separate transaction
    """
    # DEBUG: Log input received
    safe_logger_call(logger, 'info', "=== DEBUG: process_multi_layer_area_reinforcement called ===")
    safe_logger_call(logger, 'info', "processor_input keys: {}".format(list(processor_input.keys()) if processor_input else "None"))
    safe_logger_call(logger, 'info', "major_direction: {}".format(processor_input.get("major_direction") if processor_input else "None"))
    safe_logger_call(logger, 'info', "ui_settings count: {}".format(len(processor_input.get("ui_settings", [])) if processor_input else "None"))
    safe_logger_call(logger, 'info', "boundary_curves count: {}".format(len(processor_input.get("boundary_curves", [])) if processor_input and processor_input.get("boundary_curves") else "None"))
    safe_logger_call(logger, 'info', "host: {}".format(processor_input.get("host").Name if processor_input and processor_input.get("host") else "None"))
    safe_logger_call(logger, 'info', "=====================================")

    major_direction = processor_input.get("major_direction", "Y")
    ui_settings = processor_input.get("ui_settings", [])

    # Convert major direction to XYZ
    direction_vector = XYZ(1, 0, 0) if major_direction == "X" else XYZ(0, 1, 0)

    # Validate input
    validation_errors = validate_processor_input(processor_input)
    if validation_errors:
        error_msg = "Validation errors:\n" + "\n".join(validation_errors)
        safe_logger_call(logger, 'error', error_msg)
        raise ValueError(error_msg)

    # Group layers untuk adaptive AR creation
    layer_groups = group_layers_for_adaptive_ar_creation(ui_settings)

    # ============================================================================
    # PHASE 1: CREATE ALL AR ELEMENTS (Transaction 1)
    # ============================================================================
    safe_logger_call(logger, 'info', "🏗️ **PHASE 1: Creating Area Reinforcement Elements**")

    t_create = Transaction(doc, "Create Multi-Layer Area Reinforcement Elements")
    t_create.Start()

    try:
        # COLLECT ALL RESULTS - CREATE AR ELEMENTS ONLY
        all_results = []

        # AR 1: Bottom Primary Layers (always created if bottom layers exist)
        if layer_groups['bottom_primary']:
            safe_logger_call(logger, 'info', "🔧 Creating AR 1: Bottom Primary Layers ({})".format(
                len(layer_groups['bottom_primary'])))

            area_reinf = create_area_reinforcement_safe(
                doc, processor_input["boundary_curves"], processor_input["host"],
                major_direction=direction_vector, logger=None  # SILENT DURING CREATION
            )

            if area_reinf:
                safe_logger_call(logger, 'info', "✅ AR 1 created successfully - ID: {}".format(area_reinf.Id))
                all_results.append({
                    'area_reinforcement': area_reinf,
                    'layer_group': layer_groups['bottom_primary'],
                    'ar_type': 'bottom_primary',
                    'cover_offset': {}  # No cover offset for primary
                })
            else:
                safe_logger_call(logger, 'error', "❌ Failed to create AR 1 (Bottom Primary)")

        # AR 2: Bottom Additional Layers (only if enabled and layers selected)
        if layer_groups['bottom_additional']:
            safe_logger_call(logger, 'info', "🔧 Creating AR 2: Bottom Additional Layers ({})".format(
                len(layer_groups['bottom_additional'])))

            area_reinf = create_area_reinforcement_safe(
                doc, processor_input["boundary_curves"], processor_input["host"],
                major_direction=direction_vector, logger=None  # SILENT DURING CREATION
            )

            if area_reinf:
                safe_logger_call(logger, 'info', "✅ AR 2 created successfully - ID: {}".format(area_reinf.Id))
                # Calculate cover offset from AR 1
                cover_offset = calculate_cover_offset_from_previous_ar(
                    next((r['area_reinforcement'] for r in all_results if r['ar_type'] == 'bottom_primary'), None)
                )
                all_results.append({
                    'area_reinforcement': area_reinf,
                    'layer_group': layer_groups['bottom_additional'],
                    'ar_type': 'bottom_additional',
                    'cover_offset': cover_offset
                })
            else:
                safe_logger_call(logger, 'error', "❌ Failed to create AR 2 (Bottom Additional)")

        # AR 3: Top Primary Layers (always created if top layers exist)
        if layer_groups['top_primary']:
            safe_logger_call(logger, 'info', "🔧 Creating AR 3: Top Primary Layers ({})".format(
                len(layer_groups['top_primary'])))

            area_reinf = create_area_reinforcement_safe(
                doc, processor_input["boundary_curves"], processor_input["host"],
                major_direction=direction_vector, logger=None  # SILENT DURING CREATION
            )

            if area_reinf:
                safe_logger_call(logger, 'info', "✅ AR 3 created successfully - ID: {}".format(area_reinf.Id))
                all_results.append({
                    'area_reinforcement': area_reinf,
                    'layer_group': layer_groups['top_primary'],
                    'ar_type': 'top_primary',
                    'cover_offset': {}  # No cover offset for primary
                })
            else:
                safe_logger_call(logger, 'error', "❌ Failed to create AR 3 (Top Primary)")

        # AR 4: Top Additional Layers (only if enabled and layers selected)
        if layer_groups['top_additional']:
            safe_logger_call(logger, 'info', "🔧 Creating AR 4: Top Additional Layers ({})".format(
                len(layer_groups['top_additional'])))

            area_reinf = create_area_reinforcement_safe(
                doc, processor_input["boundary_curves"], processor_input["host"],
                major_direction=direction_vector, logger=None  # SILENT DURING CREATION
            )

            if area_reinf:
                safe_logger_call(logger, 'info', "✅ AR 4 created successfully - ID: {}".format(area_reinf.Id))
                # Calculate cover offset from AR 3
                cover_offset = calculate_cover_offset_from_previous_ar(
                    next((r['area_reinforcement'] for r in all_results if r['ar_type'] == 'top_primary'), None)
                )
                all_results.append({
                    'area_reinforcement': area_reinf,
                    'layer_group': layer_groups['top_additional'],
                    'ar_type': 'top_additional',
                    'cover_offset': cover_offset
                })
            else:
                safe_logger_call(logger, 'error', "❌ Failed to create AR 4 (Top Additional)")

        # COMMIT CREATION TRANSACTION
        safe_logger_call(logger, 'info', "💾 **Committing AR creation transaction...**")
        t_create.Commit()
        safe_logger_call(logger, 'info', "✅ **Phase 1 Complete: {} AR elements created**".format(len(all_results)))

    except Exception as e:
        if t_create.HasStarted() and t_create.GetStatus() == TransactionStatus.Started:
            t_create.RollBack()
            safe_logger_call(logger, 'error', "❌ **Phase 1 Failed: AR creation rolled back**")
        raise e

    # ============================================================================
    # PHASE 2: OVERRIDE PARAMETERS (Separate Transaction)
    # ============================================================================
    safe_logger_call(logger, 'info', "⚙️ **PHASE 2: Overriding Parameters**")

    t_override = Transaction(doc, "Override Multi-Layer Area Reinforcement Parameters")
    t_override.Start()

    try:
        # OVERRIDE PARAMETERS IN SEPARATE TRANSACTION
        for result in all_results:
            area_reinf = result['area_reinforcement']
            layer_group = result['layer_group']
            cover_offset = result.get('cover_offset', {})

            # Process layer group menjadi parameter overrides
            parameter_overrides = process_layer_group_to_overrides(doc, layer_group, logger=None)  # SILENT

            # Add cover offset
            if cover_offset:
                parameter_overrides.update(cover_offset)

            # OVERRIDE PARAMETERS IN SEPARATE TRANSACTION
            override_results = override_area_reinforcement_parameters(area_reinf, parameter_overrides, logger=None)  # SILENT
            result['override_results'] = override_results

        # COMMIT OVERRIDE TRANSACTION
        safe_logger_call(logger, 'info', "💾 **Committing parameter override transaction...**")
        t_override.Commit()
        safe_logger_call(logger, 'info', "✅ **Phase 2 Complete: Parameters overridden**")

    except Exception as e:
        if t_override.HasStarted() and t_override.GetStatus() == TransactionStatus.Started:
            t_override.RollBack()
            safe_logger_call(logger, 'error', "❌ **Phase 2 Failed: Parameter override rolled back**")
        raise e

    # ============================================================================
    # PHASE 3: FINAL SUMMARY
    # ============================================================================
    safe_logger_call(logger, 'info', "## ⚙️ **Processing Multi Layer Settings...**")
    safe_logger_call(logger, 'info', "\n## 📊 **Multi-Layer Processing Summary**")
    safe_logger_call(logger, 'info', "---")
    safe_logger_call(logger, 'info', "Created **{}** Area Reinforcement elements".format(len(all_results)))

    for i, result in enumerate(all_results, 1):
        area_reinf = result['area_reinforcement']
        layer_group = result['layer_group']
        override_results = result['override_results']

        layer_names = [layer.get('layer_id', 'Unknown') for layer in layer_group]
        safe_logger_call(logger, 'info', "• AR {}: ID {} - Layers: {}".format(
            i, area_reinf.Id, ", ".join(layer_names)))

        # Log override results with DETAILS
        successful_overrides = [o for o in override_results['overrides'] if o['success']]
        failed_overrides = [o for o in override_results['overrides'] if not o['success']]

        if successful_overrides:
            safe_logger_call(logger, 'info', "  ✓ {} parameters set successfully".format(len(successful_overrides)))
        if failed_overrides:
            safe_logger_call(logger, 'warning', "  ⚠️ {} parameters failed:".format(len(failed_overrides)))
            for failed in failed_overrides:
                safe_logger_call(logger, 'warning', "    - {} (value: {})".format(failed['parameter'], failed['value']))

    safe_logger_call(logger, 'info', "\n💾 **All changes saved successfully!**")

    # EXTRACT ELEMENTS FOR RETURN
    created_elements = [result['area_reinforcement'] for result in all_results]

    return created_elements


def validate_processor_input(processor_input):
    """Validate processor input structure"""
    errors = []

    required_keys = ["major_direction", "boundary_curves", "host", "ui_settings"]
    for key in required_keys:
        if key not in processor_input:
            errors.append("Missing required key: {}".format(key))

    major_direction = processor_input.get("major_direction")
    if major_direction and major_direction not in ["X", "Y"]:
        errors.append("major_direction must be 'X' or 'Y'")

    ui_settings = processor_input.get("ui_settings", [])
    if not isinstance(ui_settings, list):
        errors.append("ui_settings must be a list")

    # Validate each layer config
    for i, layer_config in enumerate(ui_settings):
        if not isinstance(layer_config, dict):
            errors.append("ui_settings[{}] must be a dictionary".format(i))
            continue

        required_layer_keys = ["layer_id", "enabled"]
        for key in required_layer_keys:
            if key not in layer_config:
                errors.append("Layer {} missing required key: {}".format(i, key))

        layer_id = layer_config.get("layer_id")
        if layer_id and layer_id not in ["Bottom Major", "Bottom Minor", "Top Major", "Top Minor",
                                        "Bottom Major Additional", "Bottom Minor Additional",
                                        "Top Major Additional", "Top Minor Additional"]:
            errors.append("Invalid layer_id '{}' in layer {}".format(layer_id, i))

        enabled = layer_config.get("enabled", False)
        if not isinstance(enabled, bool):
            errors.append("'enabled' must be boolean in layer {}".format(i))

        if enabled:
            bar_type_name = layer_config.get("bar_type_name")
            if not bar_type_name or not isinstance(bar_type_name, str):
                errors.append("bar_type_name required for enabled layer {}".format(i))

            spacing = layer_config.get("spacing")
            if spacing is not None and not isinstance(spacing, (int, float)):
                errors.append("spacing must be number in layer {}".format(i))

    return errors


def separate_top_bottom_layers(ui_settings):
    """Separate layers menjadi top dan bottom groups dengan support untuk additional layers"""
    top_layers = []
    bottom_layers = []

    for layer in ui_settings:
        layer_id = layer.get("layer_id", "")
        if layer_id.startswith("Top"):
            top_layers.append(layer)
        elif layer_id.startswith("Bottom"):
            bottom_layers.append(layer)

    # Sort by priority within each group (Major first, then Minor)
    LAYER_PRIORITY = {
        "Bottom Major": 1, "Top Major": 1,
        "Bottom Minor": 2, "Top Minor": 2,
        "Bottom Major Additional": 3, "Top Major Additional": 3,
        "Bottom Minor Additional": 4, "Top Minor Additional": 4
    }

    top_layers.sort(key=lambda x: LAYER_PRIORITY.get(x.get("layer_id"), 999))
    bottom_layers.sort(key=lambda x: LAYER_PRIORITY.get(x.get("layer_id"), 999))

    return {"top": top_layers, "bottom": bottom_layers}


def group_layers_for_adaptive_ar_creation(ui_settings):
    """
    Group layers untuk adaptive AR creation dengan support additional layers.
    Returns structured groups untuk conditional AR creation.
    """
    # Separate by side
    separated = separate_top_bottom_layers(ui_settings)

    # Group by primary vs additional
    groups = {
        'bottom_primary': [l for l in separated['bottom'] if not l.get('layer_id', '').endswith('Additional')],
        'bottom_additional': [l for l in separated['bottom'] if l.get('layer_id', '').endswith('Additional')],
        'top_primary': [l for l in separated['top'] if not l.get('layer_id', '').endswith('Additional')],
        'top_additional': [l for l in separated['top'] if l.get('layer_id', '').endswith('Additional')]
    }

    # Validate groupings
    for group_name, layers in groups.items():
        if len(layers) > 2:
            raise ValueError("Group {} cannot have more than 2 layers (Revit limitation)".format(group_name))

    return groups


def group_layers_by_side_and_count(layer_list, max_per_group=2):
    """Group layers dalam satu side by count"""
    groups = []
    for i in range(0, len(layer_list), max_per_group):
        group = layer_list[i:i+max_per_group]
        groups.append(group)
    return groups


def calculate_cover_offset_from_previous_ar(previous_ar, logger=None):
    """
    Calculate cover offset dari previous AR element berdasarkan max bar diameter.
    Returns parameter override dict untuk cover offset.
    """
    if not previous_ar:
        safe_logger_call(logger, 'debug', "No previous AR found for cover offset calculation")
        return {}

    # Get max diameter dari previous AR
    max_diameter_mm = get_max_bar_diameter_from_area_reinforcement(previous_ar)
    if max_diameter_mm <= 0:
        safe_logger_call(logger, 'warning', "Invalid max diameter from previous AR: {}".format(max_diameter_mm))
        return {}

    # Convert to feet
    offset_feet = max_diameter_mm / 304.8

    safe_logger_call(logger, 'info', "Calculated cover offset: {}mm = {:.4f}ft from AR ID {}".format(
        max_diameter_mm, offset_feet, previous_ar.Id))

    # Determine offset type based on AR type
    if is_bottom_area_reinforcement(previous_ar):
        return {"Additional Bottom Cover Offset": offset_feet}
    elif is_top_area_reinforcement(previous_ar):
        return {"Additional Top Cover Offset": offset_feet}
    else:
        safe_logger_call(logger, 'warning', "Cannot determine AR type for cover offset")
        return {}


def is_bottom_area_reinforcement(area_reinf):
    """Check if Area Reinforcement memiliki bottom layers enabled"""
    # Check visibility parameters
    bottom_major_visible = get_parameter_value_safe(area_reinf, "Bottom/Interior Major Direction")
    bottom_minor_visible = get_parameter_value_safe(area_reinf, "Bottom/Interior Minor Direction")

    return (bottom_major_visible == 1) or (bottom_minor_visible == 1)


def is_top_area_reinforcement(area_reinf):
    """Check if Area Reinforcement memiliki top layers enabled"""
    # Check visibility parameters
    top_major_visible = get_parameter_value_safe(area_reinf, "Top/Exterior Major Direction")
    top_minor_visible = get_parameter_value_safe(area_reinf, "Top/Exterior Minor Direction")

    return (top_major_visible == 1) or (top_minor_visible == 1)


# REMOVED: create_area_reinforcement_with_layer_group function
# Parameter override now handled inside main transaction in process_multi_layer_area_reinforcement


def process_layer_group_to_overrides(doc, layer_group, logger=None):
    """Convert layer group menjadi parameter overrides dictionary - FIXED VISIBILITY ORDER"""
    overrides = {
        "Layout Rule": 3,  # Maximum Spacing

        # Default: semua disabled - CORRECT FOR REVIT
        "Bottom/Interior Minor Direction": 0,
        "Bottom/Interior Major Direction": 0,
        "Top/Exterior Minor Direction": 0,
        "Top/Exterior Major Direction": 0
    }

    # FIRST PASS: Enable visibility for ALL layers in group
    for layer_config in layer_group:
        layer_id = layer_config.get("layer_id")
        # Enable visibility FIRST - ONLY FOR ACTIVE LAYERS
        visibility_param = get_visibility_parameter_name(layer_id)
        overrides[visibility_param] = 1

    # SECOND PASS: Set bar types and spacing AFTER visibility is enabled
    for layer_config in layer_group:
        layer_id = layer_config.get("layer_id")

        # Set bar type
        bar_type_name = layer_config.get("bar_type_name")
        if bar_type_name:
            bar_type_id = find_rebar_bar_type_by_name(doc, bar_type_name)
            if bar_type_id:
                bar_type_param = get_bar_type_parameter_name(layer_id)
                overrides[bar_type_param] = bar_type_id

        # Set spacing (KEEP IN MM - Revit accepts mm directly)
        spacing_mm = layer_config.get("spacing")
        if spacing_mm:
            # USE SHORT NAMES: "Top Major Spacing" instead of "Top/Exterior Major Spacing"
            short_spacing_param = get_short_spacing_parameter_name(layer_id)
            overrides[short_spacing_param] = spacing_mm  # NO CONVERSION - Keep in mm

    return overrides


def get_visibility_parameter_name(layer_id):
    """Get visibility parameter name untuk layer"""
    visibility_map = {
        "Bottom Major": "Bottom/Interior Major Direction",
        "Bottom Minor": "Bottom/Interior Minor Direction",
        "Top Major": "Top/Exterior Major Direction",
        "Top Minor": "Top/Exterior Minor Direction"
    }
    return visibility_map.get(layer_id)


def get_bar_type_parameter_name(layer_id):
    """Get bar type parameter name untuk layer - USE FULL NAMES"""
    bar_type_map = {
        "Bottom Major": "Bottom/Interior Major Bar Type",
        "Bottom Minor": "Bottom/Interior Minor Bar Type",
        "Top Major": "Top/Exterior Major Bar Type",
        "Top Minor": "Top/Exterior Minor Bar Type",
        # Additional layers use same parameter names as primary
        "Bottom Major Additional": "Bottom/Interior Major Bar Type",
        "Bottom Minor Additional": "Bottom/Interior Minor Bar Type",
        "Top Major Additional": "Top/Exterior Major Bar Type",
        "Top Minor Additional": "Top/Exterior Minor Bar Type"
    }
    return bar_type_map.get(layer_id)


def get_spacing_parameter_name(layer_id):
    """Get spacing parameter name untuk layer - FULL NAMES"""
    spacing_map = {
        "Bottom Major": "Bottom/Interior Major Spacing",
        "Bottom Minor": "Bottom/Interior Minor Spacing",
        "Top Major": "Top/Exterior Major Spacing",
        "Top Minor": "Top/Exterior Minor Spacing"
    }
    return spacing_map.get(layer_id)


def get_short_spacing_parameter_name(layer_id):
    """Get FULL spacing parameter name - use full names that actually work in Revit"""
    # Use FULL names as discovered from parameter inspection
    spacing_map = {
        "Bottom Major": "Bottom/Interior Major Spacing",
        "Bottom Minor": "Bottom/Interior Minor Spacing",
        "Top Major": "Top/Exterior Major Spacing",
        "Top Minor": "Top/Exterior Minor Spacing",
        # Additional layers use same parameter names as primary
        "Bottom Major Additional": "Bottom/Interior Major Spacing",
        "Bottom Minor Additional": "Bottom/Interior Minor Spacing",
        "Top Major Additional": "Top/Exterior Major Spacing",
        "Top Minor Additional": "Top/Exterior Minor Spacing"
    }
    return spacing_map.get(layer_id)