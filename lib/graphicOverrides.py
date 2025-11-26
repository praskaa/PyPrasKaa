# -*- coding: utf-8 -*-
from System import Int64

def get_revit_version():
    """
    Get the current Revit version number
    """
    try:
        from pyrevit import revit
        app = revit.app
        version = app.VersionNumber
        return int(version)
    except:
        return 2024  # Default fallback

def get_solid_fill_pattern(doc):
    """
    Get the Solid Fill pattern which is a drafting pattern
    Returns the pattern ID or None if not found
    """
    try:
        from pyrevit import DB
        
        # Use FilteredElementCollector to find FillPatternElement
        collector = DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement)
        
        for pattern_elem in collector:
            # Look for "Solid fill" pattern (name varies by language)
            pattern_name = pattern_elem.Name
            if pattern_name:
                # Check for common solid fill pattern names
                name_lower = pattern_name.lower()
                if 'solid' in name_lower and 'fill' in name_lower:
                    fill_pattern = pattern_elem.GetFillPattern()
                    # Verify it's a drafting pattern (Target = Drafting)
                    if hasattr(fill_pattern, 'Target'):
                        if fill_pattern.Target == DB.FillPatternTarget.Drafting:
                            return pattern_elem.Id
                    else:
                        # For older API without Target property
                        return pattern_elem.Id
        
        # Fallback: get any drafting pattern
        for pattern_elem in collector:
            fill_pattern = pattern_elem.GetFillPattern()
            if hasattr(fill_pattern, 'Target'):
                if fill_pattern.Target == DB.FillPatternTarget.Drafting:
                    return pattern_elem.Id
        
        return None
    except Exception as e:
        print("Error getting solid fill pattern: {}".format(str(e)))
        return None

def get_concrete_fill_pattern(doc):
    """
    Get the Concrete Fill pattern which is a drafting pattern
    Returns the pattern ID or None if not found
    """
    try:
        from pyrevit import DB

        # Use FilteredElementCollector to find FillPatternElement
        collector = DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement)

        for pattern_elem in collector:
            # Look for "Concrete" pattern (name varies by language)
            pattern_name = pattern_elem.Name
            if pattern_name:
                # Check for concrete pattern names
                name_lower = pattern_name.lower()
                if 'concrete' in name_lower:
                    fill_pattern = pattern_elem.GetFillPattern()
                    # Verify it's a drafting pattern (Target = Drafting)
                    if hasattr(fill_pattern, 'Target'):
                        if fill_pattern.Target == DB.FillPatternTarget.Drafting:
                            return pattern_elem.Id
                    else:
                        # For older API without Target property
                        return pattern_elem.Id

        # Fallback: get any drafting pattern containing concrete
        for pattern_elem in collector:
            pattern_name = pattern_elem.Name
            if pattern_name and 'concrete' in pattern_name.lower():
                fill_pattern = pattern_elem.GetFillPattern()
                if hasattr(fill_pattern, 'Target'):
                    if fill_pattern.Target == DB.FillPatternTarget.Drafting:
                        return pattern_elem.Id

        return None
    except Exception as e:
        print("Error getting concrete fill pattern: {}".format(str(e)))
        return None

def get_diagonal_crosshatch_pattern(doc):
    """
    Get the Diagonal crosshatch Fill pattern which is a drafting pattern
    Returns the pattern ID or None if not found
    """
    try:
        from pyrevit import DB

        # Use FilteredElementCollector to find FillPatternElement
        collector = DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement)

        for pattern_elem in collector:
            # Look for "Diagonal crosshatch" pattern (name varies by language)
            pattern_name = pattern_elem.Name
            if pattern_name:
                # Check for diagonal crosshatch pattern names
                name_lower = pattern_name.lower()
                if 'diagonal' in name_lower and 'crosshatch' in name_lower:
                    fill_pattern = pattern_elem.GetFillPattern()
                    # Verify it's a drafting pattern (Target = Drafting)
                    if hasattr(fill_pattern, 'Target'):
                        if fill_pattern.Target == DB.FillPatternTarget.Drafting:
                            return pattern_elem.Id
                    else:
                        # For older API without Target property
                        return pattern_elem.Id

        # Fallback: get any drafting pattern containing diagonal and crosshatch
        for pattern_elem in collector:
            pattern_name = pattern_elem.Name
            if pattern_name and 'diagonal' in pattern_name.lower() and 'crosshatch' in pattern_name.lower():
                fill_pattern = pattern_elem.GetFillPattern()
                if hasattr(fill_pattern, 'Target'):
                    if fill_pattern.Target == DB.FillPatternTarget.Drafting:
                        return pattern_elem.Id

        return None
    except Exception as e:
        print("Error getting diagonal crosshatch pattern: {}".format(str(e)))
        return None

