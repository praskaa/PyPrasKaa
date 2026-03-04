# -*- coding: utf-8 -*-
"""
Geometry Matching Test Pushbutton - Modular Filter Testing

This is a test button for the modular geometry matching system.
It tests the filtering pipeline between linked model and host model.

CONTEXT: PyRevit UI tool - only runs from Revit interface

Shift+Click: Opens WPF configuration dialog
"""

__title__ = 'Geometry Matching Test'
__author__ = 'PrasKaa Team'
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Test button for the modular geometry matching system. Tests the filtering
pipeline between linked model and host model to match structural elements.

How-to:
1. Click the tool button to run with default filter pipeline
2. Shift+Click to open WPF configuration dialog
3. Select element category (Structural Framing or Columns)
4. Select linked model to match against
5. Select host elements to match
6. View matching results

Notes:
- Uses modular filter system from geometry_matching library
- Supports smart selection for host elements
- Configurable filter pipeline via WPF dialog

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

import os

from pyrevit import revit, DB, forms, script
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter,
    RevitLinkInstance, ElementId
)

# Import the modular filter system (pyRevit auto-adds extension root to sys.path)
from geometry_matching import (
    match_elements_modular,
    create_default_pipeline,
    FilterPipeline,
    LevelFilter,
    ConcreteBeamDimensionFilter,
    ETABSTypeMarkFilter,
    RevitTypeMarkFilter,
    FamilyNameFilter,
    BoundingBoxFilter,
    GeometryIntersectionFilter
)

# Import smart selection (pyRevit auto-adds extension root to sys.path)
from Snippets.smart_selection import (
    get_filtered_selection,
    create_single_category_filter
)

# Import WPF config
from GeometryMatchingConfig import GeometryMatchingConfigWindow


# Filter status output
output = script.get_output()


def get_linked_models():
    """Get all linked models in the current document."""
    doc = revit.doc
    
    link_instances = FilteredElementCollector(doc) \
        .OfClass(RevitLinkInstance) \
        .ToElements()
    
    return list(link_instances)


def select_linked_model():
    """Let user select a linked model."""
    links = get_linked_models()
    
    if not links:
        forms.alert("No linked models found in the current document.")
        return None
    
    # Create options for selection
    link_dict = {link.Name: link for link in links}
    
    # Show selection dialog
    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title="Select Linked Model",
        button_name="Select Link",
        multiselect=False
    )
    
    if not selected_link_name:
        return None
    
    return link_dict.get(selected_link_name)


def select_element_category():
    """Let user select element category for matching."""
    categories = [
        ("Structural Framing (Beams)", BuiltInCategory.OST_StructuralFraming),
        ("Structural Columns", BuiltInCategory.OST_StructuralColumns),
    ]
    
    options = {name: cat for name, cat in categories}
    
    selected = forms.SelectFromList.show(
        sorted(options.keys()),
        title="Select Element Category",
        button_name="Select",
        multiselect=False
    )
    
    if selected:
        return options.get(selected)
    return None


def create_test_pipeline():
    """Create a test pipeline with all filters."""
    pipeline = FilterPipeline()
    
    # Add filters in order (cheap to expensive)
    pipeline.add_filter(LevelFilter(enabled=True))
    pipeline.add_filter(ETABSTypeMarkFilter(enabled=True, use_prefix=True))
    pipeline.add_filter(RevitTypeMarkFilter(enabled=True, use_prefix=True))
    pipeline.add_filter(FamilyNameFilter(enabled=True, exact_match=True))
    pipeline.add_filter(BoundingBoxFilter(enabled=True, buffer_m=1.5))
    pipeline.add_filter(ConcreteBeamDimensionFilter(enabled=True, tolerance_mm=1.0))
    pipeline.add_filter(GeometryIntersectionFilter(enabled=True, vol_threshold=1e-9))
    
    return pipeline


