# -*- coding: utf-8 -*-
"""
Cross-version compatibility shims for Revit API (2024/2025/2026 + IronPython 2.7).
"""

def get_element_id_value(eid):
    """Return integer value of ElementId. Works on all Revit versions."""
    try:
        return eid.Value          # Revit 2026+
    except AttributeError:
        return eid.IntegerValue   # Revit 2024–2025
