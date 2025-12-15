# -*- coding: utf-8 -*-
"""
Count Detail Item Reinforcement - Counts reinforcement detail items in current view by diameter.
Groups and counts detail items with "Detail Item_Tulangan" family name by their d_tul parameter values.
"""

__title__ = 'Count Detail Item Reinforcement'
__author__ = 'PrasKaa Team'
__doc__ = "Counts reinforcement detail items in current view by diameter."

import clr
import sys
import os

# Revit API imports
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

# PyRevit imports
from pyrevit import revit, forms, script, output
from pyrevit.revit import doc, uidoc

# Setup
logger = script.get_logger()
output_window = output.get_output()

def get_parameter_value(param):
    """
    Extract parameter value with robust error handling.
    Returns the value or None if not available.
    """
    if not param or not param.HasValue:
        return None

    try:
        storage_type = param.StorageType
        if storage_type == StorageType.Double:
            return param.AsDouble()
        elif storage_type == StorageType.Integer:
            return param.AsInteger()
        elif storage_type == StorageType.String:
            return param.AsString()
        else:
            return None
    except Exception as e:
        logger.warning("Error extracting parameter value: {}".format(str(e)))
        return None

def get_detail_item_location(item):
    """
    Extract location coordinates from a detail item.
    Returns XYZ point or None if location cannot be determined.
    """
    try:
        # Detail items are typically point-based
        if hasattr(item, 'Location') and item.Location:
            location = item.Location
            if hasattr(location, 'Point'):
                # Point location
                return location.Point
            elif hasattr(location, 'Curve'):
                # If it's a curve, get midpoint
                curve = location.Curve
                if curve:
                    return curve.Evaluate(0.5, True)  # Midpoint
    except Exception as e:
        logger.warning("Error getting location for item {}: {}".format(item.Id, str(e)))

    return None

def calculate_distance(point1, point2):
    """
    Calculate Euclidean distance between two XYZ points in plan view (X, Y only).
    Returns distance in feet (Revit units).
    """
    if not point1 or not point2:
        return float('inf')

    try:
        # Calculate distance in plan view (ignoring Z for reinforcement layout)
        dx = point1.X - point2.X
        dy = point1.Y - point2.Y
        return (dx**2 + dy**2)**0.5
    except:
        return float('inf')

def cluster_by_proximity(items, max_distance_mm):
    """
    Cluster items based on proximity using a simple iterative clustering algorithm.
    Items within max_distance_mm of each other are grouped together.

    Args:
        items: List of detail items with location data
        max_distance_mm: Maximum distance in mm (260mm)

    Returns:
        List of clusters, where each cluster is a list of items
    """
    if not items:
        return []

    # Extract locations for all items
    item_locations = []
    for item in items:
        location = get_detail_item_location(item)
        if location:
            item_locations.append((item, location))
        else:
            # Items without location get their own cluster
            item_locations.append((item, None))

    clusters = []

    # Simple clustering: start with first item, then add nearby items iteratively
    remaining_items = item_locations[:]

    while remaining_items:
        # Start a new cluster with the first remaining item
        current_cluster = [remaining_items[0]]
        remaining_items.pop(0)

        # Find all items within range of any item in current cluster
        added_to_cluster = True
        while added_to_cluster:
            added_to_cluster = False
            i = 0
            while i < len(remaining_items):
                item, item_location = remaining_items[i]

                # Check if this item is close to any item in the current cluster
                close_to_cluster = False
                for cluster_item, cluster_location in current_cluster:
                    if cluster_location and item_location:
                        distance = calculate_distance(cluster_location, item_location)
                        # Convert feet distance to mm for comparison
                        distance_mm = distance * 304.8
                        if distance_mm <= max_distance_mm:
                            close_to_cluster = True
                            break
                    elif not cluster_location and not item_location:
                        # Both items have no location, group them together
                        close_to_cluster = True
                        break

                if close_to_cluster:
                    current_cluster.append(remaining_items.pop(i))
                    added_to_cluster = True
                else:
                    i += 1

        # Add completed cluster to results
        clusters.append(current_cluster)

    return clusters

