# -*- coding: utf-8 -*-
"""
UI Item Classes

Standardized classes untuk items yang ditampilkan di list views.

Author: PrasKaa
"""

# ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ IMPORTS
# ====================================================================================================
from ui.ui_styles import DARK_BLUE_THEME

# ╔╗ ╦  ╔═╗╔═╗╦╔═  ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ╠╩╗║  ║ ║║ ║╠╩╗  ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚═╝╩═╝╚═╝╚═╝╩ ╩  ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ BASE LIST ITEM
# ====================================================================================================

class BaseListItem(object):
    """
    Base class untuk semua list items.

    Menyediakan common properties dan methods untuk items di list views.
    """

    def __init__(self, name, is_selected=False):
        """
        Initialize base list item.

        Args:
            name (str): Item name
            is_selected (bool): Selection state
        """
        self._name = name
        self._is_selected = is_selected

    @property
    def Name(self):
        """Get item name."""
        return self._name

    @Name.setter
    def Name(self, value):
        """Set item name."""
        self._name = value

    @property
    def IsSelected(self):
        """Get selection state."""
        return self._is_selected

    @IsSelected.setter
    def IsSelected(self, value):
        """Set selection state."""
        self._is_selected = value

    def __str__(self):
        """String representation."""
        return "{}(Name='{}', IsSelected={})".format(self.__class__.__name__, self._name, self._is_selected)

    def __repr__(self):
        """Representation for debugging."""
        return self.__str__()

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ CHECKABLE LIST ITEM
# ====================================================================================================

class CheckableListItem(BaseListItem):
    """
    Item dengan checkbox untuk multi-selection scenarios.

    Digunakan untuk repository-style dialogs dimana user bisa select multiple items.
    """

    def __init__(self, name, is_selected=False, status="New", status_color=None):
        """
        Initialize checkable list item.

        Args:
            name (str): Item name
            is_selected (bool): Selection state
            status (str): Status text (e.g., "New", "Available", "Synced")
            status_color (str): Status color hex code
        """
        BaseListItem.__init__(self, name, is_selected)
        self._status = status
        self._status_color = status_color or DARK_BLUE_THEME['text_gray']

    @property
    def Status(self):
        """Get status text."""
        return self._status

    @Status.setter
    def Status(self, value):
        """Set status text."""
        self._status = value

    @property
    def StatusColor(self):
        """Get status color."""
        return self._status_color

    @StatusColor.setter
    def StatusColor(self, value):
        """Set status color."""
        self._status_color = value

# ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║╣ ╚╗╔╝║╣ ║║║ ║   ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ RADIO LIST ITEM
# ====================================================================================================

class RadioListItem(BaseListItem):
    """
    Item dengan radio button behavior untuk single selection.

    Digunakan untuk dialog-style windows dimana hanya satu item yang bisa dipilih.
    """

    def __init__(self, name, is_selected=False, element=None):
        """
        Initialize radio list item.

        Args:
            name (str): Item name
            is_selected (bool): Selection state
            element: Associated Revit element (optional)
        """
        BaseListItem.__init__(self, name, is_selected)
        self._element = element

    @property
    def Element(self):
        """Get associated Revit element."""
        return self._element

    @Element.setter
    def Element(self, value):
        """Set associated Revit element."""
        self._element = value

# ╔═╗╔═╗╔═╗╔═╗╔═╗╔╗ ╔═╗═╗ ╦
# ║ ║║  ║ ║╠═╝║╣ ╠╩╗║ ║╔╩╦╝
# ╚═╝╚═╝╚═╝╩  ╚═╝╚═╝╚═╝╩ ╚═ SPECIALIZED ITEMS
# ==================================================

class FamilyItem(CheckableListItem):
    """
    Specialized item untuk Family repository.

    Menambah properties khusus untuk families seperti category dan types.
    """

    def __init__(self, name, category="", status="New", status_color=None, is_selected=False):
        """
        Initialize family item.

        Args:
            name (str): Family name
            category (str): Family category
            status (str): Status text
            status_color (str): Status color
            is_selected (bool): Selection state
        """
        CheckableListItem.__init__(self, name, is_selected, status, status_color)
        self._category = category
        self._types = []

    @property
    def Category(self):
        """Get family category."""
        return self._category

    @Category.setter
    def Category(self, value):
        """Set family category."""
        self._category = value

    @property
    def Types(self):
        """Get family types."""
        return self._types

    @Types.setter
    def Types(self, value):
        """Set family types."""
        self._types = value

