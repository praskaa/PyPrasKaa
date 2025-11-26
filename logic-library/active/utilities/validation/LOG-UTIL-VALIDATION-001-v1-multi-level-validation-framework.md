# LOG-UTIL-VALIDATION-001-v1-multi-level-validation-framework.md

## Multi-Level Validation Framework

**Version:** 1.0.0
**Date:** 2025-10-22
**Author:** Prasetyo

### Description
Comprehensive validation framework implementing hierarchical validation patterns for structural elements. Provides a structured approach to validate elements through multiple levels: geometric intersection, type compatibility, parameter validation, and engineering validation.

### Core Framework Architecture

#### **ValidationLevel Enum**
```python
class ValidationLevel:
    GEOMETRIC = 1      # Spatial/intersection validation
    TYPE_COMPATIBILITY = 2  # Semantic/type matching
    PARAMETER = 3      # Quantitative parameter comparison
    ENGINEERING = 4    # Element-specific engineering validation
```

#### **ValidationResult Class**
```python
class ValidationResult:
    def __init__(self, passed, status, details=None, level=None):
        self.passed = passed          # Boolean: validation success
        self.status = status          # String: status message
        self.details = details or {}  # Dict: detailed validation data
        self.level = level           # ValidationLevel: which level failed

    def __bool__(self):
        return self.passed
```

#### **BaseValidator Class**
```python
class BaseValidator:
    """
    Base class for all structural element validators.
    Implements the 4-level validation hierarchy.
    """

    def __init__(self, element_type):
        self.element_type = element_type
        self.validation_levels = [
            ValidationLevel.GEOMETRIC,
            ValidationLevel.TYPE_COMPATIBILITY,
            ValidationLevel.PARAMETER,
            ValidationLevel.ENGINEERING
        ]

    def validate(self, host_element, linked_elements_dict):
        """
        Main validation entry point with hierarchical processing.

        Args:
            host_element: Element from host model
            linked_elements_dict: Dict of linked elements {id: {'element': elem, 'geometry': geom}}

        Returns:
            ValidationResult: Complete validation outcome
        """
        for level in self.validation_levels:
            result = self.validate_level(host_element, linked_elements_dict, level)
            if not result.passed:
                return result

        return ValidationResult(True, "Approved", {"all_levels_passed": True})

    def validate_level(self, host_element, linked_elements_dict, level):
        """
        Dispatch validation to appropriate level method.
        """
        level_methods = {
            ValidationLevel.GEOMETRIC: self.validate_geometric,
            ValidationLevel.TYPE_COMPATIBILITY: self.validate_type_compatibility,
            ValidationLevel.PARAMETER: self.validate_parameters,
            ValidationLevel.ENGINEERING: self.validate_engineering
        }

        method = level_methods.get(level)
        if method:
            return method(host_element, linked_elements_dict)
        else:
            return ValidationResult(False, "Unknown validation level", level=level)
```

### Level-Specific Validation Methods

#### **1. Geometric Validation (Level 1)**
```python
def validate_geometric(self, host_element, linked_elements_dict):
    """
    Level 1: Geometric intersection validation.
    Finds best spatial match based on geometry intersection.
    """
    best_match, intersection_score = self.find_best_geometric_match(
        host_element, linked_elements_dict
    )

    if not best_match:
        return ValidationResult(False, "No geometric intersection found",
                              {"intersection_score": 0.0}, ValidationLevel.GEOMETRIC)

    # Store best match for subsequent levels
    self.best_match = best_match
    self.intersection_score = intersection_score

    return ValidationResult(True, "Geometric intersection found",
                          {"best_match_id": best_match.Id, "score": intersection_score})
```

#### **2. Type Compatibility Validation (Level 2)**
```python
def validate_type_compatibility(self, host_element, linked_elements_dict):
    """
    Level 2: Semantic type matching.
    Ensures elements are of compatible types (circular column vs circular column).
    """
    if not hasattr(self, 'best_match'):
        return ValidationResult(False, "No geometric match available",
                              level=ValidationLevel.TYPE_COMPATIBILITY)

    host_type = self.detect_element_type(host_element)
    linked_type = self.detect_element_type(self.best_match)

    if host_type != linked_type:
        return ValidationResult(False, "Type incompatibility",
                              {"host_type": host_type, "linked_type": linked_type},
                              ValidationLevel.TYPE_COMPATIBILITY)

    return ValidationResult(True, "Types compatible",
                          {"element_type": host_type})
```

