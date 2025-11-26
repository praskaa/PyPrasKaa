# -*- coding: UTF-8 -*-
""" Warning Schedule with Duplicate Type Analysis - Enhanced with Family and Type Name Extraction.

Lists Warnings related to Structural elements with detailed analysis of ElementTypes 
and their instances, including count and classification per type.
Enhanced to show Family Name and Type Name separately.

"""

__title__ = 'Type Mark Checker - Enhanced'
__author__ = 'PrasKaa Team'
__doc__ = 'Analyzes Warnings with detailed ElementType classification, instance tracking, and Family/Type name extraction.'

from pyrevit import revit, DB, coreutils, script, output, forms
from pyrevit.coreutils import Timer
from customOutput import typemarkWarning, hmsTimer, file_name_getter, colors, ct_icon
from collections import defaultdict
from Autodesk.Revit.DB import BuiltInParameter

# Constants for readability and maintenance
UNKNOWN_FAMILY = "Unknown Family"
UNKNOWN_TYPE = "Unknown Type"
NA_CATEGORY = "NA"
UNKNOWN_CATEGORY = "Unknown Category"


def get_family_and_type_name(element_type):
    """Mendapatkan nama famili dan nama tipe dari ElementType secara terpisah."""
    family_name = UNKNOWN_FAMILY
    type_name = UNKNOWN_TYPE

    # Ambil nama famili jika tersedia
    if hasattr(element_type, 'FamilyName'):
        family_name = element_type.FamilyName
    
    # Ambil nama tipe dari parameter SYMBOL_NAME_PARAM atau properti .Name
    p_type_name = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    if p_type_name and p_type_name.HasValue:
        type_name = p_type_name.AsString()
    elif hasattr(element_type, 'Name'):
        type_name = element_type.Name
        
    return family_name, type_name

def get_type_mark_or_name(element_type):
    """Prioritaskan Type Mark. Fallback ke Family : Type Name lalu ke .Name."""
    # 1) Type Mark - prioritas utama
    p = element_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
    if p and p.HasValue:
        s = p.AsString()
        if s and s.strip():
            return s.strip()

    # 2) Kombinasi Nama Famili dan Tipe
    family_name, type_name = get_family_and_type_name(element_type)
    if family_name != UNKNOWN_FAMILY:
        return u"{} : {}".format(family_name, type_name)

    # 3) Fallback terakhir: nama tipe saja
    if type_name != UNKNOWN_TYPE:
        return type_name
        
    return UNKNOWN_TYPE

def get_builtin_parameter_info(element_type):
    """Mendapatkan informasi tentang BuiltInParameter yang tersedia pada ElementType."""
    param_info = {}
    
    # Daftar BuiltInParameter yang umum untuk ElementType
    common_params = [
        BuiltInParameter.ALL_MODEL_TYPE_MARK,
        BuiltInParameter.SYMBOL_NAME_PARAM,
        BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM,
        BuiltInParameter.ALL_MODEL_FAMILY_NAME,
        BuiltInParameter.ELEM_FAMILY_PARAM,
        BuiltInParameter.ELEM_TYPE_PARAM
    ]
    
    for param_enum in common_params:
        try:
            param = element_type.get_Parameter(param_enum)
            if param:
                param_name = param.Definition.Name
                param_value = ""
                
                if param.HasValue:
                    if param.StorageType == DB.StorageType.String:
                        param_value = param.AsString() or ""
                    elif param.StorageType == DB.StorageType.Integer:
                        param_value = str(param.AsInteger())
                    elif param.StorageType == DB.StorageType.Double:
                        param_value = str(param.AsDouble())
                    elif param.StorageType == DB.StorageType.ElementId:
                        param_value = str(param.AsElementId().IntegerValue)
                
                param_info[param_name] = {
                    'value': param_value,
                    'builtin_param': str(param_enum),
                    'storage_type': str(param.StorageType)
                }
        except AttributeError:
            # Parameter does not exist on the element type
            continue
        except Exception:
            # Catch any other unexpected errors but continue processing
            continue
    
    return param_info

# Import charts with error handling
try:
    from pyrevit.output import charts
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("Charts module not available")

# Configuration flags
ENABLE_CHART_OUTPUT = False  # Set to False to disable chart generation
SHOW_PARAMETER_DETAILS = False  # Set to True to show detailed parameter information

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
timer = Timer()