def get_safe_pattern_id(doc, revit_version):
    """
    Get a safe pattern ID that works across Revit versions
    """
    try:
        from pyrevit import DB

        if revit_version >= 2026:
            # Revit 2026+ requires drafting patterns
            pattern_id = get_solid_fill_pattern(doc)
            return pattern_id
        else:
            # Revit 2024 and earlier: ElementId 4 usually works for solid fill
            # But it's safer to get it properly
            pattern_id = get_solid_fill_pattern(doc)
            if pattern_id:
                return pattern_id
            else:
                # Fallback to hardcoded ID
                return DB.ElementId(Int64(4))
    except Exception as e:
        print("Error in get_safe_pattern_id: {}".format(str(e)))
        return None

def get_safe_concrete_pattern_id(doc, revit_version):
    """
    Get a safe concrete pattern ID that works across Revit versions
    """
    try:
        from pyrevit import DB

        if revit_version >= 2026:
            # Revit 2026+ requires drafting patterns
            pattern_id = get_concrete_fill_pattern(doc)
            return pattern_id
        else:
            # Revit 2024 and earlier: try to get concrete pattern properly
            pattern_id = get_concrete_fill_pattern(doc)
            if pattern_id:
                return pattern_id
            else:
                # Fallback to solid fill pattern if concrete not found
                return get_safe_pattern_id(doc, revit_version)
    except Exception as e:
        print("Error in get_safe_concrete_pattern_id: {}".format(str(e)))
        return None

def get_safe_diagonal_crosshatch_pattern_id(doc, revit_version):
    """
    Get a safe diagonal crosshatch pattern ID that works across Revit versions
    """
    try:
        from pyrevit import DB

        if revit_version >= 2026:
            # Revit 2026+ requires drafting patterns
            pattern_id = get_diagonal_crosshatch_pattern(doc)
            return pattern_id
        else:
            # Revit 2024 and earlier: try to get diagonal crosshatch pattern properly
            pattern_id = get_diagonal_crosshatch_pattern(doc)
            if pattern_id:
                return pattern_id
            else:
                # Fallback to solid fill pattern if diagonal crosshatch not found
                return get_safe_pattern_id(doc, revit_version)
    except Exception as e:
        print("Error in get_safe_diagonal_crosshatch_pattern_id: {}".format(str(e)))
        return None

# overrides lines and patterns in view
def setProjLines(r, g, b, strong=False):
    from pyrevit import revit, DB, forms
    try:
        selection = revit.get_selection()
        if len(selection) > 0:
            with revit.Transaction('Line Color'):
                src_style = DB.OverrideGraphicSettings()
                
                # Constructing RGB value
                color = DB.Color(r, g, b)
                
                # Set line colors
                src_style.SetProjectionLineColor(color)
                src_style.SetCutLineColor(color)
                
                if strong:
                    # Get appropriate pattern ID based on Revit version
                    revit_version = get_revit_version()
                    pattern_id = get_safe_pattern_id(revit.doc, revit_version)
                    
                    # Only set pattern-related overrides if we have a valid pattern
                    if pattern_id:
                        # Set foreground patterns
                        src_style.SetSurfaceForegroundPatternColor(color)
                        src_style.SetSurfaceForegroundPatternId(pattern_id)
                        src_style.SetCutForegroundPatternColor(color)
                        src_style.SetCutForegroundPatternId(pattern_id)
                        
                        # Optionally set background patterns
                        # Note: Background patterns might not be visible if foreground is solid
                        src_style.SetSurfaceBackgroundPatternColor(color)
                        src_style.SetSurfaceBackgroundPatternId(pattern_id)
                        src_style.SetCutBackgroundPatternColor(color)
                        src_style.SetCutBackgroundPatternId(pattern_id)
                    else:
                        # If no pattern available, just set colors without patterns
                        src_style.SetSurfaceForegroundPatternColor(color)
                        src_style.SetCutForegroundPatternColor(color)
                        src_style.SetSurfaceBackgroundPatternColor(color)
                        src_style.SetCutBackgroundPatternColor(color)
                else:
                    # Non-strong mode: just set cut pattern colors
                    src_style.SetCutForegroundPatternColor(color)
                    src_style.SetCutBackgroundPatternColor(color)

                # Apply overrides to selected elements
                for element in selection:
                    revit.active_view.SetElementOverrides(element.Id, src_style)

                # Show success toast notification
                summary = "Applied color to {} elements".format(len(selection))
                forms.toast(summary, title="Line Color", appid="PrasKaaPyKit")
        else:
            forms.alert('You must select at least one element.', exitscript=True)
    except Exception as e:
        # Enhanced error handling with full error message
        error_msg = 'Error applying line color:\n{}\n\nRevit Version: {}'.format(
            str(e), 
            get_revit_version()
        )
        try:
            forms.alert(error_msg, exitscript=True)
        except:
            print(error_msg)

