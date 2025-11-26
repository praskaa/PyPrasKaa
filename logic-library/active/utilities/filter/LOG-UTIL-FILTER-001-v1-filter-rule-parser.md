---
title: "Filter Rule Parser"
version: "1.0"
category: "utilities/filter"
tags: ["filter", "rules", "parser", "validation", "legend"]
author: "Kilo Code"
tested_on: "Revit 2024, pyRevit 4.8.x"
status: "active"
last_updated: "2025-10-23"
---

# Filter Rule Parser

## Problem Statement

Revit filter rules are complex objects with multiple types (string, numeric, element ID, etc.) and evaluators. Parsing these rules for display, validation, or analysis requires repetitive code and deep knowledge of the Revit API filter system.

## Solution Overview

A comprehensive parser that extracts meaningful information from all types of Revit filter rules, converting them into structured data suitable for display, reporting, and analysis.

## Key Components

### 1. Rule Parser Class

```python
class ef_Rule:
    """Parser for individual FilterRule objects."""

    dict_BIPs = {str(i.value__): i for i in BuiltInParameter.GetValues(BuiltInParameter)}

    def __init__(self, rule):
        """
        Parse a FilterRule into structured data.

        Args:
            rule (FilterRule): Revit filter rule object

        Attributes:
            rule_param_name (str): Human-readable parameter name
            rule_value (str/int/float): Rule value in appropriate format
            rule_eval (str): Rule evaluator (equals, greater than, etc.)
        """
        self.rule = rule
        self.get_rule_value()
```

### 2. Filter Parser Class

```python
class ef_Filter:
    """Parser for ParameterFilterElement objects."""

    def __init__(self, pfe):
        """
        Parse a ParameterFilterElement into structured data.

        Args:
            pfe (ParameterFilterElement): Revit filter element

        Attributes:
            pfe (ParameterFilterElement): Original filter element
            cats (list): List of Category objects
            cat_names (list): List of category names
            rules (list): List of parsed ef_Rule objects
        """
        self.pfe = pfe
        self.cats = self.get_categories()
        self.cat_names = [cat.Name for cat in self.cats]
        self.rules = self.get_rules()
```

## Supported Rule Types

### 1. String Rules

```python
# FilterStringRule examples
rule = FilterStringRule(parameterId, FilterStringEvaluator.Equals, "BEAM")
# Parsed as: rule_eval="equals", rule_value="BEAM"
```

### 2. Numeric Rules

```python
# FilterDoubleRule examples
rule = FilterDoubleRule(parameterId, FilterNumericEvaluator.Greater, 100.0)
# Parsed as: rule_eval="greater", rule_value=100.0
```

### 3. Integer Rules (with Workset Handling)

```python
# FilterIntegerRule with workset conversion
rule = FilterIntegerRule(worksetParamId, FilterNumericEvaluator.Equals, worksetId)
# Parsed as: rule_eval="equals", rule_value="Workset Name" (not raw ID)
```

### 4. Element ID Rules

```python
# FilterElementIdRule with element name resolution
rule = FilterElementIdRule(parameterId, FilterNumericEvaluator.Equals, elementId)
# Parsed as: rule_eval="equals", rule_value="Element Name" (not raw ID)
```

### 5. Inverse Rules

```python
# FilterInverseRule handling
inverse_rule = FilterInverseRule(someRule)
# Parsed as: rule_eval="not equals" (automatically prefixed)
```

### 6. Special Rules

```python
# HasValueFilterRule
rule = HasValueFilterRule(parameterId)
# Parsed as: rule_eval="HasValue", rule_value="-"

# HasNoValueFilterRule
rule = HasNoValueFilterRule(parameterId)
# Parsed as: rule_eval="HasNoValue", rule_value="-"

# SharedParameterApplicableRule
rule = SharedParameterApplicableRule(sharedParam)
# Parsed as: rule_eval="Exists", rule_value="-"
```

## Parameter Name Resolution

### Built-in Parameters

```python
# Automatic conversion to human-readable names
bip_id = BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH
readable_name = LabelUtils.GetLabelFor(bip_id)  # "Width"
```

### Shared Parameters

```python
# Lookup from document
shared_param = doc.GetElement(parameterId)
param_name = shared_param.Name if shared_param else "Unknown Parameter"
```

### Workset Parameters

```python
# Special handling for workset IDs
workset_id = rule.RuleValue
workset_name = workset_names.get(int(str(workset_id)), f"Workset {workset_id}")
```

## Integration Patterns

### With Legend Generation

```python
def create_filter_legend(doc, view, filters):
    """Create visual legend for filters."""

    for filter_elem in filters:
        parsed_filter = ef_Filter(filter_elem)

        # Display categories
        categories_text = ', '.join(parsed_filter.cat_names)
        create_text_note(doc, view, x, y, categories_text, text_type)

        # Display rules
        for rule in parsed_filter.rules:
            rule_text = f"{rule.rule_param_name} {rule.rule_eval} {rule.rule_value}"
            create_text_note(doc, view, x, y, rule_text, text_type)
            y -= spacing
```

