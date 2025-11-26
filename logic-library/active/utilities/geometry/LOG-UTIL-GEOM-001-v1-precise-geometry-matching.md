# LOG-UTIL-GEOM-001-v1-precise-geometry-matching.md

## Precise Geometry Matching Utility

**Version:** 1.0.0
**Date:** 2025-10-22
**Author:** Prasetyo

### Description
Advanced geometry matching utility for precise element matching based on shape similarity, dimensional accuracy, and spatial relationships. Implements sophisticated geometric intersection algorithms with configurable matching criteria.

### Core Matching Criteria

#### **1. Shape Similarity Matching**
```python
def calculate_shape_similarity(element1, element2):
    """
    Calculate shape similarity based on geometric properties.
    Considers aspect ratios, cross-sectional profiles, and form factors.

    Args:
        element1, element2: Elements to compare

    Returns:
        float: Similarity score (0.0 to 1.0)
    """
    geom1 = extract_geometry_properties(element1)
    geom2 = extract_geometry_properties(element2)

    if not geom1 or not geom2:
        return 0.0

    # Compare shape characteristics
    shape_score = compare_shape_characteristics(geom1, geom2)

    # Compare dimensional proportions
    proportion_score = compare_dimensional_proportions(geom1, geom2)

    # Weighted combination
    return 0.7 * shape_score + 0.3 * proportion_score
```

#### **2. Dimensional Accuracy Matching**
```python
def calculate_dimensional_accuracy(element1, element2, tolerance_mm=0.01):
    """
    Calculate dimensional matching accuracy with precise tolerance control.

    Args:
        element1, element2: Elements to compare
        tolerance_mm: Tolerance in millimeters

    Returns:
        dict: Accuracy metrics and pass/fail status
    """
    dims1 = extract_precise_dimensions(element1)
    dims2 = extract_precise_dimensions(element2)

    if not dims1 or not dims2:
        return {'passed': False, 'accuracy': 0.0, 'details': 'Dimension extraction failed'}

    # Convert tolerance to feet for comparison
    tolerance_ft = tolerance_mm / 304.8

    accuracy_scores = {}

    # Compare each dimension
    for dim_name in ['width', 'height', 'diameter', 'length']:
        if dim_name in dims1 and dim_name in dims2:
            diff = abs(dims1[dim_name] - dims2[dim_name])
            accuracy_scores[dim_name] = 1.0 if diff <= tolerance_ft else 0.0

    overall_accuracy = sum(accuracy_scores.values()) / len(accuracy_scores) if accuracy_scores else 0.0

    return {
        'passed': overall_accuracy >= 0.95,  # 95% accuracy threshold
        'accuracy': overall_accuracy,
        'details': accuracy_scores
    }
```

#### **3. Spatial Relationship Matching**
```python
def analyze_spatial_relationship(element1, element2):
    """
    Analyze spatial relationships between elements.
    Considers alignment, proximity, and relative positioning.

    Args:
        element1, element2: Elements to analyze

    Returns:
        dict: Spatial relationship metrics
    """
    # Extract location data
    loc1 = extract_element_location(element1)
    loc2 = extract_element_location(element2)

    if not loc1 or not loc2:
        return {'relationship': 'unknown', 'score': 0.0}

    # Calculate spatial metrics
    alignment_score = calculate_alignment_score(loc1, loc2)
    proximity_score = calculate_proximity_score(loc1, loc2)
    orientation_score = calculate_orientation_score(loc1, loc2)

    # Determine relationship type
    if alignment_score > 0.9:
        relationship = 'perfectly_aligned'
    elif alignment_score > 0.7:
        relationship = 'well_aligned'
    elif proximity_score > 0.8:
        relationship = 'adjacent'
    else:
        relationship = 'distant'

    overall_score = (alignment_score + proximity_score + orientation_score) / 3.0

    return {
        'relationship': relationship,
        'score': overall_score,
        'metrics': {
            'alignment': alignment_score,
            'proximity': proximity_score,
            'orientation': orientation_score
        }
    }
```

### Advanced Matching Algorithms