def collect_reinforcement_detail_items(active_view):
    """
    Collect all detail items in the active view that are reinforcement items.
    Filters by family name "Detail Item_Tulangan".
    """
    reinforcement_items = []

    try:
        # Collect all detail components in the active view
        collector = FilteredElementCollector(doc, active_view.Id)
        detail_items = collector.OfCategory(BuiltInCategory.OST_DetailComponents).WhereElementIsNotElementType().ToElements()

        for item in detail_items:
            try:
                # Check if it's a FamilyInstance
                if not isinstance(item, FamilyInstance):
                    continue

                # Check family name
                family_name = item.Symbol.Family.Name if item.Symbol and item.Symbol.Family else ""
                if family_name != "Detail Item_Tulangan":
                    continue

                reinforcement_items.append(item)

            except Exception as e:
                logger.warning("Error processing detail item {}: {}".format(item.Id, str(e)))
                continue

    except Exception as e:
        logger.error("Error collecting detail items: {}".format(str(e)))

    return reinforcement_items

def extract_d_tul_values(reinforcement_items, clustering_distance_mm=260.0):
    """
    Extract d_tul parameter values from reinforcement detail items and cluster by location.
    Returns a dictionary grouping items by d_tul value with spatial clusters.

    Args:
        reinforcement_items: List of detail items to process
        clustering_distance_mm: Maximum distance in mm for spatial clustering
    """
    diameter_groups = {}
    extraction_stats = {
        'total_items': len(reinforcement_items),
        'items_with_d_tul': 0,
        'unique_diameters': 0,
        'total_clusters': 0,
        'errors': []
    }

    # First pass: group by diameter
    diameter_item_map = {}

    for item in reinforcement_items:
        try:
            # Get d_tul parameter
            d_tul_param = item.LookupParameter('d_tul')
            if not d_tul_param:
                continue

            d_tul_value = get_parameter_value(d_tul_param)
            if d_tul_value is None:
                continue

            # Convert to string key for grouping (to handle floating point precision)
            diameter_key = "{:.4f}".format(d_tul_value)

            if diameter_key not in diameter_item_map:
                diameter_item_map[diameter_key] = {
                    'diameter': d_tul_value,
                    'items': []
                }

            diameter_item_map[diameter_key]['items'].append(item)
            extraction_stats['items_with_d_tul'] += 1

        except Exception as e:
            extraction_stats['errors'].append("Item {}: {}".format(item.Id, str(e)))
            continue

    # Second pass: cluster items within each diameter by proximity
    for diameter_key, diameter_data in diameter_item_map.items():
        items = diameter_data['items']
        diameter_value = diameter_data['diameter']

        if not items:
            continue

        # Cluster items by proximity using user-specified threshold
        clusters = cluster_by_proximity(items, clustering_distance_mm)

        # Build cluster data
        cluster_data = {}
        total_count = 0

        for i, cluster in enumerate(clusters):
            cluster_id = "Group {}".format(chr(65 + i))  # A, B, C, etc.
            cluster_count = len(cluster)

            # Calculate approximate centroid location for the cluster
            locations = []
            for item, _ in cluster:
                loc = get_detail_item_location(item)
                if loc:
                    locations.append(loc)

            centroid_location = None
            if locations:
                # Calculate centroid
                avg_x = sum(loc.X for loc in locations) / len(locations)
                avg_y = sum(loc.Y for loc in locations) / len(locations)
                centroid_location = XYZ(avg_x, avg_y, 0)

            cluster_data[cluster_id] = {
                'count': cluster_count,
                'items': [item.Id for item, _ in cluster],
                'centroid': centroid_location
            }

            total_count += cluster_count
            extraction_stats['total_clusters'] += 1

        # Store in final diameter groups structure
        diameter_groups[diameter_key] = {
            'diameter': diameter_value,
            'count': total_count,
            'items': [item.Id for item in items],
            'clusters': cluster_data
        }

    extraction_stats['unique_diameters'] = len(diameter_groups)
    return diameter_groups, extraction_stats

