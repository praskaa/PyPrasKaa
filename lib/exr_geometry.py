# -*- coding: utf-8 -*-
"""
EXR Geometry utilities — category-agnostic solid extraction.

Used by CheckColumnDimensions and CheckFramingDimensions.
"""

from Autodesk.Revit.DB import (
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    GeometryInstance,
    SolidUtils,
    XYZ,
    Transform,
)


def get_solid(element, geo_opts):
    """Extract the largest united solid from an element. Handles GeometryInstance nesting."""
    geom = element.get_Geometry(geo_opts)
    if not geom:
        return None
    solids = []
    for obj in geom:
        if isinstance(obj, Solid) and obj.Volume > 0:
            solids.append(obj)
        elif isinstance(obj, GeometryInstance):
            for inst_obj in obj.GetInstanceGeometry() or []:
                if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                    solids.append(inst_obj)
    if not solids:
        return None
    result = solids[0]
    for s in solids[1:]:
        try:
            result = BooleanOperationsUtils.ExecuteBooleanOperation(
                result, s, BooleanOperationsType.Union)
        except Exception:
            pass
    return result


def _expand_solid(solid, tolerance=0.2):
    """Uniformly scale a solid outward from its centroid. Used as intersection fallback."""
    try:
        center = solid.ComputeCentroid()
        scale  = 1.0 + tolerance
        t = Transform.Identity
        t.Origin = center.Multiply(1 - scale)
        t.BasisX = XYZ(scale, 0, 0)
        t.BasisY = XYZ(0, scale, 0)
        t.BasisZ = XYZ(0, 0, scale)
        return SolidUtils.CreateTransformed(solid, t)
    except Exception:
        return solid