class ViewTemplateItem(CheckableListItem):
    """
    Specialized item untuk View Template repository.

    Menambah properties khusus untuk view templates.
    """

    def __init__(self, name, status="New", status_color=None, is_selected=False):
        """
        Initialize view template item.

        Args:
            name (str): Template name
            status (str): Status text
            status_color (str): Status color
            is_selected (bool): Selection state
        """
        CheckableListItem.__init__(self, name, is_selected, status, status_color)
        self._modified_by = None
        self._last_modified = None

    @property
    def ModifiedBy(self):
        """Get last modified by user."""
        return self._modified_by

    @ModifiedBy.setter
    def ModifiedBy(self, value):
        """Set last modified by user."""
        self._modified_by = value

    @property
    def LastModified(self):
        """Get last modified date."""
        return self._last_modified

    @LastModified.setter
    def LastModified(self, value):
        """Set last modified date."""
        self._last_modified = value

class SheetItem(RadioListItem):
    """
    Specialized item untuk sheet selection dialogs.

    Menambah properties khusus untuk sheets seperti sheet number.
    """

    def __init__(self, name, sheet_element=None, is_selected=False):
        """
        Initialize sheet item.

        Args:
            name (str): Sheet name (format: "Number - Name")
            sheet_element: Revit sheet element
            is_selected (bool): Selection state
        """
        RadioListItem.__init__(self, name, is_selected, sheet_element)

        # Parse sheet number dari name
        self._sheet_number = ""
        self._sheet_name = name

        if " - " in name:
            parts = name.split(" - ", 1)
            self._sheet_number = parts[0]
            self._sheet_name = parts[1]

    @property
    def SheetNumber(self):
        """Get sheet number."""
        return self._sheet_number

    @property
    def SheetName(self):
        """Get sheet name."""
        return self._sheet_name

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ UTILITY FUNCTIONS
# ==================================================

def create_family_item(family, current_doc):
    """
    Factory function untuk membuat FamilyItem dari Revit Family.

    Args:
        family: Revit Family object
        current_doc: Current Revit document

    Returns:
        FamilyItem: Configured family item
    """
    from ui.ui_styles import DARK_BLUE_THEME

    # Check if family exists in current document
    current_families = [f.Name for f in current_doc.GetElementsByType(Family)]
    exists_in_current = family.Name in current_families

    status = "Available" if exists_in_current else "New"
    status_color = DARK_BLUE_THEME['success_color'] if exists_in_current else DARK_BLUE_THEME['text_gray']
    is_selected = not exists_in_current  # Auto-select new families

    item = FamilyItem(
        name=family.Name,
        category=family.FamilyCategory.Name if family.FamilyCategory else "Uncategorized",
        status=status,
        status_color=status_color,
        is_selected=is_selected
    )

    # Get family types
    try:
        symbols = family.Symbols
        item.Types = [symbol.Name for symbol in symbols]
    except:
        item.Types = []

    return item

def create_view_template_item(template, current_doc):
    """
    Factory function untuk membuat ViewTemplateItem dari Revit View.

    Args:
        template: Revit View object (template)
        current_doc: Current Revit document

    Returns:
        ViewTemplateItem: Configured template item
    """
    from ui.ui_styles import DARK_BLUE_THEME

    # Check if template exists in current document
    current_templates = [v.Name for v in current_doc.GetElementsByType(View) if v.IsTemplate]
    exists_in_current = template.Name in current_templates

    status = "Available" if exists_in_current else "New"
    status_color = DARK_BLUE_THEME['success_color'] if exists_in_current else DARK_BLUE_THEME['text_gray']

    item = ViewTemplateItem(
        name=template.Name,
        status=status,
        status_color=status_color,
        is_selected=False  # Don't auto-select templates
    )

    return item

def create_sheet_item(sheet):
    """
    Factory function untuk membuat SheetItem dari Revit ViewSheet.

    Args:
        sheet: Revit ViewSheet object

    Returns:
        SheetItem: Configured sheet item
    """
    name = "{} - {}".format(sheet.SheetNumber, sheet.Name)
    return SheetItem(name=name, sheet_element=sheet, is_selected=False)