allWarnings = doc.GetWarnings()

output = script.get_output()
# changing icon
ct_icon(output)
output.set_width(900)
output.print_md("# ENHANCED TYPE MARK CHECKER - WITH FAMILY/TYPE NAME EXTRACTION")
output.print_md("### " + file_name_getter(doc))
output.freeze()

count = 0
# Dictionary to store type analysis data
type_analysis = defaultdict(dict)
# for graph
graphHeadings = []
graphWarnData = []

def get_all_instances_by_type(doc):
    """
    Collects all element instances in the document and groups them by their ElementTypeId.
    This is much more performant than querying for each type individually.
    """
    instances_by_type = defaultdict(list)
    collector = DB.FilteredElementCollector(doc).WhereElementIsNotElementType()
    for elem in collector:
        try:
            type_id = elem.GetTypeId()
            if type_id and type_id != DB.ElementId.InvalidElementId:
                instances_by_type[type_id].append(elem)
        except Exception:
            # Some elements might not have a GetTypeId method or fail for other reasons
            continue
    return instances_by_type



def process_duplicate_type_warning(elements, type_analysis_dict, description):
    """Processes elements from a 'duplicate type' warning."""
    for elemID in elements:
        try:
            elem = doc.GetElement(elemID)
            
            if not isinstance(elem, DB.ElementType):
                # Handle regular elements (not a type)
                try:
                    catName = elem.Category.Name if elem.Category else UNKNOWN_CATEGORY
                except AttributeError:
                    catName = NA_CATEGORY
                print(" \n " + output.linkify(elemID) + " \t " + catName + " \t ")
                continue

            # Process ElementType
            type_name_display = get_type_mark_or_name(elem)
            family_name, type_name_only = get_family_and_type_name(elem)
            type_id = elem.Id
            
            print("TYPE: {} {}".format(type_name_display, output.linkify(type_id)))
            print("   -> Family Name: {}".format(family_name))
            print("   -> Type Name: {}".format(type_name_only))

            if SHOW_PARAMETER_DETAILS:
                param_info = get_builtin_parameter_info(elem)
                if param_info:
                    print("   -> Available Parameters:")
                    for param_name, info in param_info.items():
                        print("      • {}: '{}' [{}]".format(param_name, info['value'], info['builtin_param']))

            instances = all_instances_by_type.get(type_id, [])
            instance_count = len(instances)
            print("   -> Count Element Instance = {}".format(instance_count))

            if instance_count > 0:
                category_groups = defaultdict(list)
                for instance in instances:
                    try:
                        cat_name = instance.Category.Name if instance.Category else UNKNOWN_CATEGORY
                        category_groups[cat_name].append(instance)
                    except AttributeError:
                        category_groups[UNKNOWN_CATEGORY].append(instance)
                
                for category, cat_instances in category_groups.items():
                    print("   -> {}: {} instances".format(category, len(cat_instances)))
                    for instance in cat_instances[:5]:
                        print("      - Instance: {}".format(output.linkify(instance.Id)))
                    if len(cat_instances) > 5:
                        remaining = len(cat_instances) - 5
                        print("      - ... and {} more instances".format(remaining))
            else:
                print("   -> No instances found using this type")
            
            print("")
            
            type_analysis_dict[type_id] = {
                'name': type_name_display,
                'family_name': family_name,
                'type_name': type_name_only,
                'instance_count': instance_count,
                'instances': instances,
                'warning_description': description
            }

        except Exception as e:
            print("   -> Error processing element {}: {}".format(elemID.IntegerValue, str(e)))


def process_generic_warning(elements):
    """Processes elements from a generic (non-duplicate type) warning."""
    for elemID in elements:
        try:
            elem = doc.GetElement(elemID)
            catName = elem.Category.Name if elem.Category else UNKNOWN_CATEGORY
        except AttributeError:
            catName = NA_CATEGORY
        print(" \n " + output.linkify(elemID) + " \t " + catName + " \t ")


# --- Main Processing Loop ---
# Pre-cache all instances in the model for performance
all_instances_by_type = get_all_instances_by_type(doc)