# overrides lines and patterns in view with diagonal crosshatch foreground and solid background
def setProjLinesDiagonalCrossHatch(r1, g1, b1, r2, g2, b2, strong=True):
    from pyrevit import revit, DB, forms
    try:
        selection = revit.get_selection()
        if len(selection) > 0:
            with revit.Transaction('Line Color with Diagonal Crosshatch'):
                src_style = DB.OverrideGraphicSettings()

                # Constructing RGB values
                color1 = DB.Color(r1, g1, b1)
                color2 = DB.Color(r2, g2, b2)

                # Line colors are preserved (not overridden)

                # Get diagonal crosshatch pattern ID
                revit_version = get_revit_version()
                foreground_pattern_id = get_safe_diagonal_crosshatch_pattern_id(revit.doc, revit_version)

                # Get solid fill pattern ID for background
                background_pattern_id = get_safe_pattern_id(revit.doc, revit_version)

                if foreground_pattern_id:
                    # Set foreground patterns with diagonal crosshatch
                    src_style.SetSurfaceForegroundPatternColor(color1)
                    src_style.SetSurfaceForegroundPatternId(foreground_pattern_id)
                    src_style.SetCutForegroundPatternColor(color1)
                    src_style.SetCutForegroundPatternId(foreground_pattern_id)
                else:
                    # If no diagonal crosshatch pattern available, just set colors
                    src_style.SetSurfaceForegroundPatternColor(color1)
                    src_style.SetCutForegroundPatternColor(color1)

                if strong and background_pattern_id:
                    # Set background patterns with solid fill and color2
                    src_style.SetSurfaceBackgroundPatternColor(color2)
                    src_style.SetSurfaceBackgroundPatternId(background_pattern_id)
                    src_style.SetCutBackgroundPatternColor(color2)
                    src_style.SetCutBackgroundPatternId(background_pattern_id)
                elif strong:
                    # If no solid pattern available but strong=True, set colors without patterns
                    src_style.SetSurfaceBackgroundPatternColor(color2)
                    src_style.SetCutBackgroundPatternColor(color2)

                # Apply overrides to selected elements
                for element in selection:
                    revit.active_view.SetElementOverrides(element.Id, src_style)

                # Show success toast notification
                summary = "Applied diagonal crosshatch color to {} elements".format(len(selection))
                forms.toast(summary, title="Line Color", appid="PrasKaaPyKit")
        else:
            forms.alert('You must select at least one element.', exitscript=True)
    except Exception as e:
        # Enhanced error handling with full error message
        error_msg = 'Error applying diagonal crosshatch line color:\n{}\n\nRevit Version: {}'.format(
            str(e),
            get_revit_version()
        )
        try:
            forms.alert(error_msg, exitscript=True)
        except:
            print(error_msg)

# overrides lines and patterns in view with concrete foreground and solid background
def setProjLinesConcrete(r1, g1, b1, r2, g2, b2, strong=True):
    from pyrevit import revit, DB, forms
    try:
        selection = revit.get_selection()
        if len(selection) > 0:
            with revit.Transaction('Line Color with Concrete'):
                src_style = DB.OverrideGraphicSettings()

                # Constructing RGB values
                color1 = DB.Color(r1, g1, b1)
                color2 = DB.Color(r2, g2, b2)

                # Line colors are preserved (not overridden)

                # Get concrete pattern ID
                revit_version = get_revit_version()
                foreground_pattern_id = get_safe_concrete_pattern_id(revit.doc, revit_version)

                # Get solid fill pattern ID for background
                background_pattern_id = get_safe_pattern_id(revit.doc, revit_version)

                if foreground_pattern_id:
                    # Set foreground patterns with concrete
                    src_style.SetSurfaceForegroundPatternColor(color1)
                    src_style.SetSurfaceForegroundPatternId(foreground_pattern_id)
                    src_style.SetCutForegroundPatternColor(color1)
                    src_style.SetCutForegroundPatternId(foreground_pattern_id)
                else:
                    # If no concrete pattern available, just set colors
                    src_style.SetSurfaceForegroundPatternColor(color1)
                    src_style.SetCutForegroundPatternColor(color1)

                if strong and background_pattern_id:
                    # Set background patterns with solid fill and color2
                    src_style.SetSurfaceBackgroundPatternColor(color2)
                    src_style.SetSurfaceBackgroundPatternId(background_pattern_id)
                    src_style.SetCutBackgroundPatternColor(color2)
                    src_style.SetCutBackgroundPatternId(background_pattern_id)
                elif strong:
                    # If no solid pattern available but strong=True, set colors without patterns
                    src_style.SetSurfaceBackgroundPatternColor(color2)
                    src_style.SetCutBackgroundPatternColor(color2)

                # Apply overrides to selected elements
                for element in selection:
                    revit.active_view.SetElementOverrides(element.Id, src_style)

                # Show success toast notification
                summary = "Applied concrete color to {} elements".format(len(selection))
                forms.toast(summary, title="Line Color", appid="PrasKaaPyKit")
        else:
            forms.alert('You must select at least one element.', exitscript=True)
    except Exception as e:
        # Enhanced error handling with full error message
        error_msg = 'Error applying concrete line color:\n{}\n\nRevit Version: {}'.format(
            str(e),
            get_revit_version()
        )
        try:
            forms.alert(error_msg, exitscript=True)
        except:
            print(error_msg)