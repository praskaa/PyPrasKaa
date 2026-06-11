# PrasKaaPyKit Library Documentation

## Overview

This document provides comprehensive documentation for all functions available in the `lib/` folder of PrasKaaPyKit extension. The library contains reusable utilities organized into logical modules for Revit API operations.

**Note:** Many modules are adapted from open-source pyRevit extensions and modified for PrasKaaPyKit needs.

## Table of Contents

1. [Core Library Modules](#core-library-modules)
   - [area_reinforcement.py](#area_reinforcementpy)
   - [geometry_matching.py](#geometry_matchingpy)
   - [graphicOverrides.py](#graphicoverridespy)
   - [element_properties.py](#element_propertiespy)
   - [view_generator.py](#view_generatorpy)
   - [smart_tag_engine.py](#smart_tag_enginepy)
   - [wall_orientation_logic.py](#wall_orientation_logicpy)
   - [join_utils.py](#join_utilspy)
   - [customOutput.py](#customoutputpy)
   - [stringFormating.py](#stringformatingpy)
   - [csv_utils.py](#csv_utilspy)
   - [configparser_ironpython.py](#configparser_ironpythonpy)
   - [database.py](#databasepy)
   - [colorize.py](#colorizepy)
   - [expUtils.py](#exputilspy)
   - [linked_elements.py](#linked_elementspy)
   - [linked_model_utils.py](#linked_model_utilspy)
   - [rebar_selection.py](#rebar_selectionpy)
   - [structural_utils.py](#structural_utilspy)
   - [modeling.py](#modelingpy)
   - [hook_translate.py](#hook_translatepy)
   - [hooksScripts.py](#hookscriptspy)
   - [join_columns.py](#join_columnspy)
   - [matching_config.py](#matching_configpy)
   - [section_generator.py](#section_generatorpy)
   - [smart_tag_config.py](#smart_tag_configpy)
   - [strUtils.py](#strutilspy)
   - [uid_registry.py](#uid_registrypy)
   - [units.py](#unitspy)

2. [Parameters Framework](#parameters-framework)
   - [framework.py](#frameworkpy)
   - [strategies.py](#strategiespy)
   - [validators.py](#validatorspy)
   - [gis_categories.py](#gis_categoriespy)
   - [exceptions.py](#exceptionspy)
   - [tests.py](#testspy)

3. [Elements Module](#elements-module)
   - [element_names.py](#element_namespy)

4. [Snippets Library](#snippets-library)
   - [smart_selection.py](#smart_selectionpy)
   - [_selection.py](#_selectionpy)
   - [_convert.py](#_convertpy)
   - [_context_manager.py](#_context_managerpy)
   - [_elements.py](#_elementspy)
   - [_filters.py](#_filterspy)
   - [_views.py](#_viewspy)
   - [_annotations.py](#_annotationspy)
   - [_boundingbox.py](#_boundingboxpy)
   - [_excel.py](#_excelpy)
   - [_filter_examples.py](#_filter_examplespy)
   - [_filtered_element_collector.py](#_filtered_element_collectorpy)
   - [_groups.py](#_groupspy)
   - [_lines.py](#_linespy)
   - [_overrides.py](#_overridespy)
   - [_revisions.py](#_revisionspy)
   - [_sheets.py](#_sheetspy)
   - [_variables.py](#_variablespy)
   - [_vectors.py](#_vectorspy)
   - [_worksharing.py](#_worksharingpy)

5. [UI Framework](#ui-framework)
   - [base_window.py](#base_windowpy)
   - [repository_ui.py](#repository_uipy)
   - [dialog_ui.py](#dialog_uipy)
   - [ui_items.py](#ui_itemspy)
   - [ui_styles.py](#ui_stylespy)
   - [ui_utils.py](#ui_utilspy)

6. [GUI Module](#gui-module)
   - [WPF_Base.py](#wpf_basepy)
   - [forms.py](#formspy)
   - [FindReplace.py](#findreplacepy)
   - [SelectFromDict.py](#selectfromdictpy)
   - [Tools/CreateFromRooms.py](#toolscreatefromroomspy)

7. [pykostik Module](#pykostik-module)
   - [Overview](#pykostik-overview)
   - [revit/db/](#revitdb)
   - [utils/](#utils)
   - [wrappers/](#wrappers)

8. [FamilyProfileUpdater Module](#familyprofileupdater-module)

9. [Samples Module](#samples-module)

10. [Utilities Module](#utilities-module)

11. [Visualization Module](#visualization-module)

---

## Core Library Modules

### area_reinforcement.py

Area Reinforcement creation and management utilities.

#### Functions

**`safe_logger_call(logger, method_name, message, *args, **kwargs)`**
- **Purpose**: Safe logging with error handling
- **Args**:
  - `logger`: Logger instance
  - `method_name`: Logger method name ('info', 'error', etc.)
  - `message`: Log message
  - `*args, **kwargs`: Additional arguments
- **Returns**: None

**`find_rebar_bar_type_by_name(doc, name)`**
- **Purpose**: Find RebarBarType by name
- **Args**:
  - `doc`: Revit Document
  - `name`: Bar type name (e.g., "D10", "D13")
- **Returns**: RebarBarType element or None

**`get_bar_diameter_from_rebar_bar_type(bar_type)`**
- **Purpose**: Extract diameter from RebarBarType name
- **Args**:
  - `bar_type`: RebarBarType element
- **Returns**: Diameter value or None

**`get_max_bar_diameter_from_area_reinforcement(area_reinf)`**
- **Purpose**: Get maximum bar diameter from Area Reinforcement
- **Args**:
  - `area_reinf`: Area Reinforcement element
- **Returns**: Maximum diameter value

**`get_bar_types_from_area_reinforcement(area_reinf)`**
- **Purpose**: Get all bar types used in Area Reinforcement
- **Args**:
  - `area_reinf`: Area Reinforcement element
- **Returns**: List of bar type names

**`get_parameter_value_safe(element, param_name)`**
- **Purpose**: Safe parameter value getter with error handling
- **Args**:
  - `element`: Revit element
  - `param_name`: Parameter name
- **Returns**: Parameter value or None

**`set_parameter_value_safe(element, param_name, value)`**
- **Purpose**: Safe parameter value setter with error handling
- **Args**:
  - `element`: Revit element
  - `param_name`: Parameter name
  - `value`: Value to set
- **Returns**: Success boolean

**`get_filled_region_boundary(filled_region, view)`**
- **Purpose**: Extract boundary curves from Filled Region
- **Args**:
  - `filled_region`: Filled Region element
  - `view`: View containing the region
- **Returns**: List of boundary curves

**`convert_view_to_model_coordinates(curves, view)`**
- **Purpose**: Convert view coordinates to model coordinates
- **Args**:
  - `curves`: List of curves in view coordinates
  - `view`: Source view
- **Returns**: List of curves in model coordinates

**`create_area_reinforcement_safe(doc, boundary_curves, host_element, major_direction=None)`**
- **Purpose**: Create Area Reinforcement with safety checks
- **Args**:
  - `doc`: Revit Document
  - `boundary_curves`: Boundary curves for reinforcement
  - `host_element`: Host element (floor/slab)
  - `major_direction`: Major reinforcement direction
- **Returns**: Created Area Reinforcement element

**`override_area_reinforcement_parameters(area_reinforcement, parameter_overrides=None, logger=None)`**
- **Purpose**: Override multiple parameters on Area Reinforcement
- **Args**:
  - `area_reinforcement`: Area Reinforcement element
  - `parameter_overrides`: Dict of parameter overrides
  - `logger`: Optional logger
- **Returns**: Success boolean

**`process_multi_layer_area_reinforcement(doc, processor_input, logger=None)`**
- **Purpose**: Process multi-layer Area Reinforcement creation
- **Args**:
  - `doc`: Revit Document
  - `processor_input`: Processing configuration
  - `logger`: Optional logger
- **Returns**: Processing results

---

### geometry_matching.py

Geometry extraction, matching, and analysis utilities for beam/column matching between host and linked models.

#### Functions

**`create_geometry_options(doc)`**
- **Purpose**: Create optimized geometry options for extraction
- **Args**:
  - `doc`: Revit Document
- **Returns**: Options object

**`collect_beams(doc, preselect_ids=None)`**
- **Purpose**: Collect structural framing beams
- **Args**:
  - `doc`: Revit Document
  - `preselect_ids`: Optional pre-selected element IDs
- **Returns**: List of beam elements

**`get_solid(element, options)`**
- **Purpose**: Extract largest solid geometry from element
- **Args**:
  - `element`: Revit element
  - `options`: Geometry options
- **Returns**: Solid geometry or None

**`find_best_match(host_solid, linked_list, vol_threshold)`**
- **Purpose**: Find best geometric match by volume intersection
- **Args**:
  - `host_solid`: Host element solid
  - `linked_list`: List of linked element data
  - `vol_threshold`: Minimum volume threshold
- **Returns**: Tuple of (best_match_element, intersection_volume)

**`get_beam_dimensions(beam)`**
- **Purpose**: Extract dimension parameters from beam
- **Args**:
  - `beam`: Beam element
- **Returns**: Dict with 'b', 'h', 'type' or None

**`compare_dimensions(host_dims, linked_dims, tolerance_mm=0.01)`**
- **Purpose**: Compare beam dimensions with tolerance
- **Args**:
  - `host_dims`: Host beam dimensions
  - `linked_dims`: Linked beam dimensions
  - `tolerance_mm`: Tolerance in mm
- **Returns**: Boolean match result

**`match_beams(link_doc, host_beams=None, uidoc=None, doc=None, vol_threshold=1e-9, validate_dimensions=False, dim_tolerance_mm=0.01)`**
- **Purpose**: Main beam matching function
- **Args**:
  - `link_doc`: Linked document
  - `host_beams`: Host beams (optional)
  - `uidoc`: UIDocument (optional)
  - `doc`: Document (optional)
  - `vol_threshold`: Volume threshold
  - `validate_dimensions`: Whether to validate dimensions
  - `dim_tolerance_mm`: Dimension tolerance
- **Returns**: Dict with matches, unmatched, stats

**`extract_type_mark_from_type_name(type_name)`**
- **Purpose**: Extract Type Mark prefix from Type Name
- **Args**:
  - `type_name`: Type name string
- **Returns**: Extracted type mark or None

---

### graphicOverrides.py

Graphic override utilities for line colors and patterns.

#### Functions

**`get_revit_version()`**
- **Purpose**: Get current Revit version
- **Returns**: Version string

**`get_solid_fill_pattern(doc)`**
- **Purpose**: Get solid fill pattern for sections
- **Args**:
  - `doc`: Revit Document
- **Returns**: FillPatternElement

**`get_concrete_fill_pattern(doc)`**
- **Purpose**: Get concrete fill pattern
- **Args**:
  - `doc`: Revit Document
- **Returns**: FillPatternElement

**`get_diagonal_crosshatch_pattern(doc)`**
- **Purpose**: Get diagonal crosshatch pattern
- **Args**:
  - `doc`: Revit Document
- **Returns**: FillPatternElement

**`setProjLines(r, g, b, strong=False)`**
- **Purpose**: Set projection line color override
- **Args**:
  - `r, g, b`: RGB color values (0-255)
  - `strong`: Whether to use strong override
- **Returns**: Success boolean

**`setProjLinesDiagonalCrossHatch(r1, g1, b1, r2, g2, b2, strong=True)`**
- **Purpose**: Set diagonal crosshatch pattern with colors
- **Args**:
  - `r1, g1, b1`: First color RGB
  - `r2, g2, b2`: Second color RGB
  - `strong`: Strong override flag
- **Returns**: Success boolean

**`setProjLinesConcrete(r1, g1, b1, r2, g2, b2, strong=True)`**
- **Purpose**: Set concrete pattern with colors
- **Args**:
  - `r1, g1, b1`: First color RGB
  - `r2, g2, b2`: Second color RGB
  - `strong`: Strong override flag
- **Returns**: Success boolean

---

### element_properties.py

Element property analysis and calculation.

#### Classes

**`ElementProperties(element, doc=None)`**
- **Purpose**: Comprehensive element property analysis
- **Methods**:
  - `_calculate_properties()`: Calculate properties based on element type
  - `_get_wall_properties()`: Wall-specific properties
  - `_get_generic_properties()`: Generic element properties
  - `_get_point_based_properties()`: Point-based family properties
  - `_get_curve_based_properties()`: Curve-based family properties
  - `_get_hosted_properties()`: Hosted family properties
  - `_get_fallback_properties()`: Fallback property calculation
  - `get_bounding_box_2d()`: 2D bounding box at elevation
  - `get_mid_height_elevation()`: Mid-height elevation
  - `_get_base_elevation()`: Base elevation calculation

---

### view_generator.py

Automated view generation utilities.

#### Classes

**`ViewGenerator(doc)`**
- **Purpose**: Reusable view generation utilities
- **Methods**:
  - `create_plan_view_for_elements(elements, level, view_name_base, crop_region=True)`: Create plan view
  - `create_elevation_view_for_elements(elements, level, view_name_base, crop_region=True)`: Create elevation view
  - `create_cross_section_view_for_elements(elements, level, view_name_base, crop_region=True)`: Create section view
  - `create_only_plan_view_for_elements(elements, level, view_name_base, crop_region=True)`: Create plan-only view
  - `ensure_unique_view_name(base_name)`: Ensure unique view name
  - `get_floor_plan_view_type()`: Get structural plan view type
  - `calculate_walls_bounding_box(elements, level)`: Calculate wall bounding box
  - `_filter_walls_by_level(walls, target_level)`: Filter walls by level

---

### smart_tag_engine.py

Intelligent tag placement system.

#### Classes

**`SmartTagEngine(doc)`**
- **Purpose**: Core engine for intelligent tag placement
- **Methods**:
  - `get_structural_plans()`: Get structural plan views
  - `set_debug(enabled)`: Enable/disable debug mode
  - `is_element_tagged_in_view(element, view)`: Check if element is tagged
  - `get_tag_type(tag_type_name, category)`: Get tag type by name
  - `calculate_framing_tag_position(beam, view, offset_mm)`: Calculate beam tag position
  - `calculate_column_tag_position(column, view, offset_mm)`: Calculate column tag position
  - `calculate_wall_tag_position(wall, view, offset_mm)`: Calculate wall tag position
  - `tag_elements_in_view(view, config, tag_mode)`: Tag elements in view
  - `get_element_base_level(element)`: Get element base level
  - `get_element_top_level(element)`: Get element top level
  - `should_tag_vertical_element(element, view_level)`: Check if vertical element should be tagged

---

### wall_orientation_logic.py

Wall orientation analysis and tag positioning.

#### Classes

**`WallOrientationHandler`**
- **Purpose**: Handle wall orientation detection and management
- **Methods**:
  - `get_wall_orientation(wall)`: Get wall orientation
  - `get_wall_facing_direction(wall)`: Get facing direction
  - `_get_cardinal_direction(angle)`: Convert angle to cardinal direction
  - `calculate_tag_position(wall, offset_mm=100)`: Calculate tag position
  - `_get_wall_midpoint(wall)`: Get wall midpoint
  - `is_wall_facing_positive_direction(wall, view_direction=None)`: Check facing direction

---

### join_utils.py

Element joining utilities.

#### Functions

**`get_intersecting_elements(element, doc, categories, tolerance=0.001)`**
- **Purpose**: Find elements that intersect with given element
- **Args**:
  - `element`: Source element
  - `doc`: Revit Document
  - `categories`: List of categories to check
  - `tolerance`: Intersection tolerance
- **Returns**: List of intersecting elements

**`perform_join_if_needed(doc, element1, element2)`**
- **Purpose**: Join elements if they intersect
- **Args**:
  - `doc`: Revit Document
  - `element1, element2`: Elements to join
- **Returns**: Success boolean

**`ensure_join_order(doc, cutting_element, cut_element)`**
- **Purpose**: Ensure correct join order
- **Args**:
  - `doc`: Revit Document
  - `cutting_element`: Element that cuts
  - `cut_element`: Element that gets cut
- **Returns**: Success boolean

**`process_elements_with_join_logic(doc, elements, join_func)`**
- **Purpose**: Process elements with join logic
- **Args**:
  - `doc`: Revit Document
  - `elements`: List of elements
  - `join_func`: Join function to apply
- **Returns**: Processing results

---

### customOutput.py

Output formatting and logging utilities.

#### Functions

**`get_safe_log_path(new_path, fallback_path)`**
- **Purpose**: Get safe log file path
- **Args**:
  - `new_path`: Preferred path
  - `fallback_path`: Fallback path
- **Returns**: Safe path string

**`company_conf()`**
- **Purpose**: Load company configuration
- **Returns**: Configuration dict

**`hmsTimer(timerSeconds)`**
- **Purpose**: Format seconds to H:MM:SS
- **Args**:
  - `timerSeconds`: Time in seconds
- **Returns**: Formatted time string

**`file_name_getter(doc)`**
- **Purpose**: Get file name from document
- **Args**:
  - `doc`: Revit Document
- **Returns**: File name string

**`mass_message_url(output)`**
- **Purpose**: Generate mass message URL
- **Args**:
  - `output`: Output instance
- **Returns**: URL string

**`text_highligter(a)`**
- **Purpose**: Highlight text in output
- **Args**:
  - `a`: Text to highlight
- **Returns**: Highlighted text

**`mailto(a)`**
- **Purpose**: Create mailto link
- **Args**:
  - `a`: Email address
- **Returns**: Mailto link

**`linkMaker(a, title)`**
- **Purpose**: Create hyperlink
- **Args**:
  - `a`: URL
  - `title`: Link title
- **Returns**: HTML link

**`heading(text, size)`**
- **Purpose**: Create heading
- **Args**:
  - `text`: Heading text
  - `size`: Heading size
- **Returns**: Formatted heading

---

### stringFormating.py

String processing utilities.

#### Functions

**`accents2ascii(text)`**
- **Purpose**: Convert accented characters to ASCII
- **Args**:
  - `text`: Text with accents
- **Returns**: ASCII text

**`listFromString(string)`**
- **Purpose**: Parse string to list
- **Args**:
  - `string`: Input string
- **Returns**: List of items

**`zeroAdder(i, positions)`**
- **Purpose**: Add leading zeros to number
- **Args**:
  - `i`: Number to format
  - `positions`: Total positions
- **Returns**: Zero-padded string

---

### csv_utils.py

CSV import/export utilities.

#### Classes

**`csvUtils(lstData, filepath)`**
- **Purpose**: CSV data handling
- **Methods**:
  - `csvUtils_import(wsName=None, col=0, row=0)`: Import CSV data

---

### configparser_ironpython.py

ConfigParser implementation for IronPython.

#### Classes

**`ConfigParser`**
- **Purpose**: Configuration file parsing
- **Methods**:
  - `read(filename)`: Read config file
  - `get(section, option)`: Get config value

---

### database.py

Database and filter utilities for Revit elements. Contains helper functions for element collection, filtering, and parameter operations.

#### Functions

**`get_alphabetic_labels(nr)`**
- **Purpose**: Get N letters A, B, C, etc or AA, AB, AC if N more than 26
- **Args**:
  - `nr`: Number of labels needed
- **Returns**: List of alphabetic labels

**`any_fill_type(doc=revit.doc)`**
- **Purpose**: Get any Filled Region Type
- **Returns**: FilledRegionType element

**`invis_style(doc=revit.doc)`**
- **Purpose**: Get invisible lines graphics style
- **Returns**: GraphicsStyle element

**`get_sheet(some_number, doc=revit.doc)`**
- **Purpose**: Get sheet by sheet number
- **Args**:
  - `some_number`: Sheet number string
- **Returns**: Sheet element

**`get_view(some_name, doc=revit.doc)`**
- **Purpose**: Get view by name
- **Args**:
  - `some_name`: View name string
- **Returns**: View element

**`get_fam_types(family_name, doc=revit.doc)`**
- **Purpose**: Get all family types by family name
- **Args**:
  - `family_name`: Family name string
- **Returns**: FilteredElementCollector

**`get_solid_fill_pat(doc=revit.doc)`**
- **Purpose**: Get solid fill pattern element
- **Returns**: FillPatternElement

**`param_set_by_cat(cat, doc=revit.doc)`**
- **Purpose**: Get all project type parameters of a given category
- **Args**:
  - `cat`: BuiltInCategory
- **Returns**: List of parameters

**`create_sheet(sheet_num, sheet_name, titleblock, doc=revit.doc)`**
- **Purpose**: Create new sheet with given parameters
- **Args**:
  - `sheet_num`: Sheet number
  - `sheet_name`: Sheet name
  - `titleblock`: Titleblock ElementId
- **Returns**: New ViewSheet

**`get_name(el)`**
- **Purpose**: Get element name using Element.Name property
- **Args**:
  - `el`: Revit element
- **Returns**: Element name string

**`get_viewport_types(doc=revit.doc)`**
- **Purpose**: Get all viewport types
- **Returns**: Collector of viewport types

**`check_filter_exists(filter_name, doc=revit.doc)`**
- **Purpose**: Check if view filter exists by name
- **Args**:
  - `filter_name`: Filter name to check
- **Returns**: FilterElement or None

**`create_filter(filter_name, bics_list, doc=revit.doc)`**
- **Purpose**: Create parameter filter element
- **Args**:
  - `filter_name`: Name for new filter
  - `bics_list`: List of BuiltInCategory
- **Returns**: ParameterFilterElement

**`get_param_value_as_string(p)`**
- **Purpose**: Get parameter value as string regardless of storage type
- **Args**:
  - `p`: Parameter object
- **Returns**: String value or None

**`get_param_value_by_storage_type(p)`**
- **Purpose**: Get parameter value by its storage type
- **Args**:
  - `p`: Parameter object
- **Returns**: Typed value or None

**`p_storage_type(param)`**
- **Purpose**: Get parameter storage type as string
- **Args**:
  - `param`: Parameter object
- **Returns**: Storage type string

**`get_builtin_label(bip_or_bic)`**
- **Purpose**: Get language-specific label for BuiltInParameter or BuiltInCategory
- **Args**:
  - `bip_or_bic`: BuiltInParameter or BuiltInCategory
- **Returns**: Localized label string

**`get_document_model_bics(doc=revit.doc)`**
- **Purpose**: Get all model BuiltInCategories in document
- **Returns**: List of BuiltInCategory

**`model_categories_dict(doc)`**
- **Purpose**: Get dictionary of model categories {Category name: BIC}
- **Returns**: Dictionary mapping

---

### colorize.py

Color generation and override management for visualization.

#### Functions

**`basic_colours()`**
- **Purpose**: Return basic color palette (14 colors)
- **Returns**: List of hex color strings

**`rainbow()`**
- **Purpose**: Return rainbow color palette
- **Returns**: List of hex color strings

**`hex_to_rgb(hex)`**
- **Purpose**: Convert hex color to RGB tuple
- **Args**:
  - `hex`: Hex color string
- **Returns**: RGB list

**`rgb_to_hex(rgb)`**
- **Purpose**: Convert RGB tuple to hex string
- **Args**:
  - `rgb`: RGB tuple
- **Returns**: Hex color string

**`linear_gradient(start_hex, finish_hex, n=10)`**
- **Purpose**: Generate gradient between two colors
- **Args**:
  - `start_hex`: Start color
  - `finish_hex`: End color
  - `n`: Number of colors
- **Returns**: Color dictionary

**`revit_colour(hex)`**
- **Purpose**: Convert hex to Revit Color object
- **Args**:
  - `hex`: Hex color string
- **Returns**: DB.Color object

**`get_colours(n)`**
- **Purpose**: Generate n Revit Color objects
- **Args**:
  - `n`: Number of colors needed
- **Returns**: List of DB.Color objects

**`get_categories_config(doc)`**
- **Purpose**: Get category configuration for colorizers
- **Args**:
  - `doc`: Revit Document
- **Returns**: Dictionary {Label: BIC}

**`set_colour_overrides_by_option(overrides_option, colour, doc)`**
- **Purpose**: Apply color overrides based on options
- **Args**:
  - `overrides_option`: List of override options
  - `colour`: DB.Color object
  - `doc`: Revit Document
- **Returns**: OverrideGraphicSettings object

---

### expUtils.py

Export utilities for PDF and DWG export operations.

#### Functions

**`expUtils_getNamingFormat(default_template="{number} {name}")`**
- **Purpose**: Get selected naming format from shared config
- **Args**:
  - `default_template`: Default naming template
- **Returns**: Template string

**`expUtils_getDir()`**
- **Purpose**: Get default export directory
- **Returns**: Directory path string

**`expUtils_getFolder(task="_PDF")`**
- **Purpose**: Create timestamped subfolder name
- **Args**:
  - `task`: Task suffix
- **Returns**: Folder name string

**`expUtils_ensureDir(dp)`**
- **Purpose**: Create directory if it doesn't exist
- **Args**:
  - `dp`: Directory path
- **Returns**: Directory path

**`expUtils_canPrint()`**
- **Purpose**: Check if Revit version supports PDF export (2022+)
- **Returns**: Boolean

**`expUtils_nameSheet(s, template=None, doc=None)`**
- **Purpose**: Generate sheet export filename
- **Args**:
  - `s`: ViewSheet element
  - `template`: Naming template
  - `doc`: Revit Document
- **Returns**: Filename string

**`expUtils_pdfOpts(hcb=False, hsb=True, hrp=True, hvt=True, mcl=True)`**
- **Purpose**: Create PDF export options
- **Args**: Various hide/show options
- **Returns**: PDFExportOptions object

**`expUtils_dwgOpts(sc=False, mv=True)`**
- **Purpose**: Create DWG export options
- **Args**:
  - `sc`: Shared coordinates
  - `mv`: Merged views
- **Returns**: DWGExportOptions object

**`expUtils_exportSheetPdf(d, s, opt, myDoc, myUidoc, template=None)`**
- **Purpose**: Export single sheet to PDF
- **Args**:
  - `d`: Directory path
  - `s`: ViewSheet
  - `opt`: PDFExportOptions
  - `myDoc`: Document
  - `myUidoc`: UIDocument
  - `template`: Naming template
- **Returns**: 1 on success

**`expUtils_exportSheetDwg(d, s, opt, myDoc, myUidoc, template=None)`**
- **Purpose**: Export single sheet to DWG
- **Returns**: 1 on success

**`expUtils_updateSheetIssueDate(sheet, doc)`**
- **Purpose**: Update Sheet Issue Date parameter
- **Args**:
  - `sheet`: ViewSheet element
  - `doc`: Document
- **Returns**: Success boolean

---

### linked_elements.py

Utilities for working with linked Revit elements, including tag checking and selection.

#### Classes

**`LinkedElementInfo`**
- **Purpose**: Container for linked element data
- **Attributes**:
  - `element`: The linked element
  - `link_instance`: RevitLinkInstance
  - `linked_doc`: Linked Document
- **Properties**:
  - `element_id`: Element ID in linked document
  - `link_instance_id`: Link instance ID in host
  - `name`: Element name with link prefix

#### Functions

**`get_all_revti_link_instances(doc)`**
- **Purpose**: Get all Revit link instances in document
- **Args**:
  - `doc`: Host document
- **Returns**: List of RevitLinkInstance

**`get_linked_document(link_instance)`**
- **Purpose**: Get Document from RevitLinkInstance
- **Args**:
  - `link_instance`: RevitLinkInstance
- **Returns**: Document or None

**`get_tagged_linked_elements_from_view(doc, view)`**
- **Purpose**: Get all tagged linked elements in view
- **Args**:
  - `doc`: Host document
  - `view`: View to check
- **Returns**: Dict of {(link_inst_id, elem_id): LinkedElementInfo}

**`get_untagged_linked_elements(doc, view, category)`**
- **Purpose**: Get untagged linked elements in view
- **Args**:
  - `doc`: Host document
  - `view`: View to check
  - `category`: BuiltInCategory to filter
- **Returns**: List of LinkedElementInfo

**`find_missing_tags(doc, view, category, include_host=True, include_linked=True)`**
- **Purpose**: Find all untagged elements from host and linked
- **Args**:
  - `doc`: Host document
  - `view`: View to check
  - `category`: BuiltInCategory
  - `include_host`: Include host elements
  - `include_linked`: Include linked elements
- **Returns**: Dict with 'host', 'linked', 'total' keys

---

### linked_model_utils.py

Utilities for working with linked Revit models.

#### Functions

**`select_linked_model(document, title='Select Source Linked Model', button_name='Select Link')`**
- **Purpose**: Prompt user to select a linked model
- **Args**:
  - `document`: Revit Document
  - `title`: Dialog title
  - `button_name`: Button label
- **Returns**: Tuple (link_doc, selected_link)

**`get_linked_beams(link_doc)`**
- **Purpose**: Collect structural framing from linked model
- **Args**:
  - `link_doc`: Linked document
- **Returns**: List of structural framing elements

**`get_linked_columns(link_doc)`**
- **Purpose**: Collect structural columns from linked model
- **Args**:
  - `link_doc`: Linked document
- **Returns**: List of structural column elements

**`validate_linked_model(link_doc)`**
- **Purpose**: Validate linked model has structural elements
- **Args**:
  - `link_doc`: Linked document
- **Returns**: Tuple (is_valid, message, stats)

**`get_all_link_instances(document)`**
- **Purpose**: Get all linked model instances
- **Returns**: List of RevitLinkInstance

**`get_link_by_name(document, link_name)`**
- **Purpose**: Get specific linked model by name
- **Args**:
  - `document`: Revit Document
  - `link_name`: Link name to find
- **Returns**: RevitLinkInstance or None

---

### rebar_selection.py

Rebar selection utilities for selecting RebarBarType and rebar elements.

#### Functions

**`select_rebar_bar_type(given_uidoc=uidoc, exitscript=True, title="Select Rebar Bar Type", label="Choose Rebar Bar Type")`**
- **Purpose**: Let user select a rebar bar type
- **Args**:
  - `given_uidoc`: UIDocument
  - `exitscript`: Exit if no selection
  - `title`: Dialog title
  - `label`: Dialog label
- **Returns**: Selected RebarBarType or None

**`select_rebar_bar_types_multiple(given_uidoc=uidoc, exitscript=True, ...)`**
- **Purpose**: Let user select multiple rebar bar types
- **Returns**: List of selected RebarBarType

**`select_rebar_bar_type_by_diameter_range(given_uidoc=uidoc, min_diameter=None, max_diameter=None, exitscript=True)`**
- **Purpose**: Select rebar type filtered by diameter range
- **Args**:
  - `min_diameter`: Minimum diameter in mm
  - `max_diameter`: Maximum diameter in mm
- **Returns**: Selected RebarBarType or None

**`pick_rebar_elements(given_uidoc=uidoc, exitscript=True)`**
- **Purpose**: Pick rebar elements from model
- **Returns**: List of selected Rebar elements

**`pick_rebar_bar_type(given_uidoc=uidoc)`**
- **Purpose**: Pick single RebarBarType in UI
- **Returns**: Selected RebarBarType

#### Classes

**`ISelectionFilter_RebarTypes`**
- **Purpose**: Selection filter for RebarBarType elements

**`ISelectionFilter_RebarElements`**
- **Purpose**: Selection filter for Rebar elements

---

### structural_utils.py

Structural element utilities for beams and columns.

#### Functions

**`collect_structural_framing(document, selection_ids=None, uidoc=None)`**
- **Purpose**: Collect structural framing elements (beams)
- **Args**:
  - `document`: Revit Document
  - `selection_ids`: Optional pre-selected IDs
  - `uidoc`: UIDocument
- **Returns**: List of structural framing elements

**`collect_structural_columns(document, selection_ids=None, uidoc=None)`**
- **Purpose**: Collect structural column elements
- **Returns**: List of structural column elements

**`get_type_info(element)`**
- **Purpose**: Get comprehensive type information
- **Args**:
  - `element`: Structural element
- **Returns**: Dict with 'type_name', 'family_name', 'family_symbol'

**`get_family_symbol(element)`**
- **Purpose**: Get FamilySymbol from element
- **Returns**: FamilySymbol or None

**`extract_mark_from_type_name(type_name)`**
- **Purpose**: Extract mark value from Type Name
- **Args**:
  - `type_name`: Type name string (e.g., "G9-99")
- **Returns**: Extracted mark or None

**`check_family_type_exists(host_doc, family_name, type_name)`**
- **Purpose**: Check if family type exists in document
- **Args**:
  - `host_doc`: Document to search
  - `family_name`: Family name
  - `type_name`: Type name
- **Returns**: FamilySymbol or None

---

### modeling.py

Modeling utilities for element creation.

#### Functions

**`rs2wallWithDoors()`**
- **Purpose**: Create walls and doors from room separation lines
- **Returns**: List of newly created walls
- **Note**: Contains internal transaction

---

### hook_translate.py

Hook translation module for multi-language support.

#### Functions

**`lang()`**
- **Purpose**: Get current language setting
- **Returns**: Language code (0=English, 1=Indonesian)

**`get_hook_text(hook_name, language=None)`**
- **Purpose**: Get translated text for hook
- **Args**:
  - `hook_name`: Name of the hook
  - `language`: Language code (optional)
- **Returns**: Dict with 'text' and 'buttons'

**`add_hook_translation(hook_name, language, text, buttons)`**
- **Purpose**: Add or update hook translation
- **Args**:
  - `hook_name`: Hook identifier
  - `language`: Language code
  - `text`: Translated text
  - `buttons`: List of button texts

---

### hooksScripts.py

Hook scripts for Revit events (load family, link CAD, etc.).

Contains event handlers for:
- Load Family warning
- Link CAD file warnings
- Project Parameters modification
- In-Place Family warning

---

### join_columns.py

Column joining utilities.

#### Functions

**`join_columns_to_beams(columns, beams, doc)`**
- **Purpose**: Join columns to intersecting beams
- **Args**:
  - `columns`: List of column elements
  - `beams`: List of beam elements
  - `doc`: Revit Document
- **Returns**: Join results

---

### matching_config.py

Configuration for geometry matching operations.

Contains configuration classes and settings for beam/column matching workflows.

---

### section_generator.py

Section view generation utilities.

#### Functions

**`create_section(doc, view_family_type_id, direction, position, far_clip, name)`**
- **Purpose**: Create section view
- **Args**:
  - `doc`: Revit Document
  - `view_family_type_id`: View family type
  - `direction`: Section direction
  - `position`: Section position
  - `far_clip`: Far clip distance
  - `name`: View name
- **Returns**: Section view

---

### smart_tag_config.py

Configuration for smart tag engine.

Contains tag configuration settings and default values.

---

### strUtils.py

String utilities for file naming.

#### Functions

**`strUtils_legalize(filename)`**
- **Purpose**: Remove illegal characters from filename
- **Args**:
  - `filename`: Input filename
- **Returns**: Legal filename string

---

### uid_registry.py

UID registry for element identification.

#### Functions

**`generate_uid(prefix, element_id)`**
- **Purpose**: Generate unique identifier
- **Args**:
  - `prefix`: Category prefix (e.g., "BEAM", "COL")
  - `element_id`: Element ID
- **Returns**: UID string

---

### units.py

Unit conversion utilities.

#### Functions

**`convert_length_to_internal(value, doc=revit.doc)`**
- **Purpose**: Convert length from display to internal units
- **Args**:
  - `value`: Length value
  - `doc`: Revit Document
- **Returns**: Internal units value

**`convert_length_to_display(value, doc=revit.doc)`**
- **Purpose**: Convert length from internal to display units
- **Returns**: Display units value

**`get_length_units(doc)`**
- **Purpose**: Get document length units
- **Returns**: UnitTypeId or DisplayUnitType

**`degree_conv(x)`**
- **Purpose**: Convert radians to degrees
- **Args**:
  - `x`: Radians value
- **Returns**: Degrees value

**`is_metric(doc)`**
- **Purpose**: Check if document uses metric units
- **Returns**: Boolean

**`correct_input_units(val, doc)`**
- **Purpose**: Parse and convert input value to internal units
- **Args**:
  - `val`: Input string or number
  - `doc`: Revit Document
- **Returns**: Internal units value

**`round_metric_or_imperial(value, doc)`**
- **Purpose**: Round value based on unit system
- **Returns**: Rounded value

**`convert_length_to_display_string(value, doc=revit.doc)`**
- **Purpose**: Convert to display string with unit symbol
- **Returns**: Formatted string

---

## Parameters Framework

### framework.py

Main parameter setting framework.

#### Classes

**`OptimizationLevel(Enum)`**
- **Values**: BASIC, BATCH, OPTIMIZED

**`ParameterSettingFramework(doc, logger=None, default_optimization=OptimizationLevel.OPTIMIZED)`**
- **Purpose**: Main framework for parameter operations
- **Methods**:
  - `set_parameter(element, param_name, value, optimization_level=None, validate=True, **kwargs)`: Set single parameter
  - `set_multiple_parameters(operations, optimization_level=None, validate=True, **kwargs)`: Set multiple parameters
  - `execute_batch_operations(transaction_name="Batch Parameter Operations")`: Execute batch operations
  - `get_performance_metrics()`: Get performance metrics
  - `clear_caches()`: Clear caches
  - `recommend_optimization_level(operation_count, has_repeated_elements=False)`: Recommend optimization level

---

### strategies.py

Parameter setting strategies.

#### Classes

**`ParameterSettingStrategy`**
- **Purpose**: Abstract base class for parameter strategies
- **Methods**:
  - `set_parameter(element, param_name, value, **kwargs)`: Abstract method

**`BasicParameterStrategy`**
- **Purpose**: Basic strategy with individual transactions

**`BatchParameterStrategy`**
- **Purpose**: Batch processing strategy

**`OptimizedParameterStrategy`**
- **Purpose**: Optimized strategy with caching

---

### validators.py

Parameter validation system.

#### Classes

**`ParameterValidator`**
- **Purpose**: Advanced parameter validation
- **Methods**:
  - `validate_parameter_value(param_name, value, storage_type, **kwargs)`: Validate parameter value
  - `validate_element_parameter(element, param_name, **kwargs)`: Validate element parameter
  - `_validate_double_value(param_name, value, **kwargs)`: Validate double values
  - `_validate_integer_value(param_name, value, **kwargs)`: Validate integer values
  - `_validate_string_value(param_name, value, **kwargs)`: Validate string values
  - `_classify_parameter_type(param_name)`: Classify parameter type

---

### gis_categories.py

Centralized GIS categories configuration.

#### Constants

**`PARAM_NAME = "GIS_Element_UID"`**
- GIS Element UID parameter name

**`GIS_CATEGORIES`**
- Dictionary mapping category names to (BuiltInCategory, UID Prefix)
- Categories: Floors, Walls, Structural Framing, Structural Columns, Structural Foundation, Stairs

#### Functions

**`get_categories_dict()`**
- **Purpose**: Returns GIS_CATEGORIES dictionary
- **Returns**: Dict {name: (BIC, prefix)}

**`get_category_by_name(category_name)`**
- **Purpose**: Get category tuple by name
- **Returns**: (BuiltInCategory, UID Prefix) or None

**`get_all_category_enums()`**
- **Purpose**: Get all BuiltInCategory enums
- **Returns**: List of BuiltInCategory

**`get_uid_prefix(category_name)`**
- **Purpose**: Get UID prefix for category
- **Returns**: Prefix string (e.g., "FLOOR", "BEAM")

---

### exceptions.py

Custom exceptions for parameter operations.

#### Classes

**`ParameterValidationError`**
- **Purpose**: Raised when parameter validation fails

**`ParameterNotFoundError`**
- **Purpose**: Raised when parameter is not found

**`ParameterReadOnlyError`**
- **Purpose**: Raised when parameter is read-only

---

### tests.py

Unit tests for parameters framework.

Contains test functions for validating parameter operations.

---

## Elements Module

### element_names.py

Element name extraction utilities.

#### Functions

**`get_type_name(element)`**
- **Purpose**: Get type name from element with fallback strategies
- **Args**:
  - `element`: Revit element
- **Returns**: Type name string or "Unknown Type"

**`get_family_name(element)`**
- **Purpose**: Get family name from element
- **Args**:
  - `element`: Revit element
- **Returns**: Family name string or "Unknown Family"

**`get_family_and_type_name(element)`**
- **Purpose**: Get both family and type name
- **Args**:
  - `element`: Revit element
- **Returns**: Tuple (family_name, type_name)

---

## Snippets Library

### smart_selection.py

Intelligent element selection utilities.

#### Functions

**`get_filtered_selection(doc, uidoc, category_filter_func, prompt_message="Select Elements", no_selection_message="No valid elements were selected. Please select valid elements.", filter_name="Element Filter")`**
- **Purpose**: Smart element selection with filtering
- **Args**:
  - `doc`: Revit Document
  - `uidoc`: UIDocument
  - `category_filter_func`: Filter function
  - `prompt_message`: Selection prompt
  - `no_selection_message`: Error message
  - `filter_name`: Filter name for logging
- **Returns**: List of valid elements

**`create_single_category_filter(category)`**
- **Purpose**: Create filter for single category
- **Args**:
  - `category`: BuiltInCategory
- **Returns**: Filter function

**`create_category_filter(categories)`**
- **Purpose**: Create filter for multiple categories
- **Args**:
  - `categories`: List of BuiltInCategory
- **Returns**: Filter function

**`create_wall_filter()`**
- **Purpose**: Create wall filter
- **Returns**: Filter function

**`create_structural_filter()`**
- **Purpose**: Create structural elements filter
- **Returns**: Filter function

---

### _selection.py

Element selection utilities.

#### Functions

**`get_selected_elements(uidoc=uidoc, exitscript=True)`**
- **Purpose**: Get currently selected elements
- **Args**:
  - `uidoc`: UIDocument
  - `exitscript`: Exit on no selection
- **Returns**: List of selected elements

**`get_selected_rooms(uidoc=uidoc, exitscript=True)`**
- **Purpose**: Get selected rooms
- **Returns**: List of room elements

**`get_selected_views(given_uidoc=uidoc, exit_if_none=False, title='__title__', version='Version: _')`**
- **Purpose**: Get selected views
- **Returns**: List of view elements

**`get_selected_sheets(given_uidoc=uidoc, exit_if_none=False, title='__title__', label='Select Sheets')`**
- **Purpose**: Get selected sheets
- **Returns**: List of sheet elements

**`get_selected_walls(uidoc, exitscript=True)`**
- **Purpose**: Get selected walls
- **Returns**: List of wall elements

**`pick_wall(given_uidoc=uidoc)`**
- **Purpose**: Pick single wall
- **Returns**: Wall element

**`pick_curve(given_uidoc=uidoc)`**
- **Purpose**: Pick single curve
- **Returns**: Curve element

**`pick_by_category(list_categories, exit_if_none=True)`**
- **Purpose**: Pick elements by category
- **Args**:
  - `list_categories`: List of categories
- **Returns**: List of elements

**`pick_by_class(list_types, exit_if_none=True)`**
- **Purpose**: Pick elements by class
- **Args**:
  - `list_types`: List of types
- **Returns**: List of elements

#### Classes

**`CustomISelectionFilter`**
- **Purpose**: Custom selection filter

---

### _convert.py

Unit conversion utilities.

#### Functions

**`convert_internal_units(value, get_internal=True, units='m')`**
- **Purpose**: Convert between Revit internal units and display units
- **Args**:
  - `value`: Value to convert
  - `get_internal`: Direction of conversion
  - `units`: Target units
- **Returns**: Converted value

**`convert_cm_to_feet(length)`**
- **Purpose**: Convert cm to feet
- **Args**:
  - `length`: Length in cm
- **Returns**: Length in feet

**`convert_m_to_feet(length)`**
- **Purpose**: Convert meters to feet
- **Args**:
  - `length`: Length in meters
- **Returns**: Length in feet

**`convert_internal_to_m(length)`**
- **Purpose**: Convert internal units to meters
- **Args**:
  - `length`: Length in internal units
- **Returns**: Length in meters

**`convert_internal_to_cm(length)`**
- **Purpose**: Convert internal units to cm
- **Args**:
  - `length`: Length in internal units
- **Returns**: Length in cm

**`convert_internal_to_m2(area)`**
- **Purpose**: Convert internal units to square meters
- **Args**:
  - `area`: Area in internal units
- **Returns**: Area in square meters

---

### _context_manager.py

Context managers for Revit operations.

#### Functions

**`try_except(debug=False)`**
- **Purpose**: Try/except context manager with debug option
- **Args**:
  - `debug`: Enable debug logging
- **Returns**: Context manager

**`ef_Transaction(doc, title, debug=True, exitscript=False)`**
- **Purpose**: Transaction context manager with error handling
- **Args**:
  - `doc`: Revit Document
  - `title`: Transaction title
  - `debug`: Debug mode
  - `exitscript`: Exit on failure
- **Returns**: Context manager

---

### _elements.py

Element utilities.

#### Functions

**`dict_name_element(given_elements, dotNet=False)`**
- **Purpose**: Create name-element dictionary
- **Args**:
  - `given_elements`: List of elements
  - `dotNet`: Use .NET Name property
- **Returns**: Dictionary of name->element

---

### _filters.py

Filtering utilities.

#### Functions

**`create_filter(key_parameter, element_value)`**
- **Purpose**: Create parameter-based filter
- **Args**:
  - `key_parameter`: Parameter for filtering
  - `element_value`: Value to match
- **Returns**: Filter function

**`get_family_types(family_name)`**
- **Purpose**: Get family types by family name
- **Args**:
  - `family_name`: Family name
- **Returns**: List of family types

---

### _views.py

View utilities.

#### Functions

**`get_sheet_from_view(view)`**
- **Purpose**: Get sheet containing view
- **Args**:
  - `view`: View element
- **Returns**: Sheet element

**`create_3D_view(uidoc, name='')`**
- **Purpose**: Create 3D view
- **Args**:
  - `uidoc`: UIDocument
  - `name`: View name
- **Returns**: 3D view

#### Classes

**`SectionGenerator`**
- **Purpose**: Generate section views
- **Methods**:
  - `create_transform(mode='elevation')`: Create view transform
  - `create_section_box(mode='elevation')`: Create section box
  - `rename_view(view, new_name)`: Rename view
  - `create_sections(view_name_base)`: Create section views

---

### _annotations.py

Annotation utilities for tags, text notes, and dimensions.

---

### _boundingbox.py

Bounding box utilities for element bounds calculation.

---

### _excel.py

Excel export/import utilities.

---

### _filter_examples.py

Example filter implementations for reference.

---

### _filtered_element_collector.py

FilteredElementCollector helper functions.

---

### _groups.py

Group-related utilities for creating and managing groups.

---

### _lines.py

Line and curve utilities.

---

### _overrides.py

Graphic override utilities.

---

### _revisions.py

Revision-related utilities.

---

### _sheets.py

Sheet utilities for view sheet operations.

---

### _variables.py

Common variable definitions and constants.

---

### _vectors.py

Vector calculation utilities.

---

### _worksharing.py

Worksharing utilities for multi-user Revit models.

#### Functions

**`is_workshared(doc)`**
- **Purpose**: Check if document is workshared
- **Returns**: Boolean

**`get_checkout_status(element, doc)`**
- **Purpose**: Get checkout status of element
- **Returns**: CheckoutStatus enum

**`is_element_editable(element, doc)`**
- **Purpose**: Check if element can be modified
- **Returns**: Boolean

**`is_element_owned_by_current_user(element, doc)`**
- **Purpose**: Check if owned by current user
- **Returns**: Boolean

**`is_element_owned_by_other_user(element, doc)`**
- **Purpose**: Check if owned by another user
- **Returns**: Boolean

**`get_ownership_summary(elements, doc)`**
- **Purpose**: Get ownership summary for elements
- **Returns**: Dict with counts for each status

**`filter_editable_elements(elements, doc)`**
- **Purpose**: Filter elements that can be edited
- **Returns**: List of editable elements

**`get_editable_and_non_editable(elements, doc)`**
- **Purpose**: Separate editable and non-editable elements
- **Returns**: Tuple (editable, non_editable)

**`batch_modify_with_worksharing_check(elements, doc, modify_func, skip_owned_by_others=True, report_progress=False)`**
- **Purpose**: Modify elements with worksharing check
- **Args**:
  - `elements`: List of elements
  - `doc`: Document
  - `modify_func`: Function to apply
  - `skip_owned_by_others`: Skip non-editable
  - `report_progress`: Print progress
- **Returns**: Dict with results

---

## UI Framework

### base_window.py

Base UI classes for WPF windows.

#### Classes

**`BaseRevitWindow(forms.WPFWindow)`**
- **Purpose**: Base class for Revit WPF windows
- **Methods**:
  - `_get_xaml_path(xaml_file)`: Get XAML file path
  - `_setup_window_properties()`: Setup window properties
  - `setup_common_ui()`: Setup common UI elements
  - `header_drag(sender, args)`: Handle header drag
  - `button_close(sender, args)`: Handle close button

**`BaseRepositoryUI(BaseRevitWindow)`**
- **Purpose**: Base class for repository UIs
- **Methods**:
  - `setup_repository_ui()`: Setup repository UI
  - `load_items()`: Load items
  - `filter_items(search_text="")`: Filter items
  - `update_list_view()`: Update list view
  - `select_all_items()`: Select all items
  - `select_none_items()`: Select none items

**`BaseDialogUI(BaseRevitWindow)`**
- **Purpose**: Base class for dialog UIs
- **Methods**:
  - `setup_dialog_ui()`: Setup dialog UI

---

### repository_ui.py

Repository UI implementations.

#### Classes

**`FamilyRepositoryUI(BaseRepositoryUI)`**
- **Purpose**: UI for family repository management
- **Methods**:
  - `load_items()`: Load families
  - `filter_items(search_text="")`: Filter families
  - `sync_selected_items()`: Sync selected families

**`ViewTemplateRepositoryUI(BaseRepositoryUI)`**
- **Purpose**: UI for view template repository
- **Methods**:
  - `load_items()`: Load view templates
  - `filter_items(search_text="")`: Filter templates
  - `sync_selected_items()`: Sync selected templates

---

### dialog_ui.py

Dialog UI implementations.

#### Classes

**`AlignViewportsUI(BaseDialogUI)`**
- **Purpose**: UI for viewport alignment
- **Methods**:
  - `get_selected_sheets()`: Get selected sheets
  - `generate_list_items()`: Generate sheet items
  - `validate_inputs()`: Validate inputs
  - `execute_alignment(state)`: Execute alignment

**`BaseSettingsDialog(BaseDialogUI)`**
- **Purpose**: Base class for settings dialogs
- **Methods**:
  - `load_settings()`: Load settings
  - `save_settings()`: Save settings
  - `apply_settings()`: Apply settings
  - `reset_to_defaults()`: Reset to defaults

---

### ui_items.py

UI item classes.

#### Classes

**`BaseListItem`**
- **Purpose**: Base class for list items
- **Properties**: Name, IsSelected

**`CheckableListItem(BaseListItem)`**
- **Purpose**: Checkable list item
- **Properties**: Status, StatusColor

**`RadioListItem(BaseListItem)`**
- **Purpose**: Radio button list item
- **Properties**: Element

**`FamilyItem(CheckableListItem)`**
- **Purpose**: Family list item
- **Properties**: Category, Types

**`ViewTemplateItem(CheckableListItem)`**
- **Purpose**: View template list item
- **Properties**: ModifiedBy, LastModified

**`SheetItem(RadioListItem)`**
- **Purpose**: Sheet list item

#### Functions

**`create_family_item(family, current_doc)`**
- **Purpose**: Create family item
- **Args**:
  - `family`: Family element
  - `current_doc`: Current document
- **Returns**: FamilyItem

**`create_view_template_item(template, current_doc)`**
- **Purpose**: Create view template item
- **Args**:
  - `template`: View template
  - `current_doc`: Current document
- **Returns**: ViewTemplateItem

**`create_sheet_item(sheet)`**
- **Purpose**: Create sheet item
- **Args**:
  - `sheet`: Sheet element
- **Returns**: SheetItem

---

### ui_styles.py

UI styling utilities.

#### Functions

**`get_common_resources()`**
- **Purpose**: Get common WPF resources
- **Returns**: Resource dictionary

**`create_color_brush(color_name)`**
- **Purpose**: Create color brush from name
- **Args**:
  - `color_name`: Color name
- **Returns**: SolidColorBrush

---

### ui_utils.py

UI utility functions.

#### Functions

**`create_modern_button(content, click_handler=None, height=None, width=None, style_name="ModernButton")`**
- **Purpose**: Create modern WPF button
- **Args**:
  - `content`: Button content
  - `click_handler`: Click event handler
  - `height`: Button height
  - `width`: Button width
  - `style_name`: Style name
- **Returns**: Button control

**`create_icon_button(icon_text, click_handler=None, tooltip=None)`**
- **Purpose**: Create icon button
- **Args**:
  - `icon_text`: Icon text
  - `click_handler`: Click handler
  - `tooltip`: Tooltip text
- **Returns**: Button control

**`create_modern_textbox(text="", watermark=None, max_length=None)`**
- **Purpose**: Create modern textbox
- **Args**:
  - `text`: Initial text
  - `watermark`: Watermark text
  - `max_length`: Maximum length
- **Returns**: TextBox control

**`create_filter_textbox(placeholder="Filter items...", change_handler=None)`**
- **Purpose**: Create filter textbox
- **Args**:
  - `placeholder`: Placeholder text
  - `change_handler`: Text change handler
- **Returns**: TextBox control

**`create_modern_checkbox(content, is_checked=False, click_handler=None)`**
- **Purpose**: Create modern checkbox
- **Args**:
  - `content`: Checkbox content
  - `is_checked`: Initial checked state
  - `click_handler`: Click handler
- **Returns**: CheckBox control

**`create_header_text(text, font_size=None)`**
- **Purpose**: Create header text
- **Args**:
  - `text`: Header text
  - `font_size`: Font size
- **Returns**: TextBlock control

**`create_body_text(text, foreground=None)`**
- **Purpose**: Create body text
- **Args**:
  - `text`: Body text
  - `foreground`: Foreground color
- **Returns**: TextBlock control

**`setup_window_properties(window, title, width=None, height=None)`**
- **Purpose**: Setup window properties
- **Args**:
  - `window`: Window to setup
  - `title`: Window title
  - `width`: Window width
  - `height`: Window height

**`center_window_on_screen(window)`**
- **Purpose**: Center window on screen
- **Args**:
  - `window`: Window to center

**`validate_text_input(text, min_length=0, max_length=None, allow_empty=False)`**
- **Purpose**: Validate text input
- **Args**:
  - `text`: Text to validate
  - `min_length`: Minimum length
  - `max_length`: Maximum length
  - `allow_empty`: Allow empty text
- **Returns**: Validation result

**`validate_numeric_input(value, min_value=None, max_value=None)`**
- **Purpose**: Validate numeric input
- **Args**:
  - `value`: Value to validate
  - `min_value`: Minimum value
  - `max_value`: Maximum value
- **Returns**: Validation result

**`log_ui_action(action, details=None)`**
- **Purpose**: Log UI action
- **Args**:
  - `action`: Action name
  - `details`: Action details

**`safe_ui_operation(operation_func, error_message="UI operation failed")`**
- **Purpose**: Execute UI operation safely
- **Args**:
  - `operation_func`: Function to execute
  - `error_message`: Error message
- **Returns**: Operation result

---

## GUI Module

### WPF_Base.py

Base WPF window class for Revit UI.

**`WPFWindow`** - Base class for WPF-based Revit windows.

### forms.py

Form utilities and helpers.

**`select_from_dict()`** - Select item from dictionary with UI.

### FindReplace.py

Find and replace dialog for text operations.

### SelectFromDict.py

Dictionary-based selection dialog.

### Tools/CreateFromRooms.py

Create elements from rooms utility.

---

## pykostik Module

### pykostik Overview

External library adapted from pyKostik project. Provides wrappers and utilities for Revit API.

### revit/db/

**`transaction.py`** - Transaction utilities and wrappers.

**`failure.py`** - Failure handling utilities.

### utils/

**`callables.py`** - Callable utilities.

**`iterables.py`** - Iterable utilities.

**`mathematic.py`** - Math utilities.

**`table.py`** - Table data handling.

### wrappers/

**`abstracts.py`** - Abstract base classes.

**`application_services.py`** - Application service wrappers.

**`creation.py`** - Element creation wrappers.

**`db/`** - Database wrappers for Revit elements.

**`ui/selection.py`** - Selection wrappers.

---

## FamilyProfileUpdater Module

Module for updating family profiles from CSV data.

**Structure:**
- `config/profile_configs.py` - Configuration
- `core/csv_processor.py` - CSV processing
- `core/family_manager.py` - Family management
- `ui/main_dialog.py` - Main UI dialog

---

## Samples Module

Sample code and templates for pyRevit development.

**Files:**
- `CreateElements.py` - Element creation examples
- `FilteredElementCollector.py` - Collector examples
- `Parameters.py` - Parameter operations
- `Selection.py` - Selection examples
- `TemplatePyRevit.py` - Full pyRevit template
- `TemplatePyRevitMin.py` - Minimal template
- `TemplatePyRevitSafe.py` - Safe template with error handling
- `Transactions.py` - Transaction examples
- `ViewsSheets.py` - View and sheet examples

---

## Utilities Module

**`parameters.py`** - Parameter utilities.

**`revit_database.py`** - Revit database utilities.

---

## Visualization Module

**`colorize.py`** - Color generation and override management (duplicate of root colorize.py with additional dependencies).

---

## Usage Guidelines

### Import Patterns

```python
# Core library imports
from geometry_matching import match_beams
from view_generator import ViewGenerator
from smart_tag_engine import SmartTagEngine

# Parameters framework
from parameters.framework import ParameterSettingFramework
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME

# Elements module
from elements.element_names import get_family_name, get_type_name

# Snippets
from Snippets.smart_selection import get_filtered_selection
from Snippets._worksharing import is_element_editable

# UI framework
from ui.base_window import BaseRevitWindow
```

### Best Practices

1. **Always use error handling** when calling library functions
2. **Check return values** for None/null results
3. **Use appropriate optimization levels** for parameter operations
4. **Validate inputs** before processing
5. **Log operations** for debugging and monitoring

### Error Handling

```python
try:
    result = some_lib_function(args)
    if result is None:
        # Handle failure
        logger.warning("Function returned None")
except Exception as e:
    logger.error("Library function failed: {}".format(str(e)))
```

---

## Potential Redundancies

The following modules may have overlapping functionality and could be candidates for consolidation:

| Module | Potential Overlap | Notes |
|--------|-------------------|-------|
| `colorize.py` | `visualization/colorize.py` | Similar functionality, visualization version imports from utilities |
| `strUtils.py` | `stringFormating.py` | Both handle string utilities |
| `join_utils.py` | `join_columns.py` | Both handle joining operations |

---

## Backup Files

The following backup files exist and should be cleaned up:

- `area_reinforcement_backup_before_multi_layer_expansion.py`
- `customOutput_backup.py`
- `view_generator_backup.py`

---

This documentation covers all major functions and classes available in the lib/ folder. For specific implementation details, refer to the source code and docstrings.

**Last Updated:** 2026-02-14
**Version:** 2.0
