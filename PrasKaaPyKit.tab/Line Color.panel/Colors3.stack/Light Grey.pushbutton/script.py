"""
Script Name: Color Button
Description: Override Projection Line & Pattern Color of Elements.
Author: David Vadkerti
Version: 1.0.0
Last Updated: 2026-02-19

Changelog:
    v1.0.0 (2026-02-19): Added Shift+Click for pattern-only override
"""

from graphicOverrides import setProjLines, setProjPatternOnly

__title__ = "."
__doc__ = 'Quicker override Projection Line & Pattern Color of Elements.\nShift+Click: Pattern only (no line color)'
__author__ = "David Vadkerti"

# Check for Shift+Click
if __shiftclick__:  #pylint: disable=E0602
    # Pattern only - no line colors
    setProjPatternOnly(180, 180, 180)
else:
    # Line + Pattern (default behavior)
    setProjLines(180, 180, 180, True)