def get_available_views():
    """
    Get all views that are suitable for detail item analysis.
    Returns views that support detail items (plans, sections, elevations, details).
    """
    collector = FilteredElementCollector(doc).OfClass(View)
    all_views = collector.ToElements()

    suitable_views = []
    for view in all_views:
        # Skip templates and system views
        if view.IsTemplate:
            continue

        # Include views that typically contain detail items
        if view.ViewType in [ViewType.FloorPlan, ViewType.EngineeringPlan,
                           ViewType.Section, ViewType.Elevation, ViewType.Detail]:
            suitable_views.append(view)

    # Sort by name for better UX
    return sorted(suitable_views, key=lambda v: v.Name)

def select_views_dialog(available_views):
    """
    Show a dialog for selecting multiple views to analyze.
    Returns list of selected views.
    """
    if not available_views:
        forms.alert("No suitable views found in the document.", exitscript=True)
        return []

    # Create options for the multi-select dialog
    view_options = []
    for view in available_views:
        view_options.append({
            'name': view.Name,
            'value': view,
            'description': '{} ({})'.format(view.Name, view.ViewType)
        })

    # Show multi-select dialog
    selected_views = forms.SelectFromList.show(
        [opt['name'] for opt in view_options],
        title="Select Views to Analyze",
        description="Choose one or more views to count reinforcement detail items:",
        multiselect=True,
        button_name="Analyze Selected Views"
    )

    if not selected_views:
        forms.alert("No views selected. Exiting.", exitscript=True)
        return []

    # Convert selected names back to view objects
    selected_view_objects = []
    name_to_view = {opt['name']: opt['value'] for opt in view_options}

    for selected_name in selected_views:
        if selected_name in name_to_view:
            selected_view_objects.append(name_to_view[selected_name])

    return selected_view_objects

def get_clustering_distance():
    """
    Get the clustering distance from user input.
    Returns distance in mm (default 260mm).
    """
    default_distance = 260

    # Show input dialog for clustering distance
    distance_input = forms.ask_for_string(
        default=str(default_distance),
        prompt="Enter maximum distance for spatial clustering (mm):",
        title="Clustering Distance Setting"
    )

    if distance_input and distance_input.strip():
        try:
            distance = float(distance_input.strip())
            if distance > 0:
                return distance
            else:
                forms.alert("Distance must be greater than 0. Using default 260mm.", title="Invalid Input")
                return default_distance
        except ValueError:
            forms.alert("Invalid number format. Using default 260mm.", title="Invalid Input")
            return default_distance
    else:
        # User cancelled or empty input, use default
        return default_distance