#### **Intersection Volume Analysis**
```python
def analyze_intersection_volume(element1, element2):
    """
    Comprehensive intersection volume analysis with multiple metrics.

    Args:
        element1, element2: Elements to analyze

    Returns:
        dict: Intersection analysis results
    """
    geom1 = extract_solid_geometry(element1)
    geom2 = extract_solid_geometry(element2)

    if not geom1 or not geom2:
        return {'intersection_volume': 0.0, 'overlap_percentage': 0.0}

    try:
        # Calculate intersection
        intersection = BooleanOperationsUtils.ExecuteBooleanOperation(
            geom1, geom2, BooleanOperationsType.Intersect
        )

        if not intersection:
            return {'intersection_volume': 0.0, 'overlap_percentage': 0.0}

        intersection_volume = intersection.Volume

        # Calculate overlap percentages
        vol1 = geom1.Volume
        vol2 = geom2.Volume

        overlap_pct1 = (intersection_volume / vol1 * 100) if vol1 > 0 else 0.0
        overlap_pct2 = (intersection_volume / vol2 * 100) if vol2 > 0 else 0.0

        # Convert to human-readable units
        intersection_mm3 = feet3_to_mm3(intersection_volume)

        return {
            'intersection_volume_cu_ft': intersection_volume,
            'intersection_volume_mm3': intersection_mm3,
            'overlap_percentage_elem1': overlap_pct1,
            'overlap_percentage_elem2': overlap_pct2,
            'average_overlap': (overlap_pct1 + overlap_pct2) / 2.0
        }

    except Exception as e:
        return {'error': str(e), 'intersection_volume': 0.0}
```

#### **Geometric Similarity Scoring**
```python
def calculate_geometric_similarity_score(element1, element2):
    """
    Calculate comprehensive geometric similarity score.
    Combines multiple geometric criteria for robust matching.

    Args:
        element1, element2: Elements to compare

    Returns:
        dict: Similarity analysis with detailed metrics
    """
    scores = {}

    # Shape similarity
    scores['shape'] = calculate_shape_similarity(element1, element2)

    # Dimensional accuracy
    dim_accuracy = calculate_dimensional_accuracy(element1, element2)
    scores['dimensions'] = dim_accuracy['accuracy']

    # Spatial relationship
    spatial_rel = analyze_spatial_relationship(element1, element2)
    scores['spatial'] = spatial_rel['score']

    # Intersection analysis
    intersection = analyze_intersection_volume(element1, element2)
    scores['intersection'] = min(intersection.get('average_overlap', 0.0) / 100.0, 1.0)

    # Weighted overall score
    weights = {
        'shape': 0.2,
        'dimensions': 0.4,
        'spatial': 0.2,
        'intersection': 0.2
    }

    overall_score = sum(scores[metric] * weights[metric] for metric in weights.keys())

    return {
        'overall_score': overall_score,
        'component_scores': scores,
        'spatial_relationship': spatial_rel['relationship'],
        'dimensional_accuracy': dim_accuracy,
        'intersection_metrics': intersection
    }
```

### Matching Strategy Classes

#### **BaseMatcher**
```python
class BaseMatcher:
    """
    Base class for geometry matching strategies.
    Provides common matching infrastructure.
    """

    def __init__(self, criteria_weights=None):
        self.criteria_weights = criteria_weights or {
            'shape': 0.2,
            'dimensions': 0.4,
            'spatial': 0.2,
            'intersection': 0.2
        }

    def find_best_match(self, target_element, candidate_elements):
        """
        Find best matching element using configured criteria.

        Args:
            target_element: Element to match
            candidate_elements: List of candidate elements

        Returns:
            tuple: (best_match, score, analysis_details)
        """
        best_match = None
        best_score = 0.0
        best_analysis = {}

        for candidate in candidate_elements:
            analysis = self.calculate_match_score(target_element, candidate)

            if analysis['overall_score'] > best_score:
                best_score = analysis['overall_score']
                best_match = candidate
                best_analysis = analysis

        return best_match, best_score, best_analysis

    def calculate_match_score(self, element1, element2):
        """
        Calculate comprehensive match score.
        Override in subclasses for element-specific logic.
        """
        return calculate_geometric_similarity_score(element1, element2)
```

