---
id: "LOG-UTIL-UI-008"
version: "v1"
status: "active"
category: "utilities/ui"
element_type: "Naming"
operation: "format_string_generation"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["ui", "naming", "format_string", "csv", "placeholders", "family_types", "bulk_processing"]
created: "2025-10-27"
updated: "2025-10-27"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Templates.panel/Family.pulldown/FamilyTypeGenerator.pushbutton/script.py"
source_location: "Templates.panel/Family.pulldown/FamilyTypeGenerator.pushbutton"
---

# LOG-UTIL-UI-008-v1: Format String Naming Generator (CSV Column to Name Conversion)

## Problem Context

Dalam tools yang perlu generate nama dari data CSV, sering diperlukan cara untuk convert multiple kolom menjadi satu string nama yang konsisten. Tantangan utama adalah:

1. **Multi-Column Naming**: Gabungkan beberapa kolom CSV menjadi nama type
2. **Flexible Formatting**: User perlu control format output
3. **Placeholder System**: Sistem placeholder yang mudah dipahami
4. **Real-time Preview**: Lihat hasil sebelum apply

Dari Family Type Generator, berhasil convert kolom "Type Plinth", "Length", "Width", "Foundation Thickness (mm)" menjadi nama seperti "PLINTH 1 300x300x795mm".

## Solution Summary

Implementasi sistem placeholder-based naming dengan format strings yang fleksibel, validation real-time, dan preview system untuk user feedback.

## Working Code

### Type Name Generator Core

```python
class TypeNameGenerator:
    """Handles type name generation using format strings with column placeholders"""

    def __init__(self, csv_headers):
        self.csv_headers = csv_headers
        self.format_string = ""

    def set_format_string(self, format_str):
        """Set the format string for name generation"""
        self.format_string = format_str

    def generate_name(self, csv_row):
        """Generate type name from CSV row using format string"""
        if not self.format_string:
            return ""

        try:
            # Replace {column_name} placeholders with actual values
            result = self.format_string

            for header in self.csv_headers:
                placeholder = "{" + header + "}"
                value = str(csv_row.get(header, "")).strip()
                result = result.replace(placeholder, value)

            return result.strip()

        except Exception as e:
            return "Error: {}".format(str(e))

    def validate_format_string(self):
        """Validate that format string contains valid placeholders"""
        if not self.format_string:
            return False, "Format string cannot be empty"

        # Check if format string contains at least one placeholder
        has_placeholder = any("{" + header + "}" in self.format_string for header in self.csv_headers)
        if not has_placeholder:
            return False, "Format string must contain at least one column placeholder like {ColumnName}"

        return True, "Format string is valid"

    def get_available_placeholders(self):
        """Get list of available placeholders for the UI"""
        return ["{" + header + "}" for header in self.csv_headers]
```

### Preview System

```python
class TypeNamePreviewItem(object):
    """Item for previewing generated type names"""

    def __init__(self, csv_row, generated_name, original_name=""):
        self.csv_row = csv_row
        self.generated_name = generated_name
        self.original_name = original_name
        self.tooltip = "Generated from format string"

    @property
    def preview_text(self):
        """Get preview text showing original -> generated"""
        if self.original_name:
            return "{} → {}".format(self.original_name, self.generated_name)
        return self.generated_name
```

## Key Techniques

### 1. Placeholder Replacement Algorithm

```python
def generate_name(self, csv_row):
    result = self.format_string
    for header in self.csv_headers:
        placeholder = "{" + header + "}"
        value = str(csv_row.get(header, "")).strip()
        result = result.replace(placeholder, value)
    return result.strip()
```

### 2. Format String Validation

```python
def validate_format_string(self):
    if not self.format_string:
        return False, "Format string cannot be empty"

    has_placeholder = any("{" + header + "}" in self.format_string
                         for header in self.csv_headers)
    if not has_placeholder:
        return False, "Must contain at least one {ColumnName} placeholder"

    return True, "Format string is valid"
```

### 3. Real-time Preview Generation

```python
def generate_preview(self, csv_rows, max_preview=10):
    """Generate preview for first N rows"""
    preview_items = []
    for row in csv_rows[:max_preview]:
        generated_name = self.generate_name(row)
        original_name = row.get('Name', '')
        preview_item = TypeNamePreviewItem(row, generated_name, original_name)
        preview_items.append(preview_item)
    return preview_items
```

## Performance Notes

