# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Set Tender Notes X offset and Y offset on SELECTED title blocks across chosen sheets
# Version: 1.1

from pyrevit import revit, DB, forms, script

doc = revit.doc

# ── 1. Sheet selection (pre-select + fallback) ──────────────────────────────
sheets = forms.select_sheets(
    title='Select Target Sheets',
    include_placeholder=False,
    use_selection=True      # pre-selects sheets active in Project Browser
)

if not sheets:
    script.exit()

# Build set of selected sheet Id INTEGER values for reliable comparison
def _id_int(eid):
    try:
        return eid.Value          # Revit 2026+
    except AttributeError:
        return eid.IntegerValue   # Revit 2024-2025

selected_sheet_id_ints = set(_id_int(s.Id) for s in sheets)

# ── 2. Ask user for target values ──────────────────────────────────────────────
x_str = forms.ask_for_string(
    prompt="Enter value for 'Tender Notes X offset' (e.g. 0.0):",
    title="Set Tender Notes Offset",
    default="0.0"
)
if x_str is None:
    script.exit()

y_str = forms.ask_for_string(
    prompt="Enter value for 'Tender Notes Y offset' (e.g. 260.0):",
    title="Set Tender Notes Offset",
    default="260.0"
)
if y_str is None:
    script.exit()

try:
    x_val = float(x_str)
    y_val = float(y_str)
except ValueError:
    forms.alert("Invalid number input. Please enter numeric values.", exitscript=True)

# ── 3. Collect title blocks belonging to selected sheets only ─────────────────
all_title_blocks = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)\
    .WhereElementIsNotElementType()\
    .ToElements()

# Compare OwnerViewId as integer — avoids IronPython ElementId equality bug
title_blocks = [tb for tb in all_title_blocks if _id_int(tb.OwnerViewId) in selected_sheet_id_ints]

if not title_blocks:
    forms.alert("No title blocks found on the selected sheets.", exitscript=True)

# ── 4. Apply values in a single transaction ────────────────────────────────────
PARAM_X = "Tender Notes X offset"
PARAM_Y = "Tender Notes Y offset"

success_count = 0
skip_count = 0
errors = []

t = DB.Transaction(doc, "Set Tender Notes Offset - Selected Sheets")
t.Start()
try:
    for tb in title_blocks:
        param_x = tb.LookupParameter(PARAM_X)
        param_y = tb.LookupParameter(PARAM_Y)

        tb_name = "TitleBlock [{}]".format(tb.Id)
        missing = []
        if not param_x:
            missing.append(PARAM_X)
        if not param_y:
            missing.append(PARAM_Y)

        if missing:
            skip_count += 1
            errors.append("{}: parameter not found — {}".format(tb_name, ", ".join(missing)))
            continue

        # StorageType check — these are likely Double (length/offset in project units)
        if param_x.StorageType == DB.StorageType.Double:
            # Convert from mm (display) to internal feet units
            # Revit internal unit = feet; 1 mm = 1/304.8 ft
            try:
                # Revit 2022+ uses UnitUtils.ConvertToInternalUnits
                x_internal = DB.UnitUtils.ConvertToInternalUnits(x_val, DB.UnitTypeId.Millimeters)
                y_internal = DB.UnitUtils.ConvertToInternalUnits(y_val, DB.UnitTypeId.Millimeters)
            except AttributeError:
                # Revit 2021 and earlier fallback (DisplayUnitType)
                x_internal = DB.UnitUtils.ConvertToInternalUnits(
                    x_val, DB.DisplayUnitType.DUT_MILLIMETERS
                )
                y_internal = DB.UnitUtils.ConvertToInternalUnits(
                    y_val, DB.DisplayUnitType.DUT_MILLIMETERS
                )
            param_x.Set(x_internal)
            param_y.Set(y_internal)

        elif param_x.StorageType == DB.StorageType.Integer:
            param_x.Set(int(x_val))
            param_y.Set(int(y_val))

        else:
            # Fallback: try as string (unlikely for offset params)
            param_x.Set(str(x_val))
            param_y.Set(str(y_val))

        success_count += 1

    t.Commit()

except Exception as e:
    t.RollbackIfPending()
    forms.alert("Transaction failed: {}".format(str(e)), exitscript=True)

# ── 5. Report results ─────────────────────────────────────────────────────────
msg_parts = []
msg_parts.append("Set Tender Notes Offset — Complete")
msg_parts.append("")
msg_parts.append("Sheets targeted: {}".format(len(sheets)))
msg_parts.append("Title blocks updated: {}".format(success_count))
msg_parts.append("X offset: {} mm".format(x_val))
msg_parts.append("Y offset: {} mm".format(y_val))
if skip_count > 0:
    msg_parts.append("")
    msg_parts.append("Skipped: {} — parameter(s) not found".format(skip_count))

forms.alert("\n".join(msg_parts), exitscript=True)