for warning in allWarnings:
    description = warning.GetDescriptionText()
    
    # Process description to create a concise heading
    try:
        descLen = description.index(".")
    except ValueError:
        descLen = len(description)
    
    limit = 50
    if descLen < limit:
        descHeading = description[:descLen]
    elif description.startswith("Mechanical") or description.startswith("Hydronic"):
        descHeading = description[:20] + "..."
    else:
        descHeading = description[:limit] + "..."

    # Process only warnings related to type marks
    if descHeading in typemarkWarning:
        count += 1
        elementsList = warning.GetFailingElements()
        
        print(coreutils.prepare_html_str("<hr>"))
        output.print_md("### Warning " + str(count))
        output.print_md("**Description:** " + description)
        
        is_duplicate_type = "duplicate" in description.lower() and "type" in description.lower()
        
        if is_duplicate_type:
            print("DUPLICATE TYPE WARNING DETECTED\n")
            process_duplicate_type_warning(elementsList, type_analysis, description)
        else:
            process_generic_warning(elementsList)

        # Collect data for the summary graph
        if descHeading not in graphHeadings:
            graphHeadings.append(descHeading)
        graphWarnData.append(descHeading)

# Enhanced Summary section for duplicate types
if type_analysis:
    print(coreutils.prepare_html_str("<hr>"))
    output.print_md("## ENHANCED DUPLICATE TYPE ANALYSIS SUMMARY")
    print("")
    
    summary_count = 0
    for type_id, data in type_analysis.items():
        summary_count += 1
        
        # Make type ID clickable
        clickable_type_id = output.linkify(type_id)
        
        print("{}. TYPE: {} {}".format(
            summary_count, 
            data['name'], 
            clickable_type_id
        ))
        print("   -> Family Name: {}".format(data['family_name']))
        print("   -> Type Name: {}".format(data['type_name']))
        print("   -> Count Element Instance = {}".format(data['instance_count']))
        
        if data['instance_count'] > 0:
            # Group by category for summary
            category_summary = defaultdict(int)
            for instance in data['instances']:
                try:
                    cat_name = instance.Category.Name if instance.Category else "Unknown Category"
                    category_summary[cat_name] += 1
                except AttributeError:
                    # Instance might not have a Category property
                    category_summary["Unknown Category"] += 1
            
            # Display category summary with better formatting
            for category, count in category_summary.items():
                print("   -> {}: {} instances".format(category, count))
        else:
            print("   -> No instances using this type")
        
        print("")
        print(coreutils.prepare_html_str("<hr style='border: 1px dashed #ccc; margin: 10px 0;'>"))

# Graph data preparation
warnSet = []
for i in graphHeadings:
    count = graphWarnData.count(i)        
    warnSet.append(count)

output.unfreeze()