- **Execution Time**: Fast (O(n*m) where n=placeholders, m=rows)
- **Memory Usage**: Low (string operations only)
- **Scalability**: Excellent (handles 1000+ rows efficiently)
- **Validation**: Real-time with immediate feedback

## Usage Examples

### Basic Format String Generation

```python
from logic_library.active.utilities.ui.format_string_naming import TypeNameGenerator

# CSV headers
headers = ['Type Plinth', 'Length', 'Width', 'Foundation Thickness (mm)']

# Create generator
name_gen = TypeNameGenerator(headers)

# Set format string
format_str = "{Type Plinth} {Length}x{Width}x{Foundation Thickness (mm)}mm"
name_gen.set_format_string(format_str)

# Validate
is_valid, message = name_gen.validate_format_string()
print(message)  # "Format string is valid"

# Generate names
csv_row = {
    'Type Plinth': 'PLINTH 1',
    'Length': '300',
    'Width': '300',
    'Foundation Thickness (mm)': '795'
}

type_name = name_gen.generate_name(csv_row)
print(type_name)  # "PLINTH 1 300x300x795mm"
```

### Integration with CSV Processing

```python
def process_csv_with_naming(csv_path):
    """Process CSV with custom naming"""

    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)

    # Get format string from user
    format_str = get_format_string_from_user(headers, rows[:5])

    # Create name generator
    name_gen = TypeNameGenerator(headers)
    name_gen.set_format_string(format_str)

    # Process rows
    for row in rows:
        type_name = name_gen.generate_name(row)
        # Create family type with generated name...
```

## Comparison with Basic Naming

| Aspect | Basic Naming | Format String Naming |
|--------|--------------|----------------------|
| **Flexibility** | Limited | Highly flexible |
| **Multi-column** | No | Yes |
| **User Control** | None | Full control |
| **Consistency** | Manual | Automated |
| **Preview** | None | Real-time |
| **Validation** | None | Built-in |

## Integration with Logic Library

### File Structure
```
logic-library/active/utilities/ui/
├── LOG-UTIL-UI-005-v1-simple-option-selection.md
├── LOG-UTIL-UI-008-v1-format-string-naming-generator.md
└── format_string_naming.py
```

### Import Pattern
```python
# For format string naming generation
from logic_library.active.utilities.ui.format_string_naming import (
    TypeNameGenerator,
    TypeNamePreviewItem
)
```

## Related Logic Entries

- [LOG-UTIL-UI-007-v1-wpf-interactive-builder-framework](LOG-UTIL-UI-007-v1-wpf-naming-convention-builder.md) - WPF UI framework
- [LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching](LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching.md) - CSV parameter matching
- [LOG-UTIL-FILTER-001-v1-filter-rule-parser](LOG-UTIL-FILTER-001-v1-filter-rule-parser.md) - Text processing

## Best Practices

### Format String Design

1. **Clear Placeholders**: Use descriptive column names in {}
2. **Consistent Spacing**: Include spaces between elements
3. **Unit Indicators**: Add units like "mm" for clarity
4. **Validation**: Always validate before processing

### Preview Usage

1. **Sample Data**: Show first 5-10 rows for preview
2. **Edge Cases**: Include rows with missing data
3. **Real-time Updates**: Update preview as user types
4. **Error Handling**: Show validation errors clearly

### Integration Patterns

```python
def create_naming_workflow(csv_headers, csv_rows):
    """Complete naming workflow"""

    # 1. Create generator
    name_gen = TypeNameGenerator(csv_headers)

    # 2. Get format string (could be from UI)
    format_str = get_format_string_interactive(csv_headers, csv_rows)

    # 3. Validate and set
    is_valid, message = name_gen.validate_format_string()
    if not is_valid:
        raise ValueError(message)

    name_gen.set_format_string(format_str)

    # 4. Generate preview
    preview = name_gen.generate_preview(csv_rows)

    # 5. Process all rows
    for row in csv_rows:
        type_name = name_gen.generate_name(row)
        # Use generated name...
```

## Future Applications

### 1. Dynamic Report Naming
Generate nama file report dari multiple data sources.

### 2. Asset Naming Standards
Standardisasi naming untuk BIM assets dari berbagai sources.

### 3. Configuration File Generation
Generate nama konfigurasi dari parameter combinations.

### 4. Template-Based Naming
Pre-built naming templates untuk industri tertentu.

## Optimization History

*Initial implementation (v1) developed for Family Type Generator, successfully converting CSV columns to structured names like "PLINTH 1 300x300x795mm". Placeholder system proved intuitive with real-time validation and preview capabilities.*

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-27