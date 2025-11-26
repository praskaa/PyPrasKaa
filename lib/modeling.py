# -*- coding: utf-8 -*- 

def rs2wallWithDoors():
    # creates walls and roors from room separations
    # there is a transaction inside
    #returns the list of newly created walls e.g. for deletion
    from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Family
    from Autodesk.Revit.DB import Transaction, WallType, Wall, Line, Structure
    from Autodesk.Revit.DB import XYZ, BuiltInParameter, ElementId
    from pyrevit import revit

    # Get current document
    doc = revit.doc
    uidoc = revit.uidoc
    view = doc.ActiveView

    # Function to get the first available Wall Type
    def get_first_wall_type(doc):
        wall_types = list(FilteredElementCollector(doc).OfClass(WallType).WhereElementIsElementType())
        return wall_types[-1] if wall_types else None

    # Function to get a specific Curtain Wall Type or fallback to the first one
    # def get_first_wall_type(doc):
    #     curtain_wall_types = list(FilteredElementCollector(doc).OfClass(WallType).WhereElementIsElementType())
    #     selection = curtain_wall_types[0]
    #     for wall_type in curtain_wall_types:
    #         if wall_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == "Curtain Wall Standard":
    #               selection = wall_type        
    #     # Return the first curtain wall type if the specific one is not found
    #     return selection

    # # Function to get the first available Door Type
    # def get_first_door_type(doc):
    #     count = 0
    #     for family in FilteredElementCollector(doc).OfClass(Family):
    #         if family.Name == "Dvere 1K oblozka_content":
    #             for symbol_id in family.GetFamilySymbolIds():
    #                 symbol = doc.GetElement(symbol_id)
    #                 if symbol.Name == "700x1970":
    #                     count += 1
    #                     return symbol
    #     if count == 0:
    #         door_families = FilteredElementCollector(doc).OfClass(Family).WhereElementIsNotElementType()
    #         for family in door_families:
    #             if family.FamilyCategory.Name == "Doors":
    #                 for symbol_id in family.GetFamilySymbolIds():
    #                     return doc.GetElement(symbol_id)  # Return first door type found
    #         return None


    # Function to get a specific Door Type or fallback to the last one
    def get_specific_or_last_door_type(doc):
        door_families = FilteredElementCollector(doc).OfClass(Family).WhereElementIsNotElementType()
        all_door_types = []

        for family in door_families:
            # if family.FamilyCategory.Name == "Doors":
            if family.FamilyCategory.Id == ElementId(BuiltInCategory.OST_Doors):
                for symbol_id in family.GetFamilySymbolIds():
                    door_type = doc.GetElement(symbol_id)
                    all_door_types.append(door_type)
                    # Check for the specific door type by name
                    # Create narrow special door just for connections
                    if door_type:
                        door_name = door_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                        if door_name == "unitConnection":
                            return door_type  # Return if found

        # Return the last door type if the specific one is not found
        return all_door_types[-1] if all_door_types else None

    # Function to get the level of a Room Separator Line
    def get_line_level(line):
        level_id = line.LevelId
        if level_id != ElementId.InvalidElementId:
            return doc.GetElement(level_id)
        return None

    # Function to get wall direction as a unit vector
    # def get_wall_direction(wall):
    #     location_curve = wall.Location.Curve
    #     direction = location_curve.GetEndPoint(1) - location_curve.GetEndPoint(0)
    #     return direction.Normalize()

    # # Function to offset a point along a direction
    # def offset_point(point, direction, distance):
    #     return XYZ(point.X + direction.X * distance, point.Y + direction.Y * distance, point.Z)

    # Start transaction
    t = Transaction(doc, "Convert Room Separators to Walls with Doors")
    t.Start()

    # Get all Room Separator Lines in the active view
    room_separator_lines = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_RoomSeparationLines)\
        .WhereElementIsNotElementType() \
        .ToElements()

    # Get the first available Wall Type and Door Type
    wall_type = get_first_wall_type(doc)
    door_symbol = get_specific_or_last_door_type(doc)

    walls = []

    # Iterate over room separator lines and replace them with walls
    for line in room_separator_lines:
        curve = line.GeometryCurve
        start = curve.GetEndPoint(0)
        end = curve.GetEndPoint(1)

        # Get the level of the room separator line
        level = get_line_level(line)

        # Create a wall
        if level:
            new_wall = Wall.Create(doc, Line.CreateBound(start, end), wall_type.Id, level.Id, 10, 0, False, False)
            # store walls in a list for later deletion
            walls.append(new_wall)

            location_curve = new_wall.Location.Curve
            mid_point = location_curve.Evaluate(0.5, True)  # Get midpoint

            # Ensure door type is activated
            if not door_symbol.IsActive:
                door_symbol.Activate()
                doc.Regenerate()

            # Place the door
            doc.Create.NewFamilyInstance(mid_point, door_symbol, new_wall, level, Structure.StructuralType.NonStructural)

    # Place doors at the midpoint of each wall
    # for wall in walls:
    #     location_curve = wall.Location.Curve
    #     mid_point = location_curve.Evaluate(0.5, True)  # Get midpoint

    #     # Ensure door type is activated
    #     if not door_symbol.IsActive:
    #         door_symbol.Activate()
    #         doc.Regenerate()

    #     # Place the door
    #     doc.Create.NewFamilyInstance(mid_point, door_symbol, wall, Structure.StructuralType.NonStructural)

    t.Commit()
    #returns the list of newly created walls e.g. for deletion
    return walls