# -*- coding: utf-8 -*-
__title__ = "Isolate Elements Modified on a Specific Date."
__author__ = "PrasKaa Team"
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Isolate Elements Modified on a Specific Date. Reads the 'LastModifiedBy'
shared parameter from structural/architectural elements and creates a 3D
isolated view for those modified on the chosen date.

This tool is useful for quality control and auditing changes made to a
Revit model on a specific date.

How-to:
1. Click the tool button to open the dialog
2. Select a target date using the date picker
3. (Optional) Filter by specific users
4. Click 'Filter Elements' to search for matching elements
5. Review the results in the results box
6. Click 'Create 3D View' to generate an isolated 3D view

Notes:
- Supports Structural Framing, Columns, Foundations, Walls, Floors, etc.
- Sheet and View elements cannot be isolated in 3D views

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from pyrevit import revit, DB, script
from Autodesk.Revit.DB import (
    ElementId, FilteredElementCollector,
    ViewFamilyType, View3D, ViewFamily,
    BuiltInCategory, FamilyInstance,
    ViewSheet, View
)
from System.Windows.Forms import (
    Form, TextBox, Button, Label, DialogResult,
    DateTimePickerFormat, FlatStyle,
    MessageBox, MessageBoxButtons, FormStartPosition,
    FormBorderStyle, ScrollBars, DateTimePicker,
    ListBox, SelectionMode, Panel, CheckBox,
    GroupBox, ComboBox, TabControl, TabPage,
    RichTextBox, BorderStyle, AnchorStyles,
    FlowLayoutPanel, FlowDirection, ToolTip,
    Application
)
from System.Drawing import (
    Font, FontStyle, Color, Point, Size,
    ContentAlignment, SolidBrush
)
from System.Collections.Generic import List
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PARAM_NAME   = "LastModifiedBy"
MAX_DETAIL   = 500     # max element rows shown in result box

ALLOWED_CATS = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_EdgeSlab,
    BuiltInCategory.OST_Stairs,
    BuiltInCategory.OST_Rebar,
    BuiltInCategory.OST_Doors,
    BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_Roofs,
    BuiltInCategory.OST_Ceilings,
    BuiltInCategory.OST_GenericModel,
    BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_MechanicalEquipment,
    BuiltInCategory.OST_PlumbingFixtures,
    BuiltInCategory.OST_ElectricalFixtures,
]

# ---------------------------------------------------------------------------
# Color scheme
# ---------------------------------------------------------------------------
def hex_to_color(hex_str):
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return Color.FromArgb(r, g, b)

CLR_BG       = hex_to_color('#181820')
CLR_PANEL    = hex_to_color('#22222E')
CLR_ACCENT   = hex_to_color('#63B3ED')
CLR_ACCENT2  = hex_to_color('#9AE6B4')
CLR_TEXT     = hex_to_color('#E2E8F0')
CLR_SUBTEXT  = hex_to_color('#94A3B8')
CLR_BORDER   = hex_to_color('#374151')
CLR_BTN      = hex_to_color('#3182CE')
CLR_WARN     = hex_to_color('#FCD34D')
CLR_DANGER   = hex_to_color('#FC8181')
CLR_SUCCESS  = hex_to_color('#68D391')

# ---------------------------------------------------------------------------
# Fonts  — Segoe UI for all UI controls; Consolas only for data output box
# ---------------------------------------------------------------------------
FNT_DEFAULT  = Font("Segoe UI", 9,  FontStyle.Regular)
FNT_BOLD     = Font("Segoe UI", 9,  FontStyle.Bold)
FNT_TITLE    = Font("Segoe UI", 14, FontStyle.Bold)
FNT_SUBTITLE = Font("Segoe UI", 9,  FontStyle.Regular)
FNT_BTN      = Font("Segoe UI", 9,  FontStyle.Bold)
FNT_DATA     = Font("Consolas", 9,  FontStyle.Regular)   # result_box only
FNT_STATUS   = Font("Segoe UI", 9,  FontStyle.Bold)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_allowed_cat_ids(doc):
    return set(ElementId(c) for c in ALLOWED_CATS)


def collect_elements_with_param(doc):
    allowed_ids = get_allowed_cat_ids(doc)
    result = []
    collector = FilteredElementCollector(doc)\
        .WhereElementIsNotElementType()\
        .ToElements()
    for el in collector:
        if el is None or el.Category is None:
            continue
        if el.Category.Id not in allowed_ids:
            continue
        p = el.LookupParameter(PARAM_NAME)
        if p is None or not p.HasValue:
            continue
        val = p.AsString()
        if val:
            result.append((el, val))
    return result