def display_reinforcement_report(view_results, clustering_distance):
    """
    Display the reinforcement counting report for multiple views using pyRevit's table formatting.
    Each view gets its own section with the view name as header.
    """
    output_window.print_md("# Detail Item Reinforcement Count")
    output_window.print_md("---")

    total_views = len(view_results)
    total_items_all_views = sum(stats['total_items'] for _, _, stats in view_results)
    total_bars_all_views = 0

    output_window.print_md("**Analysis Summary:** {} views processed, {} total items found".format(
        total_views, total_items_all_views))
    output_window.print_md("**Clustering Distance:** {} mm".format(clustering_distance))
    output_window.print_md("")

    for view_name, diameter_groups, stats in view_results:
        # View header
        output_window.print_md("## View: {}".format(view_name))
        output_window.print_md("")

        # View summary
        output_window.print_md("**View Summary:** {} items found, {} with d_tul parameter, {} unique diameters, {} spatial groups".format(
            stats['total_items'], stats['items_with_d_tul'], stats['unique_diameters'], stats.get('total_clusters', 0)))

        if stats['errors']:
            output_window.print_md("*Note: {} items had extraction errors*".format(len(stats['errors'])))

        if not diameter_groups:
            output_window.print_md("**No reinforcement detail items found in this view.**")
            output_window.print_md("---")
            continue

        # Display diameter and cluster breakdown
        view_total_bars = 0

        # Sort by diameter value
        sorted_diameters = sorted(diameter_groups.items(), key=lambda x: x[1]['diameter'])

        for diameter_key, data in sorted_diameters:
            diameter_mm = int(round(data['diameter'] * 304.8))  # Convert feet to mm and round to integer
            diameter_total = data['count']
            view_total_bars += diameter_total

            output_window.print_md("**Diameter: {} mm** (d_tul = {:.4f}, Total: {} bars)".format(
                diameter_mm, data['diameter'], diameter_total))

            # Show clusters within this diameter
            clusters = data.get('clusters', {})
            if clusters:
                cluster_items = []
                for cluster_id, cluster_data in sorted(clusters.items()):
                    count = cluster_data['count']
                    centroid = cluster_data.get('centroid')

                    # Format location info
                    location_info = ""
                    if centroid:
                        # Coordinates are already in project units (typically mm), display as-is
                        x_coord = int(round(centroid.X))
                        y_coord = int(round(centroid.Y))
                        location_info = " (~X: {}, Y: {})".format(x_coord, y_coord)

                    cluster_items.append({
                        'name': cluster_id,
                        'count': count,
                        'location': location_info
                    })

                # Display clusters as a simple list
                for cluster in cluster_items:
                    output_window.print_md("- **{}**: {} bars{}".format(
                        cluster['name'], cluster['count'], cluster['location']))

            output_window.print_md("")

        output_window.print_md("")
        output_window.print_md("**Total reinforcement bars in {}: {}**".format(view_name, view_total_bars))
        output_window.print_md("---")

        total_bars_all_views += view_total_bars

    # Overall summary
    if total_views > 1:
        output_window.print_md("## Overall Summary")
        output_window.print_md("**Total views analyzed:** {}".format(total_views))
        output_window.print_md("**Total reinforcement bars across all views:** {}".format(total_bars_all_views))

def main():
    """Main execution function."""
    output_window.set_title("Detail Item Reinforcement Count")
    output_window.freeze()

    try:
        # Get available views
        available_views = get_available_views()
        if not available_views:
            forms.alert("No suitable views found in the document.", exitscript=True)
            return

        # Show view selection dialog
        selected_views = select_views_dialog(available_views)
        if not selected_views:
            return

        # Get clustering distance from user
        clustering_distance = get_clustering_distance()
        output_window.print_md("Using clustering distance: {} mm".format(clustering_distance))

        # Process each selected view
        view_results = []
        total_processed = 0

        for view in selected_views:
            view_name = view.Name if view.Name else "Unnamed View"

            output_window.print_md("Processing view: {}...".format(view_name))

            # Collect reinforcement detail items for this view
            reinforcement_items = collect_reinforcement_detail_items(view)

            if reinforcement_items:
                # Extract d_tul values and group by diameter with spatial clustering
                diameter_groups, stats = extract_d_tul_values(reinforcement_items, clustering_distance)
                view_results.append((view_name, diameter_groups, stats))
                total_processed += 1
            else:
                # Add empty result for views with no items
                empty_stats = {
                    'total_items': 0,
                    'items_with_d_tul': 0,
                    'unique_diameters': 0,
                    'total_clusters': 0,
                    'errors': []
                }
                view_results.append((view_name, {}, empty_stats))

        if total_processed == 0:
            output_window.print_md("No reinforcement detail items found in any of the selected views.")
            output_window.unfreeze()
            return

        # Display consolidated report
        display_reinforcement_report(view_results, clustering_distance)

    except Exception as e:
        logger.error("Critical error in Count Detail Item Reinforcement: {}".format(str(e)))
        forms.alert("An error occurred: {}".format(str(e)), title="Error")
    finally:
        output_window.unfreeze()

if __name__ == '__main__':
    main()