#### **ColumnMatcher**
```python
class ColumnMatcher(BaseMatcher):
    """
    Specialized matcher for structural columns.
    Emphasizes dimensional accuracy and intersection volume.
    """

    def __init__(self):
        super().__init__(criteria_weights={
            'shape': 0.1,      # Less important for columns
            'dimensions': 0.6, # Critical for columns
            'spatial': 0.1,    # Less important
            'intersection': 0.2 # Important for validation
        })

    def calculate_match_score(self, column1, column2):
        """
        Column-specific matching with enhanced dimensional checking.
        """
        base_score = super().calculate_match_score(column1, column2)

        # Additional column-specific checks
        column_specific = self.check_column_specific_criteria(column1, column2)

        # Adjust score based on column-specific factors
        adjusted_score = base_score['overall_score'] * column_specific['multiplier']

        base_score['overall_score'] = adjusted_score
        base_score['column_specific'] = column_specific

        return base_score

    def check_column_specific_criteria(self, column1, column2):
        """
        Check column-specific matching criteria.
        """
        criteria = {}

        # Check if both are same column type (circular, square, rectangular)
        type1 = detect_column_type(column1)
        type2 = detect_column_type(column2)
        criteria['same_type'] = type1 == type2

        # Calculate type compatibility multiplier
        if criteria['same_type']:
            criteria['multiplier'] = 1.0
        else:
            criteria['multiplier'] = 0.3  # Significant penalty for type mismatch

        return criteria
```

#### **WallMatcher**
```python
class WallMatcher(BaseMatcher):
    """
    Specialized matcher for architectural walls.
    Emphasizes spatial alignment and layer compatibility.
    """

    def __init__(self):
        super().__init__(criteria_weights={
            'shape': 0.3,      # Important for wall profiles
            'dimensions': 0.3, # Important for wall thickness
            'spatial': 0.3,    # Critical for wall alignment
            'intersection': 0.1 # Less important for walls
        })

    def calculate_match_score(self, wall1, wall2):
        """
        Wall-specific matching with orientation and function checking.
        """
        base_score = super().calculate_match_score(wall1, wall2)

        # Additional wall-specific checks
        wall_specific = self.check_wall_specific_criteria(wall1, wall2)

        adjusted_score = base_score['overall_score'] * wall_specific['multiplier']
        base_score['overall_score'] = adjusted_score
        base_score['wall_specific'] = wall_specific

        return base_score

    def check_wall_specific_criteria(self, wall1, wall2):
        """
        Check wall-specific criteria like orientation and function.
        """
        criteria = {}

        # Check wall orientation alignment
        orientation1 = get_wall_orientation(wall1)
        orientation2 = get_wall_orientation(wall2)
        criteria['orientation_match'] = orientation1 == orientation2

        # Check wall function (exterior, interior, etc.)
        function1 = get_wall_function(wall1)
        function2 = get_wall_function(wall2)
        criteria['function_match'] = function1 == function2

        # Calculate compatibility multiplier
        multiplier = 1.0
        if not criteria['orientation_match']:
            multiplier *= 0.5
        if not criteria['function_match']:
            multiplier *= 0.7

        criteria['multiplier'] = multiplier
        return criteria
```

### Usage Examples

#### **Basic Geometry Matching**
```python
from logic_library.active.utilities.geometry.precise_matching import ColumnMatcher

# Create matcher
matcher = ColumnMatcher()

# Find best match for a column
host_column = get_selected_column()
linked_columns = get_linked_columns()

best_match, score, analysis = matcher.find_best_match(host_column, linked_columns)

if best_match:
    print(f"Best match found: Column {best_match.Id}")
    print(f"Match score: {score:.3f}")
    print(f"Dimensional accuracy: {analysis['dimensional_accuracy']['accuracy']:.1%}")
else:
    print("No suitable match found")
```

#### **Advanced Matching with Custom Criteria**
```python
# Custom matcher with specific requirements
class StrictColumnMatcher(ColumnMatcher):
    def __init__(self, min_accuracy=0.99):
        super().__init__()
        self.min_accuracy = min_accuracy

    def find_best_match(self, target, candidates):
        best_match, score, analysis = super().find_best_match(target, candidates)

        # Apply strict accuracy requirement
        if analysis['dimensional_accuracy']['accuracy'] < self.min_accuracy:
            return None, 0.0, analysis

        return best_match, score, analysis

# Usage
strict_matcher = StrictColumnMatcher(min_accuracy=0.99)  # Require 99% accuracy
match = strict_matcher.find_best_match(host_column, linked_columns)
```