# CHART OUTPUT
if CHARTS_AVAILABLE and ENABLE_CHART_OUTPUT:
    output = script.get_output()

    # Original Warning Types Chart
    try:
        chart = output.make_chart()
        chart.type = 'doughnut'
        chart.options.title = {'display': True, 'text': 'Warning Types Distribution'}

        chart.data.labels = graphHeadings
        chart.data.datasets = [{
            'label': 'Warning Types',
            'data': warnSet,
            'backgroundColor': colors[:len(warnSet)] if len(colors) >= len(warnSet) else colors * ((len(warnSet) // len(colors)) + 1)
        }]

        # Flexible chart size
        cat_count = len(graphHeadings)
        legend_len = len("".join(graphHeadings))
        legend_metric = cat_count*10 + legend_len

        if legend_metric < 450:
            chart.set_height(150)
        elif legend_metric < 900:
            chart.set_height(200)
        elif legend_metric < 1500:
            chart.set_height(250)
        else:
            chart.set_height(300)

        chart.draw()
    except Exception as e:
        print("Error creating warning types chart: {}".format(str(e)))

    # Function to get all element types and their instances by category
    def get_element_types_and_instances(category_name):
        """Get all element types of specified category and count their instances"""
        type_data = {}

        # Get all element types of the specified category
        collector = DB.FilteredElementCollector(doc)
        element_types = collector.OfClass(DB.ElementType).ToElements()

        for elem_type in element_types:
            try:
                if elem_type.Category and elem_type.Category.Name == category_name:
                    # Use the consolidated function to get a display name
                    family_name, type_name_only = get_family_and_type_name(elem_type)
                    type_name = u"{} - {}".format(family_name, type_name_only) if family_name != UNKNOWN_FAMILY else type_name_only
                    instances = get_all_instances_of_type(elem_type.Id)
                    instance_count = len(instances)

                    if instance_count > 0:  # Only include types that have instances
                        type_data[type_name] = instance_count
            except AttributeError:
                # Element type might not have a Category property
                continue

        return type_data

    # Chart 1: Structural Framing Instance Count per Type
    try:
        framing_data = get_element_types_and_instances("Structural Framing")

        if framing_data:
            output.print_md("---")
            chart_framing = output.make_chart()
            chart_framing.type = 'bar'
            chart_framing.options.title = {'display': True, 'text': 'Structural Framing - Instance Count per Type'}
            chart_framing.options.scales = {
                'yAxes': [{
                    'ticks': {
                        'beginAtZero': True,
                        'stepSize': 1
                    },
                    'scaleLabel': {
                        'display': True,
                        'labelString': 'Number of Instances'
                    }
                }],
                'xAxes': [{
                    'scaleLabel': {
                        'display': True,
                        'labelString': 'Element Types'
                    }
                }]
            }
            
            framing_labels = list(framing_data.keys())
            framing_counts = list(framing_data.values())
            
            chart_framing.data.labels = framing_labels
            chart_framing.data.datasets = [{
                'label': 'Instance Count',
                'data': framing_counts,
                'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'][:len(framing_counts)]
            }]
            
            # Dynamic height based on number of types
            if len(framing_labels) <= 5:
                chart_framing.set_height(200)
            elif len(framing_labels) <= 10:
                chart_framing.set_height(250)
            else:
                chart_framing.set_height(300)
            
            chart_framing.draw()
            
            # Print summary for Structural Framing
            print("")
            print("STRUCTURAL FRAMING SUMMARY:")
            total_framing_instances = sum(framing_counts)
            print("- Total Types: {}".format(len(framing_labels)))
            print("- Total Instances: {}".format(total_framing_instances))
            for type_name, count in sorted(framing_data.items(), key=lambda x: x[1], reverse=True):
                print("  • {}: {} instances".format(type_name, count))
    except Exception as e:
        print("Error creating framing chart: {}".format(str(e)))

    # Chart 2: Structural Columns Instance Count per Type
    try:
        column_data = get_element_types_and_instances("Structural Columns")

        if column_data:
            output.print_md("---")
            chart_column = output.make_chart()
            chart_column.type = 'bar'
            chart_column.options.title = {'display': True, 'text': 'Structural Columns - Instance Count per Type'}
            chart_column.options.scales = {
                'yAxes': [{
                    'ticks': {
                        'beginAtZero': True,
                        'stepSize': 1
                    },
                    'scaleLabel': {
                        'display': True,
                        'labelString': 'Number of Instances'
                    }
                }],
                'xAxes': [{
                    'scaleLabel': {
                        'display': True,
                        'labelString': 'Element Types'
                    }
                }]
            }
            
            column_labels = list(column_data.keys())
            column_counts = list(column_data.values())
            
            chart_column.data.labels = column_labels
            chart_column.data.datasets = [{
                'label': 'Instance Count',
                'data': column_counts,
                'backgroundColor': ['#4BC0C0', '#36A2EB', '#FF9F40', '#FF6384', '#9966FF', '#FFCE56', '#C9CBCF', '#4BC0C0', '#36A2EB', '#FF6384'][:len(column_counts)]
            }]
            
            # Dynamic height based on number of types
            if len(column_labels) <= 5:
                chart_column.set_height(200)
            elif len(column_labels) <= 10:
                chart_column.set_height(250)
            else:
                chart_column.set_height(300)
            
            chart_column.draw()
            
            # Print summary for Structural Columns
            print("")
            print("STRUCTURAL COLUMNS SUMMARY:")
            total_column_instances = sum(column_counts)
            print("- Total Types: {}".format(len(column_labels)))
            print("- Total Instances: {}".format(total_column_instances))
            for type_name, count in sorted(column_data.items(), key=lambda x: x[1], reverse=True):
                print("  • {}: {} instances".format(type_name, count))
    except Exception as e:
        print("Error creating column chart: {}".format(str(e)))

elif CHARTS_AVAILABLE:
    print("Chart output is disabled by ENABLE_CHART_OUTPUT flag")
else:
    print("Charts are not available in this pyRevit version")

# Timing
endtime = timer.get_time()
print(hmsTimer(endtime))