#### **3. Parameter Validation (Level 3)**
```python
def validate_parameters(self, host_element, linked_elements_dict):
    """
    Level 3: Quantitative parameter comparison.
    Compares dimensions and other measurable properties.
    """
    if not hasattr(self, 'best_match'):
        return ValidationResult(False, "No geometric match available",
                              level=ValidationLevel.PARAMETER)

    host_params = self.extract_parameters(host_element)
    linked_params = self.extract_parameters(self.best_match)

    if not host_params or not linked_params:
        return ValidationResult(False, "Parameter extraction failed",
                              {"host_params": host_params, "linked_params": linked_params},
                              ValidationLevel.PARAMETER)

    comparison_result = self.compare_parameters(host_params, linked_params)
    if not comparison_result['passed']:
        return ValidationResult(False, "Parameter mismatch",
                              comparison_result, ValidationLevel.PARAMETER)

    return ValidationResult(True, "Parameters match",
                          comparison_result)
```

#### **4. Engineering Validation (Level 4)**
```python
def validate_engineering(self, host_element, linked_elements_dict):
    """
    Level 4: Element-specific engineering validation.
    Validates engineering-critical properties (capacity, loading, etc.)
    """
    if not hasattr(self, 'best_match'):
        return ValidationResult(False, "No geometric match available",
                              level=ValidationLevel.ENGINEERING)

    # Element-specific engineering validation
    engineering_result = self.validate_engineering_properties(host_element, self.best_match)

    if not engineering_result['passed']:
        return ValidationResult(False, engineering_result.get('reason', 'Engineering validation failed'),
                              engineering_result, ValidationLevel.ENGINEERING)

    return ValidationResult(True, "Engineering validation passed",
                          engineering_result)
```

### Utility Methods

#### **Geometric Matching**
```python
def find_best_geometric_match(self, host_element, linked_elements_dict):
    """
    Advanced geometric matching with intersection volume analysis.
    """
    host_geometry = self.extract_geometry(host_element)
    if not host_geometry:
        return None, 0.0

    best_match = None
    max_score = 0.0
    candidates = []

    for elem_id, elem_data in linked_elements_dict.items():
        linked_geometry = elem_data.get('geometry')
        if not linked_geometry:
            continue

        score = self.calculate_intersection_score(host_geometry, linked_geometry)
        candidates.append((elem_id, score))

        if score > max_score:
            max_score = score
            best_match = elem_data['element']

    # Log top candidates for debugging
    self.log_top_candidates(sorted(candidates, key=lambda x: x[1], reverse=True)[:5], max_score)

    return best_match, max_score

def calculate_intersection_score(self, geom1, geom2):
    """
    Calculate geometric intersection score.
    Override in subclasses for element-specific scoring.
    """
    try:
        intersection = BooleanOperationsUtils.ExecuteBooleanOperation(
            geom1, geom2, BooleanOperationsType.Intersect
        )
        return intersection.Volume if intersection else 0.0
    except:
        return 0.0
```

#### **Parameter Extraction**
```python
def extract_parameters(self, element):
    """
    Hierarchical parameter extraction with multiple fallback levels.
    """
    # Level 1: Built-in parameters
    params = self.extract_builtin_parameters(element)
    if params:
        return params

    # Level 2: Instance-level custom parameters
    params = self.extract_instance_parameters(element)
    if params:
        return params

    # Level 3: Type-level parameters
    params = self.extract_type_parameters(element)
    if params:
        return params

    return None

def extract_builtin_parameters(self, element):
    """Extract Revit built-in parameters. Override in subclasses."""
    return {}

def extract_instance_parameters(self, element):
    """Extract instance-level custom parameters. Override in subclasses."""
    return {}

def extract_type_parameters(self, element):
    """Extract type-level parameters. Override in subclasses."""
    return {}
```

#### **Type Detection**
```python
def detect_element_type(self, element):
    """
    Intelligent type detection using name-based analysis.
    """
    # Primary: Name-based detection
    type_from_name = self.detect_type_from_name(element)
    if type_from_name:
        return type_from_name

    # Secondary: Parameter-based detection
    type_from_params = self.detect_type_from_parameters(element)
    if type_from_params:
        return type_from_params

    return 'unknown'

def detect_type_from_name(self, element):
    """
    Parse family/type names to detect element type.
    """
    family_symbol = self.get_family_type(element)
    if not family_symbol:
        return None

    # Parse names with multiple separators
    names = []
    if family_symbol.Family and family_symbol.Family.Name:
        names.append(family_symbol.Family.Name)
    if family_symbol.Name:
        names.append(family_symbol.Name)

    all_parts = []
    for name in names:
        # Handle multiple separators
        for sep in ['-', '_', ' ']:
            if sep in name:
                all_parts.extend([part.strip() for part in name.split(sep)])
                break
        else:
            all_parts.append(name)

    # Element-specific keyword matching
    return self.match_type_keywords(all_parts)

def match_type_keywords(self, name_parts):
    """
    Match name parts against type keywords.
    Override in subclasses for element-specific keywords.
    """
    # Default implementation - override in subclasses
    return None
```