def parse_date_from_value(val):
    try:
        start = val.find('(')
        end   = val.find(')')
        if start == -1 or end == -1:
            return None
        date_str = val[start+1:end].strip()
        current_year = datetime.now().year
        date_str_with_year = "{} {}".format(date_str, current_year)
        dt = datetime.strptime(date_str_with_year, "%a, %d %b %H:%M %Y")
        return dt
    except Exception:
        return None


def parse_user_from_value(val):
    try:
        paren_pos = val.find('(')
        if paren_pos == -1:
            return val.strip()
        return val[:paren_pos].strip()
    except Exception:
        return val


def filter_elements_by_date(elements_with_params, target_date, selected_users=None):
    matched = []
    summary = {}
    for el, val in elements_with_params:
        dt = parse_date_from_value(val)
        if dt is None:
            continue
        if dt.day == target_date.day and dt.month == target_date.month:
            user = parse_user_from_value(val)
            if selected_users and user not in selected_users:
                continue
            matched.append(el)
            summary[user] = summary.get(user, 0) + 1
    return matched, summary


# ---------------------------------------------------------------------------
# 3D View helpers
# ---------------------------------------------------------------------------

def create_3d_view(doc, view_name):
    view_type_collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)
    view_3d_types = [vt for vt in view_type_collector
                     if vt.ViewFamily == ViewFamily.ThreeDimensional]
    if not view_3d_types:
        return None
    view_type_3d = view_3d_types[0]
    view_3d = View3D.CreateIsometric(doc, view_type_3d.Id)
    base_name = view_name
    for i in range(100):
        try:
            view_3d.Name = view_name
            break
        except Exception:
            view_name = "{} {}".format(base_name, i + 1)
    return view_3d


def hide_other_elements(view_3d, elements_to_show, doc):
    if not elements_to_show:
        return False
    cats_to_hide = [
        BuiltInCategory.OST_Levels,
        BuiltInCategory.OST_Grids,
        BuiltInCategory.OST_VolumeOfInterest,
        BuiltInCategory.OST_SectionBox,
    ]
    for cat in cats_to_hide:
        try:
            view_3d.SetCategoryHidden(ElementId(cat), True)
        except Exception:
            pass
    target_id_set = set(el.Id for el in elements_to_show)
    all_elements = FilteredElementCollector(doc, view_3d.Id)\
        .WhereElementIsNotElementType()\
        .ToElements()
    to_hide = []
    for el in all_elements:
        if el.Id not in target_id_set:
            try:
                if el.CanBeHidden(view_3d):
                    to_hide.append(el.Id)
            except Exception:
                pass
    if to_hide:
        view_3d.HideElements(List[ElementId](to_hide))
    return True


# ---------------------------------------------------------------------------
# UI -- Main Dialog
# ---------------------------------------------------------------------------

