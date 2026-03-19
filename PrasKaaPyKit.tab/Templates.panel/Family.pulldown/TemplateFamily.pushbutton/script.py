# -*- coding: utf-8 -*-
"""Family Repository Sync Tool
Synchronize families with a template project.
"""

__title__ = "Family Repository"
__author__ = "PrasKaa Team"
__doc__ = """Synchronize families with template project.

Key features:
- Central storage in template project
- Smart sync with overwrite protection
- Filter by family category
- Multi-family type support

Author: PrasKaa
"""

import os
import clr
import traceback

# Add references
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
from Autodesk.Revit.DB import *

# Import pyRevit modules
from pyrevit import script
from pyrevit import forms
from pyrevit import revit
from pyrevit.forms import WPFWindow

# Import configuration
from config import TEMPLATE_PATTERNS, TEMPLATE_PROJECT_PATHS, COLORS, STATUS

# Initialize script
output = script.get_output()
logger = script.get_logger()
my_config = script.get_config()

# Get Revit app and doc
doc = revit.doc
uidoc = revit.uidoc
app = revit.doc.Application

# ─────────────────────────────────────────────────────────────────────────────
# Category group keywords for side nav filter
# ─────────────────────────────────────────────────────────────────────────────
NAV_CATEGORY_GROUPS = {
    'structural': [
        'structural', 'column', 'beam', 'framing', 'foundation',
        'wall', 'floor', 'slab', 'footing', 'brace', 'truss'
    ],
    'arch': [
        'door', 'window', 'curtain', 'furniture', 'casework',
        'ceiling', 'roof', 'stair', 'railing', 'ramp',
        'specialty', 'generic', 'detail', 'annotation'
    ],
    'mep': [
        'mechanical', 'electrical', 'plumbing', 'piping', 'duct',
        'conduit', 'lighting', 'air', 'hvac', 'fire', 'sprinkler',
        'equipment', 'terminal', 'fixture'
    ],
}


class FamilyItem(object):
    """Represents a family in the sync UI."""

    def __init__(self, name, category, status="New", status_color="#D7EDFF", is_selected=True):
        self._name = name
        self._category = category
        self._status = status
        self._status_color = status_color
        self._is_selected = is_selected
        self._types = []

    @property
    def Name(self):
        return self._name

    @property
    def Category(self):
        return self._category

    @property
    def Status(self):
        return self._status

    @Status.setter
    def Status(self, value):
        self._status = value

    @property
    def StatusColor(self):
        return self._status_color

    @StatusColor.setter
    def StatusColor(self, value):
        self._status_color = value

    @property
    def IsSelected(self):
        return self._is_selected

    @IsSelected.setter
    def IsSelected(self, value):
        self._is_selected = value

    @property
    def Types(self):
        return self._types

    @Types.setter
    def Types(self, value):
        self._types = value


class FamilyRepository(object):
    """Manages family synchronization with template project."""

    def __init__(self, template_doc, opened_by_script=False):
        self.doc_template = template_doc
        self.opened_by_script = opened_by_script

    def get_families(self):
        """Get all non-in-place families from template document."""
        collector = FilteredElementCollector(self.doc_template)
        families = collector.OfClass(Family).ToElements()
        return [f for f in families if not f.IsInPlace]

    def sync_family(self, family_name, target_doc):
        """Sync a single family from template to target document."""
        try:
            family = self._find_family_by_name(family_name)
            if not family:
                logger.error("Family not found in template: {}".format(family_name))
                return False

            family_doc = self.doc_template.EditFamily(family)
            if not family_doc:
                logger.error("Could not open family: {}".format(family_name))
                return False

            try:
                loaded_family = family_doc.LoadFamily(target_doc)
                family_doc.Close(False)
                return loaded_family
            except Exception as ex:
                logger.error("Error loading family {}: {}".format(family_name, str(ex)))
                if family_doc:
                    family_doc.Close(False)
                return False

        except Exception as ex:
            logger.error("Error syncing family {}: {}".format(family_name, str(ex)))
            return False

    def close_template_if_owned(self):
        """Close the template doc only if this script opened it.

        IMPORTANT: Must be called from main() AFTER ShowDialog() returns.
        Calling doc.Close() from the WPF dispatcher thread causes Revit to
        freeze on files >= ~50MB.
        """
        if not self.opened_by_script:
            logger.info("Template was opened by user — leaving it open.")
            return
        try:
            if self.doc_template and not self.doc_template.IsReadOnly:
                self.doc_template.Close(False)
                logger.info("Template document closed by script cleanup.")
            else:
                logger.warning("Template document could not be closed (read-only or already closed).")
        except Exception as ex:
            logger.error("Error closing template doc: {}".format(str(ex)))

    def _find_family_by_name(self, family_name):
        collector = FilteredElementCollector(self.doc_template)
        families = collector.OfClass(Family).ToElements()
        for family in families:
            if family.Name == family_name:
                return family
        return None