### With Filter Validation

```python
def validate_filter_rules(filter_elem):
    """Validate filter has meaningful rules."""

    parsed = ef_Filter(filter_elem)

    if not parsed.rules:
        return "No rules defined"

    for rule in parsed.rules:
        if rule.rule_value == "-" and rule.rule_eval in ["HasValue", "HasNoValue"]:
            continue  # Valid special rule
        elif not rule.rule_value or rule.rule_value == "Unknown":
            return f"Invalid rule value for {rule.rule_param_name}"

    return "Valid"
```

### With Filter Comparison

```python
def compare_filters(filter1, filter2):
    """Compare two filters for equivalence."""

    parsed1 = ef_Filter(filter1)
    parsed2 = ef_Filter(filter2)

    # Compare categories
    if set(parsed1.cat_names) != set(parsed2.cat_names):
        return False

    # Compare rules (simplified)
    if len(parsed1.rules) != len(parsed2.rules):
        return False

    # Detailed rule comparison would go here
    return True
```

## Usage Examples

### Basic Filter Analysis

```python
# Get all filters in document
filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()

for filter_elem in filters:
    parsed = ef_Filter(filter_elem)

    print(f"Filter: {filter_elem.Name}")
    print(f"Categories: {', '.join(parsed.cat_names)}")

    for rule in parsed.rules:
        print(f"  Rule: {rule.rule_param_name} {rule.rule_eval} {rule.rule_value}")
```

### Filter Report Generation

```python
def generate_filter_report(doc):
    """Generate CSV report of all filters."""

    filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()

    with open('filter_report.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Filter Name', 'Categories', 'Parameter', 'Evaluator', 'Value'])

        for filter_elem in filters:
            parsed = ef_Filter(filter_elem)

            for rule in parsed.rules:
                writer.writerow([
                    filter_elem.Name,
                    '; '.join(parsed.cat_names),
                    rule.rule_param_name,
                    rule.rule_eval,
                    str(rule.rule_value)
                ])
```

### Filter Override Visualization

```python
def visualize_filter_overrides(view, filter_elem):
    """Create visual representation of filter graphics overrides."""

    parsed = ef_Filter(filter_elem)

    # Get overrides
    overrides = view.GetFilterOverrides(filter_elem.Id)

    # Create legend entry
    legend_text = f"{filter_elem.Name}\\nCategories: {', '.join(parsed.cat_names)}"

    # Add visual sample with override colors
    region = create_region(doc, view, x, y, width, height)
    override_graphics_region(doc, view, region,
                           fg_color=overrides.SurfaceForegroundPatternColor,
                           bg_color=overrides.SurfaceBackgroundPatternColor)
```

## Error Handling

```python
def safe_parse_filter(filter_elem):
    """Parse filter with comprehensive error handling."""

    try:
        parsed = ef_Filter(filter_elem)

        # Validate parsed data
        if not parsed.cat_names:
            logger.warning(f"Filter {filter_elem.Name} has no categories")

        if not parsed.rules:
            logger.warning(f"Filter {filter_elem.Name} has no rules")

        return parsed

    except Exception as e:
        logger.error(f"Failed to parse filter {filter_elem.Name}: {e}")
        return None
```

## Performance Considerations

- **Caching**: Cache parsed filters for repeated access
- **Batch Processing**: Parse multiple filters in single operation
- **Lazy Loading**: Only parse rules when needed
- **Memory Management**: Clean up large filter collections

## Compatibility

- **Revit Versions**: 2021+ (all filter rule types supported)
- **pyRevit**: 4.8.x+
- **Dependencies**: Requires access to document for parameter resolution

## Cross-References

- **Annotations**: `LOG-UTIL-ANNOTATIONS-001-v1-text-graphics-creation.md`
- **Graphics Overrides**: `Snippets._overrides` module
- **View Analysis**: `LOG-UTIL-VIEW-001-v1-view-filter-analysis.md`

## Testing Recommendations

```python
def test_filter_parsing():
    """Test filter parsing with various rule types."""

    # Test string rule
    string_rule = create_string_rule()
    parsed = ef_Rule(string_rule)
    assert parsed.rule_eval == "equals"
    assert parsed.rule_value == "test_value"

    # Test numeric rule
    numeric_rule = create_numeric_rule()
    parsed = ef_Rule(numeric_rule)
    assert isinstance(parsed.rule_value, (int, float))

    # Test element ID rule
    element_rule = create_element_rule()
    parsed = ef_Rule(element_rule)
    assert "element" in parsed.rule_value.lower() or parsed.rule_value != str(element_id)
```

## Future Enhancements

- [ ] Add support for custom evaluators
- [ ] Add filter performance analysis
- [ ] Add filter conflict detection
- [ ] Add filter optimization suggestions
- [ ] Add support for filter templates