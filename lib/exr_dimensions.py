# -*- coding: utf-8 -*-
"""
EXR Dimension extraction, comparison, and geometry type detection.

Unified for columns and framing (beams). Category-agnostic.
"""

from Autodesk.Revit.DB import (
    BuiltInParameter,
    StorageType,
)


def _feet_to_mm(v):
    """Convert internal feet to mm. Module-level to avoid repeated imports."""
    try:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
        return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)
    except (ImportError, AttributeError):
        return v * 304.8


def get_dimensions(element):
    """
    Unified dimension extraction for columns or framing.
    Returns {'b': float, 'h': float, 'diameter': float or None, 'type': str} or None.
    Type: 'rectangular' | 'square' | 'circular' | 'unknown'
    """
    try:
        def _lookup(elem, names):
            for name in names:
                try:
                    p = elem.LookupParameter(name)
                    if p and p.HasValue and p.StorageType == StorageType.Double:
                        return p.AsDouble()
                except:
                    continue
            return None

        b_param_names = ['b', 'B', 'Width', 'width', 'w', 'W', 'd', 'Depth', 'depth', 'Section Width', 'web_width']
        h_param_names = ['h', 'H', 'Height', 'height', 'd', 'Depth', 'depth', 'Section Depth', 'flange_width', 'total_depth']
        d_param_names = ['Diameter', 'diameter', 'D', 'd', 'dia', 'Dia']

        # BuiltIn first
        b_val = element.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        b_val = b_val.AsDouble() if (b_val and b_val.HasValue) else None
        if b_val is None:
            b_val = _lookup(element, b_param_names)
            if b_val is None and hasattr(element, 'Symbol') and element.Symbol:
                b_val = _lookup(element.Symbol, b_param_names)

        h_val = element.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        h_val = h_val.AsDouble() if (h_val and h_val.HasValue) else None
        if h_val is None:
            h_val = _lookup(element, h_param_names)
            if h_val is None and hasattr(element, 'Symbol') and element.Symbol:
                h_val = _lookup(element.Symbol, h_param_names)

        dia_val = element.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_DIAMETER)
        dia_val = dia_val.AsDouble() if (dia_val and dia_val.HasValue) else None
        if dia_val is None:
            dia_val = _lookup(element, d_param_names)
            if dia_val is None and hasattr(element, 'Symbol') and element.Symbol:
                dia_val = _lookup(element.Symbol, d_param_names)

        if dia_val is not None:
            return {'b': None, 'h': None, 'diameter': dia_val, 'type': 'circular'}

        if b_val is not None and h_val is None:
            h_val = b_val
        if b_val is not None and h_val is not None:
            if abs(b_val - h_val) < 1e-6:
                return {'b': b_val, 'h': b_val, 'diameter': None, 'type': 'square'}
            return {'b': b_val, 'h': h_val, 'diameter': None, 'type': 'rectangular'}
        if b_val is not None:
            return {'b': b_val, 'h': b_val, 'diameter': None, 'type': 'square'}
        return None

    except Exception:
        return None


def compare_dimensions(host_dims, linked_dims):
    """Framing version: tolerance 0.01 mm, type check first."""
    if not host_dims or not linked_dims:
        return False
    if host_dims.get('type') != linked_dims.get('type'):
        return False

    tol = 0.01

    if host_dims['type'] == 'circular':
        hd = host_dims.get('diameter')
        ld = linked_dims.get('diameter')
        if hd is None or ld is None:
            return False
        return abs(_feet_to_mm(hd) - _feet_to_mm(ld)) <= tol

    if host_dims['type'] == 'square':
        hb = host_dims.get('b')
        lb = linked_dims.get('b')
        if hb is None or lb is None:
            return False
        return abs(_feet_to_mm(hb) - _feet_to_mm(lb)) <= tol

    if host_dims['type'] == 'rectangular':
        hb, hh = host_dims.get('b'), host_dims.get('h')
        lb, lh = linked_dims.get('b'), linked_dims.get('h')
        if None in [hb, hh, lb, lh]:
            return False
        return (abs(_feet_to_mm(hb) - _feet_to_mm(lb)) <= tol and
                abs(_feet_to_mm(hh) - _feet_to_mm(lh)) <= tol)

    return False


def get_geometry_type(element):
    """Framing version using SYMBOL_NAME_PARAM (safer than .Name)."""
    try:
        type_id = element.GetTypeId()
        btype = element.Document.GetElement(type_id)
        family_name = ''
        type_name = ''
        if btype:
            try:
                if hasattr(btype, 'Family') and btype.Family:
                    family_name = str(btype.Family.Name).lower()
            except Exception:
                pass
            try:
                p = btype.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                type_name = str(p.AsString()).lower() if (p and p.HasValue) else ''
            except Exception:
                pass
    except Exception:
        family_name = ''
        type_name = ''

    combined = family_name + ' ' + type_name

    for kw in ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']:
        if kw in combined:
            return 'circular'
    for kw in ['square', 'box', 'kuadrat']:
        if kw in combined:
            return 'square'
    for kw in ['rectangular', 'rectangle', 'rect', 'persegi']:
        if kw in combined:
            return 'rectangular'

    dims = get_dimensions(element)
    if dims:
        return dims.get('type', 'unknown')
    return 'unknown'


def dims_to_mm_str(dims):
    """Framing _dims_to_mm_str renamed for CSV readability."""
    if not dims:
        return '-'
    b = _feet_to_mm(dims.get('b', 0) or 0)
    h = _feet_to_mm(dims.get('h', dims.get('b', 0) or 0))
    if dims.get('type') == 'circular':
        d = _feet_to_mm(dims.get('diameter', 0) or 0)
        return 'diameter={:.0f}mm'.format(d)
    return 'b={:.0f}mm x h={:.0f}mm'.format(b, h)