#### **Batch Matching**
```python
def match_multiple_elements(host_elements, linked_elements_dict, matcher_class=ColumnMatcher):
    """
    Match multiple elements efficiently.
    """
    matcher = matcher_class()
    results = {}

    for host_elem in host_elements:
        best_match, score, analysis = matcher.find_best_match(host_elem, linked_elements_dict.values())
        results[host_elem.Id] = {
            'match': best_match,
            'score': score,
            'analysis': analysis
        }

    return results

# Usage
host_columns = get_all_host_columns()
linked_columns_dict = get_linked_columns_dict()

matching_results = match_multiple_elements(host_columns, linked_columns_dict, ColumnMatcher)
```

### Configuration and Thresholds

#### **Matching Thresholds**
```python
DEFAULT_THRESHOLDS = {
    'min_intersection_volume_cu_ft': 0.1,    # Minimum intersection volume
    'min_dimensional_accuracy': 0.95,       # 95% dimensional accuracy required
    'min_shape_similarity': 0.8,            # 80% shape similarity required
    'min_spatial_alignment': 0.7,           # 70% spatial alignment required
    'max_position_tolerance_ft': 1.0        # 1 foot position tolerance
}

class ConfigurableMatcher(BaseMatcher):
    """
    Matcher with configurable thresholds for different precision requirements.
    """

    def __init__(self, thresholds=None):
        super().__init__()
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def meets_thresholds(self, analysis):
        """
        Check if match meets configured thresholds.
        """
        return (
            analysis['intersection_metrics'].get('intersection_volume_cu_ft', 0) >= self.thresholds['min_intersection_volume_cu_ft'] and
            analysis['dimensional_accuracy']['accuracy'] >= self.thresholds['min_dimensional_accuracy'] and
            analysis['component_scores']['shape'] >= self.thresholds['min_shape_similarity'] and
            analysis['component_scores']['spatial'] >= self.thresholds['min_spatial_alignment']
        )
```

### Performance Optimizations

#### **Geometry Caching**
```python
class CachedGeometryMatcher(BaseMatcher):
    """
    Matcher with geometry caching for improved performance.
    """

    def __init__(self):
        super().__init__()
        self.geometry_cache = {}

    def get_cached_geometry(self, element):
        """
        Get geometry with caching to avoid repeated extraction.
        """
        elem_id = element.Id.IntegerValue

        if elem_id not in self.geometry_cache:
            self.geometry_cache[elem_id] = extract_solid_geometry(element)

        return self.geometry_cache[elem_id]
```

#### **Batch Processing**
```python
def batch_geometry_extraction(elements):
    """
    Extract geometry for multiple elements efficiently.
    """
    geometry_dict = {}

    for element in elements:
        try:
            geometry = extract_solid_geometry(element)
            if geometry:
                geometry_dict[element.Id] = {
                    'element': element,
                    'geometry': geometry,
                    'properties': extract_geometry_properties(geometry)
                }
        except Exception as e:
            print(f"Failed to extract geometry for element {element.Id}: {e}")

    return geometry_dict
```

### Integration with Logic Library

#### **File Structure**
```
logic-library/active/utilities/geometry/
├── LOG-UTIL-GEOM-001-v1-precise-geometry-matching.md    # This documentation
├── precise_matching.py                                  # Implementation
└── matchers/
    ├── column_matcher.py
    ├── wall_matcher.py
    ├── beam_matcher.py
    └── foundation_matcher.py
```

#### **Import Pattern**
```python
from logic_library.active.utilities.geometry.precise_matching import (
    BaseMatcher, ColumnMatcher, WallMatcher, calculate_geometric_similarity_score
)
from logic_library.active.utilities.geometry.matchers.column_matcher import StrictColumnMatcher
```

### Benefits

#### **Precision and Accuracy**
- Multiple matching criteria for robust element identification
- Configurable thresholds for different precision requirements
- Detailed analysis for troubleshooting mismatches

#### **Performance and Scalability**
- Geometry caching for repeated operations
- Batch processing capabilities
- Optimized intersection algorithms

#### **Flexibility and Extensibility**
- Base class for custom matching strategies
- Element-specific matchers for specialized requirements
- Configurable weights and thresholds

#### **Comprehensive Analysis**
- Detailed scoring breakdown
- Spatial relationship analysis
- Intersection volume metrics

### Changelog
**v1.0.0 (2025-10-22)**:
- Initial implementation of precise geometry matching
- Multi-criteria matching algorithms (shape, dimensions, spatial, intersection)
- Specialized matchers for columns and walls
- Configurable thresholds and performance optimizations
- Comprehensive documentation and usage examples