def main():
    """Main function for geometry matching test."""
    # Check for shift+click to open config
    if __shiftclick__:
        output.print_md("=== Opening WPF Configuration Dialog ===\n")
        xaml_path = os.path.join(os.path.dirname(__file__), 'GeometryMatchingConfig.xaml')
        config_window = GeometryMatchingConfigWindow(xaml_path)
        config_window.show_dialog()
        
        if not config_window._saved:
            output.print_md("Configuration cancelled.")
            return
        
        # Use configured pipeline
        pipeline = config_window.pipeline
        output.print_md("Using configured filter pipeline.")
    else:
        # Use default pipeline
        pipeline = create_default_pipeline()
        output.print_md("Using default filter pipeline.")
    
    doc = revit.doc
    uidoc = revit.uidoc
    
    output.print_md("")
    output.print_md("=" * 60)
    output.print_md("=== Geometry Matching - Modular Filter Test ===")
    output.print_md("=" * 60)
    output.print_md("")
    
    # Step 1: Select element category
    output.print_md("Step 1: Selecting element category...")
    category = select_element_category()
    
    if not category:
        output.print_md("No category selected. Cancelled.")
        return
    
    output.print_md("Selected category: {}".format(category))
    output.print_md("")
    
    # Step 2: Select linked model
    output.print_md("Step 2: Selecting linked model...")
    link_instance = select_linked_model()
    
    if not link_instance:
        output.print_md("No linked model selected. Cancelled.")
        return
    
    link_doc = link_instance.GetLinkDocument()
    
    if not link_doc:
        output.print_md("ERROR: Could not get linked document.")
        return
    
    output.print_md("Selected: {}".format(link_instance.Name))
    output.print_md("")
    
    # Step 3: Get host elements using smart selection
    output.print_md("Step 3: Getting host elements (Smart Selection)...")
    
    # Create category filter for smart selection
    category_filter = create_single_category_filter(category)
    
    # Use smart selection - falls back to manual selection if no valid elements
    host_elements = get_filtered_selection(
        doc=doc,
        uidoc=uidoc,
        category_filter_func=category_filter,
        prompt_message="Select {} elements to match with linked model".format(
            "Structural Framing" if category == BuiltInCategory.OST_StructuralFraming else "Structural Column"
        ),
        no_selection_message="No valid elements selected. Please select elements to match.",
        filter_name="Geometry Matching"
    )
    
    if not host_elements:
        return
    
    output.print_md("Found {} host elements".format(len(host_elements)))
    output.print_md("")
    
    # Step 4: Show filter pipeline configuration
    output.print_md("Step 4: Filter Pipeline Configuration:")
    output.print_md("-" * 40)
    for f in pipeline.filters:
        status = "ON" if f.enabled else "OFF"
        if isinstance(f, BoundingBoxFilter):
            output.print_md("  {} [{}] - buffer: {}m".format(f.name, status, f.buffer_m))
        elif isinstance(f, ConcreteBeamDimensionFilter):
            output.print_md("  {} [{}] - tolerance: {}mm".format(f.name, status, f.tolerance_mm))
        elif isinstance(f, GeometryIntersectionFilter):
            output.print_md("  {} [{}] - threshold: {}".format(f.name, status, f.vol_threshold))
        else:
            output.print_md("  {} [{}]".format(f.name, status))
    output.print_md("")
    
    # Step 5: Run matching
    output.print_md("Step 5: Running modular matching...")
    output.print_md("-" * 40)
    
    results = match_elements_modular(
        link_doc=link_doc,
        link_instance=link_instance,
        host_elements=host_elements,
        element_category=category,
        filter_pipeline=pipeline
    )
    
    # Step 6: Display results (simplified)
    matched_count = len(results.get('matches', []))
    unmatched_count = len(results.get('unmatched', []))
    total_time = results.get('time_s', 0)
    
    output.print_md("")
    output.print_md("=== MATCHING COMPLETE ===")
    output.print_md("Matches: {} | Unmatched: {} | Time: {:.2f}s".format(
        matched_count, unmatched_count, total_time))


if __name__ == '__main__':
    main()