class RepositorySyncUI(WPFWindow):
    """UI for family repository synchronization."""

    def __init__(self):
        template_doc = self._get_template_project()
        if not template_doc:
            forms.alert(
                "Template project not found. Please open your template project.",
                exitscript=True
            )

        self.repository = FamilyRepository(
            template_doc,
            opened_by_script=self._was_opened_by_script
        )
        self._is_syncing = False
        self._active_nav = 'all'
        self.family_items = []
        self.filtered_items = []

        xaml_file = os.path.join(os.path.dirname(__file__), 'RepositorySyncUI.xaml')
        try:
            WPFWindow.__init__(self, xaml_file)
        except Exception as xaml_ex:
            # XAML load failed — immediately close template doc so it does not
            # stay open invisibly in the background, then re-raise so main()
            # can surface the error to the user.
            logger.error("XAML load failed: {}".format(str(xaml_ex)))
            self.repository.close_template_if_owned()
            raise

        # Closing: cancel sync only. Doc cleanup deferred to main().
        self.Closing += self._on_window_closing

        self.setup_ui()
        self.load_families()

    # ─────────────────────────────────────────────────────────────────────────
    # Template discovery
    # ─────────────────────────────────────────────────────────────────────────

    def _get_template_project(self):
        self._was_opened_by_script = False

        try:
            from config import TEMPLATE_PATTERNS, TEMPLATE_PROJECT_PATHS
        except ImportError as e:
            logger.error("Could not import config.py: {}".format(str(e)))
            TEMPLATE_PATTERNS = ["TEMPLATE", "STD", "STANDARD", "_TPL", "_TEMPLATE"]
            TEMPLATE_PROJECT_PATHS = []

        for path in TEMPLATE_PROJECT_PATHS:
            if os.path.exists(path):
                try:
                    template_doc = app.OpenDocumentFile(path)
                    if template_doc:
                        logger.info("Opened template from path: {}".format(path))
                        self._was_opened_by_script = True
                        return template_doc
                except Exception as ex:
                    logger.error("Failed to open template from {}: {}".format(path, str(ex)))
                    continue

        for opened_doc in app.Documents:
            if not opened_doc.IsFamilyDocument and not opened_doc.IsLinked:
                doc_name = opened_doc.Title.upper()
                if any(pattern in doc_name for pattern in TEMPLATE_PATTERNS):
                    logger.info("Found template in open documents: {}".format(opened_doc.Title))
                    return opened_doc

        options = ['Select from Open Documents', 'Browse for Template File']
        selected_option = forms.CommandSwitchWindow.show(
            options,
            message='Template project not found automatically.\n'
                    'How would you like to select the template?'
        )

        if selected_option == 'Select from Open Documents':
            project_list = [
                d for d in app.Documents
                if not d.IsFamilyDocument and not d.IsLinked
            ]
            if project_list:
                selected_title = forms.SelectFromList.show(
                    [d.Title for d in project_list],
                    title='Select Template Project',
                    message='Please select your template project:',
                    multiselect=False
                )
                if selected_title:
                    return next(d for d in project_list if d.Title == selected_title)

        elif selected_option == 'Browse for Template File':
            template_path = forms.pick_file(
                file_ext='rte',
                init_dir=r'I:\1_STUDI\Revit_Template',
                title='Select Template File'
            )
            if template_path:
                try:
                    template_doc = app.OpenDocumentFile(template_path)
                    if template_doc:
                        logger.info("Opened template from selected path: {}".format(template_path))
                        self._was_opened_by_script = True
                        return template_doc
                except Exception as ex:
                    logger.error("Failed to open selected template: {}".format(str(ex)))

        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Window lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def _on_window_closing(self, sender, args):
        if self._is_syncing:
            self._is_syncing = False
            logger.info("Sync cancelled by user (window closed).")

    def header_drag(self, sender, args):
        self.DragMove()

    def button_close(self, sender, args):
        self.Close()

    # ─────────────────────────────────────────────────────────────────────────
    # UI setup & data loading
    # ─────────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        try:
            self.Title = "Family Repository Sync"

            if hasattr(self, 'main_title'):
                self.main_title.Text = "Family Repository Sync"

            if hasattr(self, 'repository_path'):
                path = self.repository.doc_template.PathName
                self.repository_path.Text = path if path else "Template loaded (unsaved)"

            if hasattr(self, 'footer_version'):
                username = doc.Application.Username
                self.footer_version.Text = "v1.0 | {}".format(username)

        except Exception as ex:
            logger.error("Error in setup_ui: {}".format(str(ex)))
            logger.error(traceback.format_exc())

    def load_families(self):
        try:
            self.family_items = []

            template_families = self.repository.get_families()
            current_families = FilteredElementCollector(doc).OfClass(Family).ToElements()
            current_family_names = {f.Name for f in current_families}

            for family in template_families:
                if family.Name in current_family_names:
                    status       = STATUS['EXISTS']
                    status_color = COLORS['EXISTS']
                else:
                    status       = STATUS['NEW']
                    status_color = COLORS['NEW']

                item = FamilyItem(
                    name=family.Name,
                    category=family.FamilyCategory.Name if family.FamilyCategory else "Uncategorized",
                    status=status,
                    status_color=status_color,
                    is_selected=(status == STATUS['NEW'])
                )

                try:
                    item.Types = [s.Name for s in family.Symbols]
                except:
                    item.Types = []

                self.family_items.append(item)

            self.family_items.sort(key=lambda x: (x.Category, x.Name))
            self._apply_filter()

        except Exception as ex:
            logger.error("Failed to load families: {}".format(ex))
            logger.error(traceback.format_exc())
            forms.alert("Failed to load families. See log for details.")

    # ─────────────────────────────────────────────────────────────────────────
    # Filter helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _apply_filter(self):
        """Apply nav category filter + text search, then refresh list and counter."""
        search_text = ""
        if hasattr(self, 'UI_TextBox_Filter') and self.UI_TextBox_Filter.Text:
            search_text = self.UI_TextBox_Filter.Text.lower()

        result = self.family_items

        if self._active_nav != 'all':
            keywords = NAV_CATEGORY_GROUPS.get(self._active_nav, [])
            result = [
                f for f in result
                if any(kw in f.Category.lower() for kw in keywords)
            ]

        if search_text:
            result = [
                f for f in result
                if search_text in f.Name.lower() or search_text in f.Category.lower()
            ]

        self.filtered_items = result
        self.UI_ListBox_Families.ItemsSource = self.filtered_items
        self._update_counter()

    def _update_counter(self):
        """Update label_counter: '124 families — 47 selected'."""
        if not hasattr(self, 'label_counter'):
            return
        total    = len(self.filtered_items)
        selected = sum(1 for f in self.filtered_items if f.IsSelected)
        self.label_counter.Text = "{} {} — {} selected".format(
            total,
            "family" if total == 1 else "families",
            selected
        )

    def _set_active_nav(self, nav_key):
        """Switch active nav button style and reapply filter."""
        self._active_nav = nav_key

        nav_map = {
            'all':        'nav_btn_all',
            'structural': 'nav_btn_structural',
            'arch':       'nav_btn_arch',
            'mep':        'nav_btn_mep',
        }

        try:
            active_style   = self.FindResource('NavButtonActive')
            inactive_style = self.FindResource('NavButton')
            for key, btn_name in nav_map.items():
                btn = self.FindName(btn_name)
                if btn:
                    btn.Style = active_style if key == nav_key else inactive_style
        except Exception as ex:
            logger.warning("Could not update nav styles: {}".format(str(ex)))

        self._apply_filter()

    # ─────────────────────────────────────────────────────────────────────────
    # UI event handlers
    # ─────────────────────────────────────────────────────────────────────────

    def UIe_nav_all(self, sender, args):
        self._set_active_nav('all')

    def UIe_nav_structural(self, sender, args):
        self._set_active_nav('structural')

    def UIe_nav_arch(self, sender, args):
        self._set_active_nav('arch')

    def UIe_nav_mep(self, sender, args):
        self._set_active_nav('mep')

    def UIe_text_filter_updated(self, sender, args):
        self._apply_filter()

    def UIe_btn_select_all(self, sender, args):
        for item in self.filtered_items:
            item.IsSelected = True
        self.UI_ListBox_Families.Items.Refresh()
        self._update_counter()

    def UIe_btn_select_none(self, sender, args):
        for item in self.filtered_items:
            item.IsSelected = False
        self.UI_ListBox_Families.Items.Refresh()
        self._update_counter()

    def UIe_btn_sync(self, sender, args):
        """Sync selected families from template into the active document."""
        sync_button   = self.FindName("sync_button")
        sync_progress = self.FindName("sync_progress")

        try:
            selected_items = [item for item in self.filtered_items if item.IsSelected]
            if not selected_items:
                forms.alert("Please select at least one family to sync.")
                return

            if not forms.alert(
                "Sync {} selected {}?".format(
                    len(selected_items),
                    "family" if len(selected_items) == 1 else "families"
                ),
                ok=False, yes=True, no=True
            ):
                return

            # Lock UI + show progress
            sync_button.IsEnabled = False
            sync_button.Content   = "Syncing..."
            if sync_progress:
                sync_progress.Visibility = self._vis(True)

            self._is_syncing      = True
            operation_success     = True
            synced_count          = 0

            for item in selected_items:
                if not self._is_syncing:
                    logger.info("Sync aborted by user.")
                    break
                try:
                    success = self.repository.sync_family(item.Name, doc)
                    if success:
                        item.Status      = STATUS['SYNCED']
                        item.StatusColor = COLORS['SYNCED']
                        synced_count    += 1
                    else:
                        item.Status      = STATUS['ERROR']
                        item.StatusColor = COLORS['ERROR']
                        operation_success = False
                except Exception as e:
                    logger.error("Error syncing {}: {}".format(item.Name, str(e)))
                    item.Status      = STATUS['ERROR']
                    item.StatusColor = COLORS['ERROR']
                    operation_success = False

        except Exception as ex:
            operation_success = False
            logger.error("Error in sync operation: {}".format(str(ex)))
            logger.error(traceback.format_exc())

        finally:
            # Always restore UI regardless of how we exited
            self._is_syncing = False
            if sync_button:
                sync_button.IsEnabled = True
                sync_button.Content   = "Sync Selected Families"
            if sync_progress:
                sync_progress.Visibility = self._vis(False)
            self.UI_ListBox_Families.Items.Refresh()
            self._update_counter()

        if operation_success:
            forms.alert("Synced {} {} successfully.".format(
                synced_count,
                "family" if synced_count == 1 else "families"
            ))
        else:
            forms.alert("Sync completed with errors. Check the output window for details.")

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _vis(self, visible):
        """Return Visibility enum value. Lazy import avoids IronPython issues."""
        from System.Windows import Visibility
        return Visibility.Visible if visible else Visibility.Collapsed


def main():
    """Main script execution."""
    try:
        dialog = RepositorySyncUI()

        # ShowDialog() blocks until window is fully closed.
        # WPF dispatcher thread is done after this line returns.
        dialog.ShowDialog()

        # Safe to call doc.Close() here — back in Revit's execution context.
        if hasattr(dialog, 'repository') and dialog.repository:
            dialog.repository.close_template_if_owned()

    except Exception as ex:
        logger.error("Error running Family Repository: {}".format(ex))
        logger.error(traceback.format_exc())
        forms.alert("Failed to start Family Repository. See log for details.", exitscript=True)


if __name__ == '__main__':
    main()