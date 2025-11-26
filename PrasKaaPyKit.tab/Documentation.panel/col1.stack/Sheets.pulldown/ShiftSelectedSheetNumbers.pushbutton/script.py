#pylint: disable=W0703,E0401,C0103,C0111
from pyrevit import coreutils
from pyrevit import revit, DB
from pyrevit import forms
from pyrevit import script


logger = script.get_logger()
doc = __revit__.ActiveUIDocument.Document

# Ask user for shift amount
shift_input = forms.ask_for_string(
    default="1",
    prompt="Enter shift amount (positive for increment, negative for decrement):",
    title="Shift Sheet Numbers"
)

if not shift_input:
    script.exit()

try:
    shift = int(shift_input)
except ValueError:
    forms.alert("Invalid number entered. Please enter a valid integer.", exitscript=True)

selected_sheets = forms.select_sheets(title='Select Sheets to Shift Numbers',
                                      use_selection=True)
if not selected_sheets:
    script.exit()

sorted_sheet_list = sorted(selected_sheets, key=lambda x: x.SheetNumber)
if shift >= 0:
    sorted_sheet_list.reverse()

# Process each sheet in separate transaction
for sheet in sorted_sheet_list:
    t = DB.Transaction(doc, 'Shift Sheet: {}'.format(sheet.SheetNumber))
    t.Start()
    
    try:
        cur_sheet_num = sheet.SheetNumber
        sheetnum_p = sheet.Parameter[DB.BuiltInParameter.SHEET_NUMBER]
        
        # Use coreutils functions based on shift direction
        if shift >= 0:
            new_sheet_num = coreutils.increment_str(cur_sheet_num, shift)
        else:
            # For negative shift, use decrement_str with absolute value
            new_sheet_num = coreutils.decrement_str(cur_sheet_num, abs(shift))
        
        sheetnum_p.Set(new_sheet_num)
        
        t.Commit()
        logger.info('{} -> {}'.format(cur_sheet_num, new_sheet_num))
        
    except Exception as shift_err:
        t.RollBack()
        logger.error('Error processing sheet {}: {}'.format(cur_sheet_num, shift_err))