class IsolateByDateForm(Form):
    def __init__(self, doc):
        self.doc = doc
        self.selected_elements = []
        self.all_data = []
        self.unique_users = []
        self._tooltip = ToolTip()

        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        self.Text = "Isolate Elements by Modification Date"
        self.Width = 700
        # Height ditentukan oleh ClientSize di akhir _build_ui
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.BackColor = CLR_BG
        self.Font = FNT_DEFAULT

        y = 16

        # ── Title ──────────────────────────────────────────────────────────
        title = Label()
        title.Text = "ISOLATE BY DATE"
        title.Font = FNT_TITLE
        title.ForeColor = CLR_ACCENT
        title.Location = Point(20, y)
        title.Size = Size(500, 30)
        self.Controls.Add(title)
        y += 32

        subtitle = Label()
        subtitle.Text = "Filter elements by '{}' parameter".format(PARAM_NAME)
        subtitle.Font = FNT_SUBTITLE
        subtitle.ForeColor = CLR_SUBTEXT
        subtitle.Location = Point(21, y)
        subtitle.Size = Size(500, 20)
        self.Controls.Add(subtitle)
        y += 32

        # ── Date row ───────────────────────────────────────────────────────
        lbl_date = Label()
        lbl_date.Text = "Target Date:"
        lbl_date.Font = FNT_BOLD
        lbl_date.ForeColor = CLR_TEXT
        lbl_date.Location = Point(20, y + 4)
        lbl_date.Size = Size(100, 20)
        self.Controls.Add(lbl_date)

        self.date_picker = DateTimePicker()
        self.date_picker.Location = Point(125, y)
        self.date_picker.Size = Size(180, 26)
        self.date_picker.Font = FNT_DEFAULT
        self.date_picker.Format = DateTimePickerFormat.Short
        self.Controls.Add(self.date_picker)

        btn_filter = Button()
        btn_filter.Text = "Filter Elements"
        btn_filter.Location = Point(320, y - 1)
        btn_filter.Size = Size(140, 30)
        btn_filter.Font = FNT_BTN
        btn_filter.BackColor = CLR_BTN
        btn_filter.ForeColor = CLR_TEXT
        btn_filter.FlatStyle = FlatStyle.Flat
        btn_filter.FlatAppearance.BorderSize = 0
        btn_filter.Click += self._on_filter
        self._tooltip.SetToolTip(btn_filter,
            "Search for elements modified on the selected date")
        self.Controls.Add(btn_filter)
        y += 42

        # ── User filter ────────────────────────────────────────────────────
        lbl_user = Label()
        lbl_user.Text = "Filter by User:"
        lbl_user.Font = FNT_BOLD
        lbl_user.ForeColor = CLR_TEXT
        lbl_user.Location = Point(20, y)
        lbl_user.Size = Size(200, 20)
        self.Controls.Add(lbl_user)
        y += 22

        self.user_list = ListBox()
        self.user_list.Location = Point(20, y)
        self.user_list.Size = Size(250, 90)
        self.user_list.Font = FNT_DEFAULT
        self.user_list.BackColor = CLR_PANEL
        self.user_list.ForeColor = CLR_TEXT
        self.user_list.SelectionMode = SelectionMode.MultiExtended
        self.user_list.BorderStyle = BorderStyle.FixedSingle
        self._tooltip.SetToolTip(self.user_list,
            "Leave empty to include all users.\n"
            "Ctrl+Click to select multiple users.")
        self.Controls.Add(self.user_list)

        # "Clear Selection" button — directly below ListBox
        btn_clear_sel = Button()
        btn_clear_sel.Text = "Clear Selection"
        btn_clear_sel.Location = Point(20, y + 95)
        btn_clear_sel.Size = Size(120, 26)
        btn_clear_sel.Font = FNT_DEFAULT
        btn_clear_sel.BackColor = CLR_PANEL
        btn_clear_sel.ForeColor = CLR_SUBTEXT
        btn_clear_sel.FlatStyle = FlatStyle.Flat
        btn_clear_sel.FlatAppearance.BorderColor = CLR_BORDER
        btn_clear_sel.FlatAppearance.BorderSize = 1
        btn_clear_sel.Click += lambda s, e: self.user_list.ClearSelected()
        self._tooltip.SetToolTip(btn_clear_sel,
            "Deselect all users — results will include all users")
        self.Controls.Add(btn_clear_sel)

        y += 130

        # ── Results label ──────────────────────────────────────────────────
        lbl_result = Label()
        lbl_result.Text = "Matched Elements:"
        lbl_result.Font = FNT_BOLD
        lbl_result.ForeColor = CLR_TEXT
        lbl_result.Location = Point(20, y)
        lbl_result.Size = Size(300, 20)
        self.Controls.Add(lbl_result)
        y += 22

        # ── Result box  (Consolas 9pt — data output only) ──────────────────
        self.result_box = RichTextBox()
        self.result_box.Location = Point(20, y)
        self.result_box.Size = Size(650, 210)
        self.result_box.Font = FNT_DATA
        self.result_box.BackColor = CLR_PANEL
        self.result_box.ForeColor = CLR_TEXT
        self.result_box.BorderStyle = BorderStyle.FixedSingle
        self.result_box.ReadOnly = True
        self.Controls.Add(self.result_box)
        y += 218

        # ── Status bar ─────────────────────────────────────────────────────
        self.lbl_status = Label()
        self.lbl_status.Text = "Ready — click 'Filter Elements' to begin."
        self.lbl_status.Font = FNT_STATUS
        self.lbl_status.ForeColor = CLR_SUBTEXT
        self.lbl_status.Location = Point(20, y + 4)
        self.lbl_status.Size = Size(400, 22)   # max x = 20+400=420, tombol mulai x=440
        self.lbl_status.AutoEllipsis = True    # potong teks panjang dengan "..."
        self.Controls.Add(self.lbl_status)

        # ── Action buttons ─────────────────────────────────────────────────
        self.btn_create = Button()
        self.btn_create.Text = "Create 3D View"
        self.btn_create.Location = Point(440, y)
        self.btn_create.Size = Size(130, 34)
        self.btn_create.Font = FNT_BTN
        self.btn_create.BackColor = CLR_SUCCESS
        self.btn_create.ForeColor = CLR_BG
        self.btn_create.FlatStyle = FlatStyle.Flat
        self.btn_create.FlatAppearance.BorderSize = 0
        self.btn_create.Enabled = False
        self.btn_create.Click += self._on_create
        self._tooltip.SetToolTip(self.btn_create,
            "Create a new isolated 3D view containing only the matched elements")
        self.Controls.Add(self.btn_create)

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(580, y)
        btn_cancel.Size = Size(80, 34)
        btn_cancel.Font = FNT_DEFAULT
        btn_cancel.BackColor = CLR_PANEL
        btn_cancel.ForeColor = CLR_TEXT
        btn_cancel.FlatStyle = FlatStyle.Flat
        btn_cancel.FlatAppearance.BorderColor = CLR_BORDER
        btn_cancel.FlatAppearance.BorderSize = 1
        btn_cancel.DialogResult = DialogResult.Cancel
        self.Controls.Add(btn_cancel)

        self.CancelButton = btn_cancel

        # ClientSize mengukur area konten saja (tidak termasuk title bar & border)
        # sehingga hitungan lebih akurat daripada self.Height
        # bottom of button = y + 34 (button height) + 16 (bottom padding)
        self.ClientSize = Size(700, y + 34 + 16)

    # ---------------------------------------------------------------- Data --

    def _set_status(self, text, color):
        """Update status label with text and color, flush UI immediately."""
        self.lbl_status.Text = text
        self.lbl_status.ForeColor = color
        self.lbl_status.Refresh()

    def _load_data(self):
        self._set_status("Loading elements from document...", CLR_WARN)
        Application.DoEvents()   # ensure status renders before heavy work

        try:
            self.all_data = collect_elements_with_param(self.doc)

            users = set()
            for _, val in self.all_data:
                users.add(parse_user_from_value(val))

            self.unique_users = sorted(list(users))
            self.user_list.Items.Clear()
            for u in self.unique_users:
                self.user_list.Items.Add(u)

            self._set_status(
                "Loaded {} element(s) with '{}' parameter.".format(
                    len(self.all_data), PARAM_NAME),
                CLR_SUCCESS
            )

        except Exception as e:
            self._set_status("Error loading data: {}".format(str(e)), CLR_DANGER)

    # -------------------------------------------------------------- Events --

    def _on_filter(self, sender, args):
        try:
            picked = self.date_picker.Value
            target_date = datetime(picked.Year, picked.Month, picked.Day)

            selected_users = None
            if self.user_list.SelectedItems.Count > 0:
                selected_users = set(self.user_list.SelectedItems)

            matched, summary = filter_elements_by_date(
                self.all_data, target_date, selected_users
            )
            self.selected_elements = matched

            self.result_box.Clear()
            self.result_box.SuspendLayout()

            if not matched:
                self.result_box.SelectionColor = CLR_WARN
                self.result_box.AppendText(
                    "No elements found for: {}\n".format(
                        target_date.strftime("%A, %d %B %Y")
                    )
                )
                self.btn_create.Enabled = False
                self._set_status("No matching elements found.", CLR_WARN)

            else:
                self.result_box.SelectionColor = CLR_ACCENT
                self.result_box.AppendText(
                    "Date: {}  —  {} element(s) found\n".format(
                        target_date.strftime("%A, %d %B %Y"),
                        len(matched)
                    )
                )
                self.result_box.AppendText("-" * 68 + "\n")

                self.result_box.SelectionColor = CLR_ACCENT2
                self.result_box.AppendText("By User:\n")
                for user, count in sorted(summary.items()):
                    self.result_box.SelectionColor = CLR_TEXT
                    self.result_box.AppendText(
                        "  {:35s}  {:>4d} element(s)\n".format(user, count)
                    )

                self.result_box.AppendText("-" * 68 + "\n")

                self.result_box.SelectionColor = CLR_ACCENT2
                self.result_box.AppendText("Element Details:\n")

                display_els = matched[:MAX_DETAIL]
                for el in display_els:
                    p = el.LookupParameter(PARAM_NAME)
                    val = p.AsString() if p and p.HasValue else "-"
                    cat_name = el.Category.Name if el.Category else "Unknown"
                    self.result_box.SelectionColor = CLR_SUBTEXT
                    self.result_box.AppendText(
                        "  ID: {:>10}  Cat: {:25s}  {}\n".format(
                            el.Id.IntegerValue, cat_name, val
                        )
                    )

                if len(matched) > MAX_DETAIL:
                    self.result_box.SelectionColor = CLR_WARN
                    self.result_box.AppendText(
                        "\n  ... {} more element(s) not shown "
                        "(display limited to {}).\n".format(
                            len(matched) - MAX_DETAIL, MAX_DETAIL
                        )
                    )

                self.btn_create.Enabled = True
                self._set_status(
                    "{} element(s) ready to isolate.".format(len(matched)),
                    CLR_SUCCESS
                )

            self.result_box.ResumeLayout()

        except Exception as e:
            import traceback
            self.result_box.SelectionColor = CLR_DANGER
            self.result_box.AppendText("Error:\n" + traceback.format_exc())
            self._set_status("Filter error — see result box.", CLR_DANGER)

    def _on_create(self, sender, args):
        """
        Signal intent only.
        Do NOT close the form here — main() closes it after
        the Revit transaction succeeds.
        """
        if not self.selected_elements:
            MessageBox.Show("No elements to isolate.", "Warning")
            return
        self.DialogResult = DialogResult.OK
        # ✅ self.Close() intentionally omitted


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    doc   = revit.doc
    uidoc = revit.uidoc

    form   = IsolateByDateForm(doc)
    result = form.ShowDialog()

    if result != DialogResult.OK:
        script.exit()

    elements_to_isolate = form.selected_elements
    if not elements_to_isolate:
        script.exit()

    isolatable     = []
    non_isolatable = []
    for el in elements_to_isolate:
        if isinstance(el, (ViewSheet, View)):
            non_isolatable.append(el)
        else:
            isolatable.append(el)

    if not isolatable:
        MessageBox.Show(
            "All matched elements are Sheets or Views which cannot be\n"
            "isolated in a 3D view.\n\n"
            "Found {} non-isolatable element(s):\n{}".format(
                len(non_isolatable),
                "\n".join("  - {}  (ID: {})".format(
                    el.Name if hasattr(el, 'Name') else str(el.Id),
                    el.Id.IntegerValue
                ) for el in non_isolatable[:10])
            ),
            "Cannot Isolate"
        )
        script.exit()

    if non_isolatable:
        MessageBox.Show(
            "{} Sheet/View element(s) excluded from 3D view:\n{}".format(
                len(non_isolatable),
                "\n".join("  - {}".format(
                    el.Name if hasattr(el, 'Name') else str(el.Id)
                ) for el in non_isolatable[:10])
            ),
            "Note: Sheets/Views Excluded"
        )

    picked_date = form.date_picker.Value
    date_str    = "{:04d}{:02d}{:02d}".format(
        picked_date.Year, picked_date.Month, picked_date.Day
    )
    view_name = "Isolated_ByDate_{}".format(date_str)

    with revit.Transaction("Create Isolated 3D View by Date"):
        view_3d = create_3d_view(doc, view_name)
        if view_3d is None:
            MessageBox.Show("Failed to create 3D view.", "Error")
            script.exit()
        hide_other_elements(view_3d, isolatable, doc)

    # ✅ Close form only after transaction succeeds
    form.Close()

    uidoc.ActiveView = view_3d

    output = script.get_output()
    output.print_md("# Isolate by Date — Complete")
    output.print_md("**View Created:** `{}`".format(view_3d.Name))
    output.print_md("**Elements Isolated:** {}".format(len(isolatable)))
    if non_isolatable:
        output.print_md("**Skipped (Sheet/View):** {}".format(len(non_isolatable)))
    output.print_md("---")
    output.print_md("### Isolated Elements")
    for el in isolatable:
        p = el.LookupParameter(PARAM_NAME)
        val = p.AsString() if p and p.HasValue else "-"
        cat_name = el.Category.Name if el.Category else "Unknown"
        output.print_md("- **ID** `{}` | **Cat** {} | **{}** {}".format(
            el.Id.IntegerValue, cat_name, PARAM_NAME, val
        ))


if __name__ == '__main__':
    main()