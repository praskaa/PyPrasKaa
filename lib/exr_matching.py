# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: 3-pass geometric matching for EXR validation tools
# Version: 1.1

from Autodesk.Revit.DB import BooleanOperationsUtils, BooleanOperationsType, SolidUtils, XYZ
from exr_dimensions import get_geometry_type, compare_dimensions, get_dimensions

# Solid expansion tolerance ~6 cm
INTERSECTION_TOLERANCE = 0.2

STATUS_APPROVED        = "Approved"
STATUS_DIM_MISMATCH    = "Dimension Mismatch"
STATUS_FAMILY_MISMATCH = "Family Mismatch"
STATUS_UNMATCHED       = "Unmatched"


def _expand_solid(solid, tolerance):
    """Uniformly scale a solid outward from its centroid. Used as intersection fallback."""
    try:
        from Autodesk.Revit.DB import Transform
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


def _best_by_volume(candidates, exp_host, expand_linked=False):
    """
    Single pass: find the candidate with the largest intersection volume.
    Returns (best_data dict or None, unmatched list).
    No geometry type or dimension checks here — pure spatial match only.
    """
    best_data  = None
    max_vol    = 0.0
    no_spatial = []  # candidates with zero intersection — retry next pass

    for data in candidates:
        linked_solid = data['solid']
        if not linked_solid:
            continue

        ls = _expand_solid(linked_solid, INTERSECTION_TOLERANCE) if expand_linked else linked_solid

        try:
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                exp_host, ls, BooleanOperationsType.Intersect)
            vol = inter.Volume if inter else 0.0
        except Exception:
            vol = 0.0

        if vol == 0.0:
            # No spatial overlap — candidate goes to next pass
            no_spatial.append(data)
            continue

        # Spatial overlap found — track best by volume
        if vol > max_vol:
            max_vol   = vol
            best_data = data

    return best_data, no_spatial


def find_best_match(host_elem, host_solid, linked_beams_dict, host_dims, host_geom_type):
    """
    3-pass spatial matching followed by a single validation check on the best candidate.

    Pass 1 — direct intersection
    Pass 2 — expand host solid
    Pass 3 — expand host and linked solid

    Each pass finds the spatially best candidate (largest intersection volume).
    Once ANY pass finds a spatial neighbour, validation runs immediately:
      · geometry type mismatch  → return (None, STATUS_FAMILY_MISMATCH)
      · dimension mismatch      → return (None, STATUS_DIM_MISMATCH)
      · both pass               → return (element, None)

    If all 3 passes find zero intersection → return (None, STATUS_UNMATCHED).

    This is the correct separation: expansion passes fix spatial gaps,
    not dimension problems. A column that intersects but has wrong dimensions
    returns Dimension Mismatch immediately — it does not retry with expansion.
    """
    all_candidates = list(linked_beams_dict.values())

    # Pass 1: direct
    try:
        best_data, no_spatial = _best_by_volume(all_candidates, host_solid)
    except Exception:
        best_data, no_spatial = None, all_candidates

    if best_data is None:
        # Pass 2: expand host
        try:
            exp_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
        except Exception:
            exp_host = host_solid
        try:
            best_data, no_spatial_2 = _best_by_volume(no_spatial, exp_host)
        except Exception:
            best_data, no_spatial_2 = None, no_spatial

        if best_data is None:
            # Pass 3: expand both
            try:
                best_data, _ = _best_by_volume(no_spatial_2, exp_host, expand_linked=True)
            except Exception:
                best_data = None

    # No spatial neighbour found across all passes
    if best_data is None:
        return None, STATUS_UNMATCHED

    # Spatial neighbour found — validate geometry type and dimensions once
    linked_elem      = best_data['element']
    linked_geom_type = get_geometry_type(linked_elem)

    if host_geom_type != linked_geom_type:
        return None, STATUS_FAMILY_MISMATCH

    linked_dims = get_dimensions(linked_elem)
    if not compare_dimensions(host_dims, linked_dims):
        return None, STATUS_DIM_MISMATCH

    return linked_elem, None