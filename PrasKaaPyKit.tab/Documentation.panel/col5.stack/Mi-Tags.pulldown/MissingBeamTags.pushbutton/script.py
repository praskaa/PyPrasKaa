"""
Missing Beam Tag Finder

This addin selects beams with no associated tags in current view.

CONTEXT: PyRevit UI tool - hanya dijalankan dari Revit interface
"""

from pyrevit import revit, DB, forms

# Configuration
TAG_CATEGORY = DB.BuiltInCategory.OST_StructuralFramingTags
ELEMENT_CATEGORY = DB.BuiltInCategory.OST_StructuralFraming

doc = revit.doc
curview = doc.ActiveView

# Make sure active view is not a sheet
if isinstance(curview, DB.ViewSheet):
    forms.alert(
        "You're on a Sheet. Activate a model view please.",
        exitscript=True
    )

selection = revit.get_selection()

# ============================================================================
# Main Logic: Check host document elements only
# Note: Linked elements are NOT checked due to Revit API limitations.
# The linked_elements.py library is preserved for future development.
# ============================================================================

# Collect all tags in view
tag_collector = DB.FilteredElementCollector(doc, curview.Id)
tag_collector.OfClass(DB.IndependentTag)
tag_collector.WhereElementIsNotElementType()

tagged_ids = set()

for tag in tag_collector:
    try:
        tagged_local = tag.GetTaggedLocalElementIds()
        
        if tagged_local and tagged_local != DB.ElementId.InvalidElementId:
            for tid in tagged_local:
                tagged_ids.add(tid)
    except Exception:
        try:
            if hasattr(tag, 'TaggedLocalElementId'):
                tid = tag.TaggedLocalElementId
                if tid and tid != DB.ElementId.InvalidElementId:
                    tagged_ids.add(tid)
        except Exception:
            continue

# Collect all beams in view
beam_collector = DB.FilteredElementCollector(doc, curview.Id)
beam_collector.OfCategory(ELEMENT_CATEGORY)
beam_collector.WhereElementIsNotElementType()

untagged_beams = []

for beam in beam_collector:
    if beam.Id not in tagged_ids:
        untagged_beams.append(beam.Id)

# ============================================================================
# Report Results
# ============================================================================

if untagged_beams:
    # Select untagged beams
    selection.set_to(untagged_beams)
    
    forms.alert(
        "Selected {} untagged beam(s)".format(len(untagged_beams)),
        title="Missing Beam Tags"
    )

else:
    # Check if there are any beams at all
    all_beams = list(DB.FilteredElementCollector(doc, curview.Id)
        .OfCategory(ELEMENT_CATEGORY)
        .WhereElementIsNotElementType())
    
    if all_beams:
        forms.alert(
            'All beams in current view have tags.',
            title="Missing Beam Tags"
        )
    else:
        forms.alert(
            'No beams found in current view.',
            title="Missing Beam Tags"
        )
