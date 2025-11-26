# -*- coding: utf-8 -*-
"""Smart Tag System - Core Tagging Engine"""

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
import math

class SmartTagEngine:
    """Core engine for intelligent tag placement"""
    
    def __init__(self, doc):
        self.doc = doc
        self.debug_enabled = False  # Debug logging toggle
        self.stats = {
            'framing': 0,
            'columns': 0,
            'walls': 0,
            'errors': []
        }
        self.tag_cache = {}  # Cache for tag collections per view
    
    def get_structural_plans(self):
        """Get all structural plan views using ViewType.EngineeringPlan"""
        collector = FilteredElementCollector(self.doc)
        views = collector.OfClass(View).ToElements()

        structural_plans = []
        for view in views:
            # Use ViewType.EngineeringPlan for structural plans
            if view.ViewType == ViewType.EngineeringPlan:
                structural_plans.append(view)

        # Sort by elevation (top to bottom) instead of alphabetical
        return sorted(structural_plans, key=lambda v: v.GenLevel.Elevation if v.GenLevel else 0, reverse=True)

    def set_debug(self, enabled):
        """Enable/disable debug logging"""
        self.debug_enabled = enabled
        # Only print status in verbose mode
        if self.debug_enabled:
            print("Smart Tag Debug: ENABLED")
        # Silent in quiet mode (no print statement)

    def is_element_tagged_in_view(self, element, view):
        """Check if element already has a tag in the view using cached tag collections"""
        element_id = element.Id

        # Cache tag collection per view - collect only once per view
        if view.Id not in self.tag_cache:
            self.tag_cache[view.Id] = FilteredElementCollector(self.doc, view.Id) \
                .OfClass(IndependentTag).WhereElementIsNotElementType().ToElements()

        # Use cached tags for this view
        tags = self.tag_cache[view.Id]

        for tag in tags:
            try:
                # Use GetTaggedLocalElementIds() for robust checking
                tagged_ids = tag.GetTaggedLocalElementIds()

                # Check if target element ID is in the tagged elements
                if element_id in tagged_ids:
                    return True

            except Exception as e:
                # Handle any issues with tag processing
                self.stats['errors'].append("Error checking tag {}: {}".format(tag.Id, str(e)))
                continue

        return False
    
    def get_tag_type(self, tag_type_name, category):
        """Get tag type by name and category - supports 'Family: Type' format"""
        collector = FilteredElementCollector(self.doc)
        
        # Get appropriate tag category
        if category == BuiltInCategory.OST_StructuralFraming:
            tag_category = BuiltInCategory.OST_StructuralFramingTags
        elif category == BuiltInCategory.OST_StructuralColumns:
            tag_category = BuiltInCategory.OST_StructuralColumnTags
        elif category == BuiltInCategory.OST_Walls:
            tag_category = BuiltInCategory.OST_WallTags
        else:
            return None
        
        tag_types = collector.OfCategory(tag_category).WhereElementIsElementType().ToElements()
        
        if self.debug_enabled:
            print("\n=== DEBUG get_tag_type ===")
            print("Looking for: '{}'".format(tag_type_name))
            print("Category: {}".format(category))
            print("Available tag types:")
        
        # Parse the tag_type_name if it's in "Family: Type" format
        if ": " in tag_type_name:
            parts = tag_type_name.split(": ", 1)  # Split only on first occurrence
            family_name = parts[0].strip()
            type_name = parts[1].strip()
            
            if self.debug_enabled:
                print("Parsed - Family: '{}', Type: '{}'".format(family_name, type_name))
            
            # Search for exact match on both family and type name
            for tag_type in tag_types:
                try:
                    # Get type name from parameter
                    current_type_name = tag_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                    if current_type_name:
                        current_type_name = current_type_name.AsString()
                    else:
                        current_type_name = tag_type.Name if hasattr(tag_type, 'Name') else ""
                    
                    current_family_name = tag_type.FamilyName if hasattr(tag_type, 'FamilyName') else ""
                    
                    if self.debug_enabled:
                        print("  Checking: '{}' - Family: '{}', Type: '{}'".format(
                            tag_type.Id, current_family_name, current_type_name))
                    
                    # Match both family and type name
                    if current_family_name == family_name and current_type_name == type_name:
                        if self.debug_enabled:
                            print("  >>> MATCH FOUND! Using tag type ID: {}".format(tag_type.Id))
                        return tag_type
                except Exception as e:
                    if self.debug_enabled:
                        print("  Error checking tag: {}".format(str(e)))
                    continue
        else:
            # Legacy format: try to match by FamilyName or Name only
            if self.debug_enabled:
                print("Legacy format (no colon separator)")
            
            for tag_type in tag_types:
                try:
                    if self.debug_enabled:
                        print("  Checking: '{}' - FamilyName: '{}', Name: '{}'".format(
                            tag_type.Id, tag_type.FamilyName, tag_type.Name))
                    
                    if tag_type.FamilyName == tag_type_name or tag_type.Name == tag_type_name:
                        if self.debug_enabled:
                            print("  >>> MATCH FOUND! Using tag type ID: {}".format(tag_type.Id))
                        return tag_type
                except:
                    continue
        
        if self.debug_enabled:
            print("  >>> NO MATCH FOUND!")
        
        # If not found, return None (don't auto-select first one)
        return None
    
    def mm_to_feet(self, mm):
        """Convert millimeters to feet"""
        return mm / 304.8
    
    def calculate_framing_tag_position(self, beam, view, offset_mm):
        """Calculate tag position for structural framing"""
        try:
            # Get beam location curve
            location = beam.Location
            if not isinstance(location, LocationCurve):
                return None
            
            curve = location.Curve
            midpoint = curve.Evaluate(0.5, True)  # Get midpoint of beam
            
            # Get beam direction
            start_point = curve.GetEndPoint(0)
            end_point = curve.GetEndPoint(1)
            direction = (end_point - start_point).Normalize()
            
            # Get perpendicular vector (rotate 90 degrees in plan view)
            perpendicular = XYZ(-direction.Y, direction.X, 0).Normalize()
            
            # Get beam width from parameter "b" using LookupParameter
            beam_width = 0
            beam_type = self.doc.GetElement(beam.GetTypeId())
            b_param = beam_type.LookupParameter("b")

            if b_param and b_param.HasValue:
                beam_width = b_param.AsDouble()
            else:
                # If "b" parameter not found, skip this beam
                return None
            
            # Calculate offset distance
            offset_feet = self.mm_to_feet(offset_mm)
            total_offset = (beam_width / 2.0) + offset_feet
            
            # Calculate tag position
            tag_position = midpoint + (perpendicular * total_offset)
            
            return tag_position
            
        except Exception as e:
            self.stats['errors'].append("Framing {}: {}".format(beam.Id, str(e)))
            return None
    
    def calculate_column_tag_position(self, column, view, offset_mm):
        """Calculate tag position for structural column with size-based offset"""
        try:
            # Get column bounding box in view
            bbox = column.get_BoundingBox(view)
            if not bbox:
                return None

            # Calculate column size for adaptive offset
            width = bbox.Max.X - bbox.Min.X
            height = bbox.Max.Y - bbox.Min.Y
            column_size = max(width, height)  # Use largest dimension

            # Size-based factor (30% of column size)
            size_factor = column_size * 0.3

            # Base offset from config
            base_offset = self.mm_to_feet(offset_mm)

            # Total adaptive offset
            total_offset = base_offset + size_factor

            # Get top-right corner (Max X, Max Y)
            corner = XYZ(bbox.Max.X, bbox.Max.Y, bbox.Min.Z)

            # Apply diagonal offset with size-based adjustment
            tag_position = corner + XYZ(total_offset, total_offset, 0)

            return tag_position

        except Exception as e:
            self.stats['errors'].append("Column {}: {}".format(column.Id, str(e)))
            return None
    
    def calculate_wall_tag_position(self, wall, view, offset_mm):
        """Calculate tag position and orientation for wall with smart perpendicular offset"""
        try:
            # Get wall location curve
            location = wall.Location
            if not isinstance(location, LocationCurve):
                return None, TagOrientation.Horizontal

            curve = location.Curve
            midpoint = curve.Evaluate(0.5, True)  # Get midpoint of wall

            # Get wall direction (start to end)
            start_point = curve.GetEndPoint(0)
            end_point = curve.GetEndPoint(1)
            direction = (end_point - start_point).Normalize()

            # Determine if wall is more horizontal or vertical
            abs_x = abs(direction.X)
            abs_y = abs(direction.Y)

            if abs_x > abs_y:
                # Wall is more horizontal - offset upward/downward
                perpendicular = XYZ(0, 1, 0)  # Up direction
                orientation = TagOrientation.Horizontal
            else:
                # Wall is more vertical - offset left/right
                perpendicular = XYZ(1, 0, 0)  # Right direction
                orientation = TagOrientation.Vertical

            # Get wall thickness
            wall_width = wall.Width

            # Calculate offset distance
            offset_feet = self.mm_to_feet(offset_mm)
            total_offset = (wall_width / 2.0) + offset_feet

            # Calculate tag position - perpendicular to wall direction
            tag_position = midpoint + (perpendicular * total_offset)

            return tag_position, orientation

        except Exception as e:
            self.stats['errors'].append("Wall {}: {}".format(wall.Id, str(e)))
            return None, TagOrientation.Horizontal
    
    def tag_elements_in_view(self, view, config, tag_mode):
        """Tag all enabled categories in a view using batch processing"""
        view_stats = {
            'framing': 0,
            'columns': 0,
            'walls': 0
        }

        try:
            # Phase 1: Prepare all tag data
            tag_batch = self._prepare_tag_batch(view, config, tag_mode)

            # Phase 2: Create tags in batch
            batch_stats = self._create_tags_batch(view, tag_batch)

            # Update view stats
            view_stats.update(batch_stats)

            return view_stats

        except Exception as e:
            self.stats['errors'].append("View {}: {}".format(view.Name, str(e)))
            return view_stats
    
    def _get_all_structural_elements(self, view):
        """Get structural elements by category - Revit 2024+ compatible"""
        elements_by_category = {}

        # Collect each category separately using FilteredElementCollector
        # Still optimized: 3 collectors per view (same as before optimization)

        # Framing elements
        collector = FilteredElementCollector(self.doc, view.Id)
        elements_by_category['framing'] = collector.OfCategory(BuiltInCategory.OST_StructuralFraming) \
            .WhereElementIsNotElementType().ToElements()

        # Column elements
        collector = FilteredElementCollector(self.doc, view.Id)
        elements_by_category['columns'] = collector.OfCategory(BuiltInCategory.OST_StructuralColumns) \
            .WhereElementIsNotElementType().ToElements()

        # Wall elements
        collector = FilteredElementCollector(self.doc, view.Id)
        elements_by_category['walls'] = collector.OfCategory(BuiltInCategory.OST_Walls) \
            .WhereElementIsNotElementType().ToElements()

        return elements_by_category

    def _prepare_tag_batch(self, view, config, tag_mode):
        """Phase 1: Prepare all tag data using optimized element collection"""
        tag_batch = []

        # Get view level for vertical element filtering
        view_level = self.get_view_level(view)

        # Get structural elements grouped by category
        elements_by_category = self._get_all_structural_elements(view)

        # Process each category
        categories_to_process = []

        # Structural Framing
        if config['structural_framing']['enabled']:
            categories_to_process.append({
                'category': BuiltInCategory.OST_StructuralFraming,
                'config_key': 'structural_framing',
                'stat_key': 'framing',
                'elements_key': 'framing'
            })

        # Structural Columns
        if config['structural_column']['enabled']:
            categories_to_process.append({
                'category': BuiltInCategory.OST_StructuralColumns,
                'config_key': 'structural_column',
                'stat_key': 'columns',
                'elements_key': 'columns'
            })

        # Walls
        if config['walls']['enabled']:
            categories_to_process.append({
                'category': BuiltInCategory.OST_Walls,
                'config_key': 'walls',
                'stat_key': 'walls',
                'elements_key': 'walls'
            })

        # Process each category using pre-grouped elements
        for cat_info in categories_to_process:
            category = cat_info['category']
            config_key = cat_info['config_key']
            stat_key = cat_info['stat_key']
            elements_key = cat_info['elements_key']

            cat_config = config[config_key]

            # Get tag type
            tag_type = self.get_tag_type(cat_config['tag_type_name'], category)
            if not tag_type:
                error_msg = "View {}: Tag type '{}' not found for {}. Please check Settings.".format(
                    view.Name,
                    cat_config['tag_type_name'],
                    config_key
                )
                self.stats['errors'].append(error_msg)
                continue  # Skip this category for this view

            # Get elements directly from pre-grouped collection
            elements = elements_by_category[elements_key]

            # Prepare tag data for each element
            for element in elements:
                try:
                    # Check if already tagged
                    if tag_mode == 'untagged_only':
                        if self.is_element_tagged_in_view(element, view):
                            continue

                    # EARLY LEVEL FILTERING for vertical elements (columns and walls)
                    if self._is_vertical_element(element):
                        if not self.should_tag_vertical_element(element, view_level):
                            continue  # Skip this element, don't calculate expensive geometry

                    # Calculate tag position and orientation based on category
                    tag_position = None
                    tag_orientation = TagOrientation.Horizontal  # Default

                    if category == BuiltInCategory.OST_StructuralFraming:
                        tag_position = self.calculate_framing_tag_position(
                            element, view, cat_config['offset_mm']
                        )
                    elif category == BuiltInCategory.OST_StructuralColumns:
                        tag_position = self.calculate_column_tag_position(
                            element, view, cat_config['offset_mm']
                        )
                    elif category == BuiltInCategory.OST_Walls:
                        tag_position, tag_orientation = self.calculate_wall_tag_position(
                            element, view, cat_config['offset_mm']
                        )

                    if tag_position:
                        tag_batch.append({
                            'element': element,
                            'position': tag_position,
                            'orientation': tag_orientation,
                            'category': stat_key,
                            'tag_type': tag_type  # Add tag type to batch data
                        })

                except Exception as e:
                    self.stats['errors'].append("Error preparing tag for {}: {}".format(element.Id, str(e)))

        return tag_batch

    def _create_tags_batch(self, view, tag_batch):
        """Phase 2: Create all tags in batch transactions"""
        batch_stats = {
            'framing': 0,
            'columns': 0,
            'walls': 0
        }

        if not tag_batch:
            return batch_stats

        # Group by category for better error handling
        category_batches = {}
        for tag_data in tag_batch:
            cat = tag_data['category']
            if cat not in category_batches:
                category_batches[cat] = []
            category_batches[cat].append(tag_data)

        # Create tags per category batch
        for category, batch in category_batches.items():
            try:
                with Transaction(self.doc, "Batch Tag Creation - {}".format(category)) as t:
                    t.Start()

                    created_count = 0
                    for tag_data in batch:
                        try:
                            reference = Reference(tag_data['element'])
                            tag = IndependentTag.Create(
                                self.doc,
                                view.Id,
                                reference,
                                False,  # addLeader
                                TagMode.TM_ADDBY_CATEGORY,
                                tag_data['orientation'],
                                tag_data['position']
                            )

                            if tag:
                                # Change tag type to the one specified in settings
                                tag.ChangeTypeId(tag_data['tag_type'].Id)
                                
                                created_count += 1
                                batch_stats[tag_data['category']] += 1
                                self.stats[tag_data['category']] += 1
                            else:
                                self.stats['errors'].append("Failed to create tag for element {}".format(tag_data['element'].Id))

                        except Exception as e:
                            self.stats['errors'].append("Error creating tag for {}: {}".format(tag_data['element'].Id, str(e)))

                    t.Commit()

            except Exception as e:
                self.stats['errors'].append("Batch creation failed for {}: {}".format(category, str(e)))

        return batch_stats

    def get_statistics(self):
        """Get tagging statistics"""
        return self.stats
    
    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            'framing': 0,
            'columns': 0,
            'walls': 0,
            'errors': []
        }

    def reset_cache(self):
        """Reset tag cache between runs"""
        self.tag_cache = {}

    def get_view_level(self, view):
        """Get the level associated with a view using GenLevel"""
        try:
            # Use GenLevel like in AutoDimensionColumn script
            return view.GenLevel
        except:
            return None

    def get_element_base_level(self, element):
        """Get base level of vertical element (column/wall)"""
        try:
            if element.Category.Id == BuiltInCategory.OST_StructuralColumns:
                # For columns
                base_param = element.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
                if base_param and base_param.AsElementId():
                    return self.doc.GetElement(base_param.AsElementId())
            elif element.Category.Id == BuiltInCategory.OST_Walls:
                # For walls - use WALL_BASE_LEVEL (returns ElementId)
                base_param = element.get_Parameter(BuiltInParameter.WALL_BASE_LEVEL)
                if base_param and base_param.AsElementId():
                    return self.doc.GetElement(base_param.AsElementId())
        except:
            pass
        return None

    def get_element_top_level(self, element):
        """Get top level of vertical element (column/wall)"""
        try:
            if element.Category.Id == BuiltInCategory.OST_StructuralColumns:
                # For columns - use FAMILY_TOP_LEVEL_PARAM
                top_param = element.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
                if top_param and top_param.AsElementId():
                    return self.doc.GetElement(top_param.AsElementId())

            elif element.Category.Id == BuiltInCategory.OST_Walls:
                # For walls - use WALL_TOP_CONSTRAINT first
                top_param = element.get_Parameter(BuiltInParameter.WALL_TOP_CONSTRAINT)
                if top_param and top_param.AsElementId():
                    return self.doc.GetElement(top_param.AsElementId())

                # Fallback: WALL_HEIGHT_TYPE
                height_type_param = element.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
                if height_type_param and height_type_param.AsElementId():
                    height_type = self.doc.GetElement(height_type_param.AsElementId())
                    # Check if it's a level
                    if isinstance(height_type, Level):
                        return height_type

                # Last fallback: calculate from base + height
                base_level = self.get_element_base_level(element)
                if base_level:
                    height_param = element.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
                    if height_param and height_param.HasValue:
                        height = height_param.AsDouble()
                        # Find level at base elevation + height
                        all_levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()
                        target_elevation = base_level.Elevation + height
                        # Find closest level above target elevation
                        above_levels = [lvl for lvl in all_levels if lvl.Elevation >= target_elevation]
                        if above_levels:
                            return min(above_levels, key=lambda x: x.Elevation)

        except Exception as e:
            print("Error getting top level for element {}: {}".format(element.Id, str(e)))

        return None

    def _is_vertical_element(self, element):
        """Check if element is vertical (columns or walls) based on category name"""
        try:
            category_name = element.Category.Name.lower()
            return ('column' in category_name) or ('wall' in category_name)
        except:
            return False

    def should_tag_vertical_element(self, element, view_level):
        """Check if vertical element should be tagged based on level constraints"""
        if not view_level:
            return True

        # Use different logic for different element types
        category_name = element.Category.Name.lower()
        if 'column' in category_name:
            # Use same logic as AutoDimensionColumn script for columns
            return self._should_tag_column_like_autodimension(element, view_level)
        elif 'wall' in category_name:
            # Use level relationship logic for walls
            return self._should_tag_wall_by_level_relationship(element, view_level)

        return True  # Default for other categories

    def _should_tag_column_like_autodimension(self, column, view_level):
        """Check if column should be tagged using AutoDimensionColumn logic"""
        try:
            view_elevation = view_level.Elevation

            # Get column top level/offset
            top_level_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
            top_offset_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)

            if top_level_param and top_level_param.HasValue:
                top_level_id = top_level_param.AsElementId()
                if top_level_id and top_level_id != ElementId.InvalidElementId:
                    top_level = self.doc.GetElement(top_level_id)
                    if top_level:
                        top_elevation = top_level.Elevation

                        # Add top offset if exists
                        if top_offset_param and top_offset_param.HasValue:
                            top_elevation += top_offset_param.AsDouble()

                        # Column continues upward if top is above current level
                        return top_elevation > view_elevation

            return True  # Default: include if can't determine

        except Exception as e:
            return True  # Default: include if error

    def get_wall_base_elevation(self, wall):
        """Get wall base elevation using Base Constraint + Base Offset"""
        try:
            # Try different parameter names for Base Constraint
            base_constraint_names = ["Base Constraint", "Base Level", "Wall Base Constraint"]

            for constraint_name in base_constraint_names:
                base_constraint_param = wall.LookupParameter(constraint_name)
                if base_constraint_param and base_constraint_param.HasValue:
                    if base_constraint_param.StorageType == StorageType.ElementId:
                        level_id = base_constraint_param.AsElementId()
                        if level_id and level_id != ElementId.InvalidElementId:
                            level = self.doc.GetElement(level_id)
                            if level and isinstance(level, Level):
                                base_elevation = level.Elevation

                                # Add Base Offset if exists
                                base_offset_param = wall.LookupParameter("Base Offset")
                                if base_offset_param and base_offset_param.HasValue:
                                    base_offset = base_offset_param.AsDouble()
                                    base_elevation += base_offset

                                return base_elevation

            return None

        except Exception as e:
            return None

    def _should_tag_wall_by_level_relationship(self, wall, view_level):
        """Check if wall should be tagged based on level relationships"""
        try:
            view_elevation = view_level.Elevation
            if self.debug_enabled:
                print("DEBUG WALL FILTER: Wall {} in view '{}' ({:.2f} ft)".format(
                    wall.Id, view_level.Name, view_elevation))

            # Get base elevation directly
            base_elevation = self.get_wall_base_elevation(wall)
            if self.debug_enabled:
                print("DEBUG WALL FILTER: Base elevation: {:.2f} ft".format(base_elevation or 0))
            if base_elevation is None:
                if self.debug_enabled:
                    print("DEBUG WALL FILTER: No base elevation found → TAG (default)")
                return True

            # Get top elevation using wall-specific logic
            top_elevation = self._get_wall_top_elevation_from_base(wall, base_elevation)
            if self.debug_enabled:
                print("DEBUG WALL FILTER: Top elevation: {:.2f} ft".format(top_elevation or 0))
            if top_elevation is None:
                if self.debug_enabled:
                    print("DEBUG WALL FILTER: No top elevation found → TAG (default)")
                return True

            # Wall continues upward if top is above current level
            should_tag = top_elevation > view_elevation
            if self.debug_enabled:
                print("DEBUG WALL FILTER: {:.2f} > {:.2f} = {} → {}".format(
                    top_elevation if top_elevation is not None else 0,
                    view_elevation,
                    should_tag,
                    "TAG" if should_tag else "NO TAG"))

            return should_tag

        except Exception as e:
            if self.debug_enabled:
                print("DEBUG WALL FILTER: Error: {} → TAG (default)".format(str(e)))
            return True  # Default: include if error

    def _get_wall_top_elevation_from_base(self, wall, base_elevation):
        """Get wall top elevation by searching for Top Constraint parameter"""
        try:
            if self.debug_enabled:
                print("DEBUG TOP ELEV: Starting for wall {}".format(wall.Id))

            # Find Top Constraint parameter by searching all parameters
            top_constraint_param = None
            for param in wall.Parameters:
                param_name = param.Definition.Name
                if self.debug_enabled:
                    print("DEBUG TOP ELEV: Checking param: '{}'".format(param_name))
                if "top constraint" in param_name.lower() or "top level" in param_name.lower():
                    if self.debug_enabled:
                        print("DEBUG TOP ELEV: Found potential top param: '{}'".format(param_name))
                    if param.HasValue:
                        top_constraint_param = param
                        if self.debug_enabled:
                            print("DEBUG TOP ELEV: Using param '{}' with StorageType: {}".format(
                                param_name, param.StorageType))
                        break

            if top_constraint_param:
                if self.debug_enabled:
                    print("DEBUG TOP ELEV: Processing param with StorageType: {}".format(
                        top_constraint_param.StorageType))

                # Handle based on StorageType
                if top_constraint_param.StorageType == StorageType.ElementId:
                    if self.debug_enabled:
                        print("DEBUG TOP ELEV: Handling ElementId StorageType")
                    # Top Constraint is stored as ElementId reference to level
                    element_id = top_constraint_param.AsElementId()
                    if self.debug_enabled:
                        print("DEBUG TOP ELEV: ElementId: {}".format(element_id))

                    if element_id and element_id != ElementId.InvalidElementId:
                        # Connected to level
                        level = self.doc.GetElement(element_id)
                        if self.debug_enabled:
                            print("DEBUG TOP ELEV: Got element: {}".format(level))
                        if level and isinstance(level, Level):
                            top_elevation = level.Elevation
                            if self.debug_enabled:
                                print("DEBUG TOP ELEV: Level elevation: {:.2f}".format(top_elevation))

                            # Add Top Offset if exists
                            top_offset_param = wall.LookupParameter("Top Offset")
                            if top_offset_param and top_offset_param.HasValue:
                                top_offset = top_offset_param.AsDouble()
                                if self.debug_enabled:
                                    print("DEBUG TOP ELEV: Adding top offset: {:.2f}".format(top_offset))
                                top_elevation += top_offset

                            if self.debug_enabled:
                                print("DEBUG TOP ELEV: Final top elevation: {:.2f}".format(top_elevation))
                            return top_elevation
                    else:
                        # Unconnected wall - use Unconnected Height
                        if self.debug_enabled:
                            print("DEBUG TOP ELEV: Wall is unconnected (ElementId = {}), using Unconnected Height".format(element_id))
                        unconnected_height_param = wall.LookupParameter("Unconnected Height")
                        if unconnected_height_param and unconnected_height_param.HasValue:
                            unconnected_height = unconnected_height_param.AsDouble()
                            if self.debug_enabled:
                                print("DEBUG TOP ELEV: Unconnected height: {:.2f}".format(unconnected_height))
                            result = base_elevation + unconnected_height
                            if self.debug_enabled:
                                print("DEBUG TOP ELEV: Final elevation: {:.2f}".format(result))
                            return result

                elif top_constraint_param.StorageType == StorageType.String:
                    print("DEBUG TOP ELEV: Handling String StorageType")
                    # Handle string format (fallback)
                    top_constraint_value = top_constraint_param.AsString()
                    print("DEBUG TOP ELEV: String value: '{}'".format(top_constraint_value))

                    # Parse string format
                    if "Up to level:" in top_constraint_value:
                        level_name = top_constraint_value.replace("Up to level:", "").strip()
                        print("DEBUG TOP ELEV: Parsed level name: '{}'".format(level_name))
                        collector = FilteredElementCollector(self.doc).OfClass(Level)
                        for level in collector:
                            if level.Name == level_name:
                                print("DEBUG TOP ELEV: Found level '{}' with elevation: {:.2f}".format(
                                    level.Name, level.Elevation))
                                return level.Elevation

                    elif "Unconnected" in top_constraint_value:
                        print("DEBUG TOP ELEV: Wall is unconnected")
                        unconnected_height_param = wall.LookupParameter("Unconnected Height")
                        if unconnected_height_param and unconnected_height_param.HasValue:
                            unconnected_height = unconnected_height_param.AsDouble()
                            print("DEBUG TOP ELEV: Unconnected height: {:.2f}".format(unconnected_height))
                            result = base_elevation + unconnected_height
                            print("DEBUG TOP ELEV: Final elevation: {:.2f}".format(result))
                            return result

                else:
                    print("DEBUG TOP ELEV: Unknown StorageType: {}".format(top_constraint_param.StorageType))

            else:
                print("DEBUG TOP ELEV: No Top Constraint parameter found")

            print("DEBUG TOP ELEV: Returning None")
            return None

        except Exception as e:
            print("DEBUG TOP ELEV: Exception: {}".format(str(e)))
            return None