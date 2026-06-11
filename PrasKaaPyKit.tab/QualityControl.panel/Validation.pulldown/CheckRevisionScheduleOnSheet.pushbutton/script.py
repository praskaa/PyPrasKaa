from pyrevit import revit, DB, script, forms

output = script.get_output()
output.close_others()

doc = revit.doc

TARGET_SCHEDULE_NAME = "REVISION CLOUD SCHEDULE"

# Collect all sheets
sheets = (
    DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_Sheets)
    .WhereElementIsNotElementType()
    .ToElements()
)

# Collect sheet IDs that already have the target schedule
schedule_instances = (
    DB.FilteredElementCollector(doc)
    .OfClass(DB.ScheduleSheetInstance)
    .ToElements()
)

sheets_with_target = set()
for si in schedule_instances:
    if si.IsTitleblockRevisionSchedule:
        continue
    sched_elem = doc.GetElement(si.ScheduleId)
    if sched_elem and sched_elem.Name == TARGET_SCHEDULE_NAME:
        sheets_with_target.add(si.OwnerViewId)

# Find sheets missing the target schedule
missing = []
for sheet in sheets:
    if sheet.Id not in sheets_with_target:
        missing.append((sheet.SheetNumber, sheet.Name))

# Output
if missing:
    missing = sorted(missing, key=lambda x: x[0])
    output.print_md(
        "## QA \u2014 Sheets Missing *{}*".format(TARGET_SCHEDULE_NAME)
    )
    output.print_md("**{} sheet(s) found without the schedule:**".format(len(missing)))
    headers = ["Sheet Number", "Sheet Name"]
    output.print_table(missing, headers)
else:
    forms.alert(
        "All sheets have '{}' schedule.".format(TARGET_SCHEDULE_NAME),
        title="QA Passed"
    )