### Concrete Implementations

#### **ColumnValidator**
```python
class ColumnValidator(BaseValidator):
    def __init__(self):
        super().__init__("column")

    def match_type_keywords(self, name_parts):
        keywords = {
            'circular': ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat'],
            'square': ['square', 'box', 'kuadrat'],
            'rectangular': ['rectangular', 'rectangle', 'rect', 'persegi panjang']
        }

        for part in name_parts:
            part_lower = part.lower()
            for type_name, type_keywords in keywords.items():
                if part_lower in type_keywords:
                    return type_name
        return None

    def extract_builtin_parameters(self, column):
        params = {}
        # Extract b, h, diameter using BuiltInParameters
        b_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        if b_param and b_param.HasValue:
            params['b'] = b_param.AsDouble()

        h_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        if h_param and h_param.HasValue:
            params['h'] = h_param.AsDouble()

        diam_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_DIAMETER)
        if diam_param and diam_param.HasValue:
            params['diameter'] = diam_param.AsDouble()

        return params if params else None

    def validate_engineering(self, host_column, linked_column):
        """Column-specific engineering validation (if needed)"""
        return {'passed': True, 'reason': 'No specific engineering validation required for columns'}
```

#### **WallValidator**
```python
class WallValidator(BaseValidator):
    def __init__(self):
        super().__init__("wall")

    def match_type_keywords(self, name_parts):
        keywords = {
            'exterior': ['exterior', 'external', 'outside'],
            'interior': ['interior', 'internal', 'inside'],
            'curtain': ['curtain', 'glazed'],
            'bearing': ['bearing', 'structural']
        }
        # Implementation similar to ColumnValidator
        return None

    def validate_engineering(self, host_wall, linked_wall):
        """Wall-specific engineering validation"""
        # Check wall function, structural role, etc.
        return {'passed': True}
```

### Usage Examples

#### **Basic Usage**
```python
# Create validator
column_validator = ColumnValidator()

# Prepare linked elements dictionary
linked_columns_dict = {}
for column in linked_columns:
    geometry = extract_geometry(column)
    linked_columns_dict[column.Id] = {
        'element': column,
        'geometry': geometry
    }

# Validate single column
result = column_validator.validate(host_column, linked_columns_dict)

if result.passed:
    print(f"Column {host_column.Id} validation: PASSED")
else:
    print(f"Column {host_column.Id} validation: FAILED at level {result.level}")
    print(f"Status: {result.status}")
    print(f"Details: {result.details}")
```

#### **Batch Validation**
```python
def validate_all_columns(host_columns, linked_columns_dict):
    validator = ColumnValidator()
    results = {}

    for host_column in host_columns:
        result = validator.validate(host_column, linked_columns_dict)
        results[host_column.Id] = result

        # Set comment parameter based on result
        set_comment_parameter(host_column, result.status)

    return results
```

### Benefits

#### **Structured Approach**
- Clear validation hierarchy prevents confusion
- Each level has specific responsibility
- Easy to debug which level failed

#### **Extensible Design**
- Base class can be extended for new element types
- Level-specific methods can be overridden
- New validation levels can be added

#### **Comprehensive Validation**
- Covers spatial, semantic, quantitative, and engineering aspects
- Provides detailed failure information
- Supports debugging and troubleshooting

#### **Reusable Framework**
- Consistent API across all element validators
- Can be used in various scripts and tools
- Integrates with existing utility functions

### Integration with Logic Library

#### **File Structure**
```
logic-library/active/utilities/validation/
├── LOG-UTIL-VALIDATION-001-v1-multi-level-validation-framework.md  # Documentation
├── validation_framework.py                                         # Implementation
└── validators/
    ├── column_validator.py
    ├── wall_validator.py
    ├── beam_validator.py
    └── foundation_validator.py
```

#### **Import Pattern**
```python
from logic_library.active.utilities.validation.validation_framework import (
    BaseValidator, ValidationLevel, ValidationResult
)
from logic_library.active.utilities.validation.validators.column_validator import ColumnValidator
```

### Changelog
**v1.0.0 (2025-10-22)**:
- Initial implementation of multi-level validation framework
- Base validator class with 4-level hierarchy
- Column validator implementation
- Comprehensive documentation and examples
- Integration guidelines for logic library