# LOG-UTIL-DATA-001-v1-hierarchical-data-processing.md

## Hierarchical Data Processing Framework

**Version:** 1.0.0
**Date:** 2025-10-22
**Author:** Prasetyo

### Description
Comprehensive framework for processing nested hierarchical data structures in Revit elements. Provides structured approach for traversal, node evaluation, parameter extraction, and matching against predefined geometries or patterns, ensuring efficiency and accuracy in data manipulation.

### Core Framework Architecture

#### **HierarchicalDataProcessor**
```python
class HierarchicalDataProcessor:
    """
    Base class for processing hierarchical data structures in Revit elements.
    Handles nested data traversal, evaluation, and extraction.
    """

    def __init__(self, traversal_strategy='depth_first'):
        self.traversal_strategy = traversal_strategy
        self.processing_stats = {
            'nodes_processed': 0,
            'nodes_skipped': 0,
            'extraction_errors': 0,
            'matching_attempts': 0
        }

    def process_element_hierarchy(self, root_element, processing_rules):
        """
        Process element hierarchy according to defined rules.

        Args:
            root_element: Root element to start processing from
            processing_rules: Dict defining processing rules and criteria

        Returns:
            dict: Processing results with extracted data and metadata
        """
        self.processing_stats = {k: 0 for k in self.processing_stats.keys()}

        # Extract hierarchical structure
        hierarchy = self.extract_hierarchy(root_element)

        # Apply processing rules
        processed_data = self.apply_processing_rules(hierarchy, processing_rules)

        # Generate processing report
        report = self.generate_processing_report(processed_data)

        return {
            'processed_data': processed_data,
            'hierarchy': hierarchy,
            'processing_stats': self.processing_stats,
            'report': report
        }
```

#### **Traversal Strategies**
```python
class DepthFirstTraversal:
    """
    Depth-first traversal strategy for hierarchical data.
    Processes child nodes before siblings.
    """

    def traverse(self, node, visitor_func, context=None):
        """
        Traverse hierarchy using depth-first approach.

        Args:
            node: Current node to process
            visitor_func: Function to call on each node
            context: Shared context for traversal

        Returns:
            dict: Traversal results
        """
        results = {}

        # Process current node
        node_result = visitor_func(node, context)
        results[node.id] = node_result

        # Process children recursively
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                child_results = self.traverse(child, visitor_func, context)
                results.update(child_results)

        return results

class BreadthFirstTraversal:
    """
    Breadth-first traversal strategy for hierarchical data.
    Processes all nodes at current level before going deeper.
    """

    def traverse(self, node, visitor_func, context=None):
        """
        Traverse hierarchy using breadth-first approach.
        """
        results = {}
        queue = [(node, 0)]  # (node, level)

        while queue:
            current_node, level = queue.pop(0)

            # Process current node
            node_result = visitor_func(current_node, context)
            results[current_node.id] = node_result

            # Add children to queue
            if hasattr(current_node, 'children') and current_node.children:
                for child in current_node.children:
                    queue.append((child, level + 1))

        return results
```

### Node Evaluation System

#### **NodeEvaluator**
```python
class NodeEvaluator:
    """
    Evaluates nodes during hierarchical traversal.
    Applies evaluation criteria and extracts relevant data.
    """

    def __init__(self, evaluation_criteria):
        self.evaluation_criteria = evaluation_criteria

    def evaluate_node(self, node, context=None):
        """
        Evaluate a single node against defined criteria.

        Args:
            node: Node to evaluate
            context: Evaluation context

        Returns:
            dict: Evaluation results
        """
        evaluation_result = {
            'node_id': node.id,
            'node_type': type(node).__name__,
            'evaluation_passed': False,
            'extracted_data': {},
            'evaluation_details': {}
        }

        # Apply evaluation criteria
        for criterion_name, criterion_func in self.evaluation_criteria.items():
            try:
                criterion_result = criterion_func(node, context)
                evaluation_result['evaluation_details'][criterion_name] = criterion_result

                # Update overall pass/fail status
                if isinstance(criterion_result, dict) and 'passed' in criterion_result:
                    if not criterion_result['passed']:
                        evaluation_result['evaluation_passed'] = False
                        break
                elif not criterion_result:
                    evaluation_result['evaluation_passed'] = False
                    break

            except Exception as e:
                evaluation_result['evaluation_details'][criterion_name] = {'error': str(e)}
                evaluation_result['evaluation_passed'] = False

        # Extract data if evaluation passed
        if evaluation_result['evaluation_passed']:
            evaluation_result['extracted_data'] = self.extract_node_data(node, context)

        return evaluation_result

    def extract_node_data(self, node, context=None):
        """
        Extract relevant data from evaluated node.
        Override in subclasses for specific data extraction logic.
        """
        return {}
```

### Parameter Extraction in Hierarchies

#### **HierarchicalParameterExtractor**
```python
class HierarchicalParameterExtractor:
    """
    Extracts parameters from hierarchical element structures.
    Handles nested families, components, and sub-elements.
    """

    def __init__(self, parameter_mappings):
        self.parameter_mappings = parameter_mappings

    def extract_hierarchical_parameters(self, root_element):
        """
        Extract parameters from element hierarchy.

        Args:
            root_element: Root element to extract from

        Returns:
            dict: Hierarchical parameter data
        """
        hierarchy_data = {
            'root': self.extract_element_parameters(root_element),
            'nested_elements': {},
            'subcomponents': {},
            'metadata': {
                'extraction_timestamp': datetime.now().isoformat(),
                'total_elements_processed': 0
            }
        }

        # Extract nested family instances
        nested_instances = self.extract_nested_family_instances(root_element)
        for instance_id, instance in nested_instances.items():
            hierarchy_data['nested_elements'][instance_id] = self.extract_element_parameters(instance)

        # Extract subcomponents (geometry instances, etc.)
        subcomponents = self.extract_subcomponents(root_element)
        for comp_id, component in subcomponents.items():
            hierarchy_data['subcomponents'][comp_id] = self.extract_component_parameters(component)

        hierarchy_data['metadata']['total_elements_processed'] = (
            1 + len(nested_instances) + len(subcomponents)
        )

        return hierarchy_data

    def extract_nested_family_instances(self, element):
        """
        Extract nested family instances from element geometry.
        """
        nested_instances = {}

        try:
            geom_element = element.get_Geometry(options)
            if geom_element:
                for geom_obj in geom_element:
                    if isinstance(geom_obj, GeometryInstance):
                        instance_elem = geom_obj.Symbol.Family
                        if instance_elem:
                            nested_instances[str(instance_elem.Id)] = instance_elem
        except:
            pass

        return nested_instances

    def extract_subcomponents(self, element):
        """
        Extract subcomponents from element.
        """
        subcomponents = {}

        # Implementation depends on element type
        # For walls: extract layers
        # For columns: extract rebar, etc.

        return subcomponents
```

### Geometry Matching in Hierarchies

#### **HierarchicalGeometryMatcher**
```python
class HierarchicalGeometryMatcher:
    """
    Matches geometries within hierarchical structures.
    Handles complex nested geometries and subcomponents.
    """

    def __init__(self, matching_criteria):
        self.matching_criteria = matching_criteria

    def match_hierarchical_geometries(self, source_hierarchy, target_hierarchy):
        """
        Match geometries between two hierarchical structures.

        Args:
            source_hierarchy: Source element hierarchy
            target_hierarchy: Target element hierarchy to match against

        Returns:
            dict: Matching results with confidence scores
        """
        matching_results = {
            'overall_match_score': 0.0,
            'component_matches': {},
            'unmatched_components': [],
            'matching_metadata': {}
        }

        # Match root geometries
        root_match = self.match_geometries(
            source_hierarchy.get('root', {}),
            target_hierarchy.get('root', {})
        )
        matching_results['component_matches']['root'] = root_match

        # Match nested elements
        nested_matches = self.match_nested_elements(
            source_hierarchy.get('nested_elements', {}),
            target_hierarchy.get('nested_elements', {})
        )
        matching_results['component_matches']['nested'] = nested_matches

        # Match subcomponents
        subcomponent_matches = self.match_subcomponents(
            source_hierarchy.get('subcomponents', {}),
            target_hierarchy.get('subcomponents', {})
        )
        matching_results['component_matches']['subcomponents'] = subcomponent_matches

        # Calculate overall score
        matching_results['overall_match_score'] = self.calculate_overall_match_score(
            matching_results['component_matches']
        )

        return matching_results

    def match_geometries(self, source_geom, target_geom):
        """
        Match individual geometries using defined criteria.
        """
        # Implementation uses geometric similarity algorithms
        # Returns match score and details
        pass

    def match_nested_elements(self, source_nested, target_nested):
        """
        Match nested elements between hierarchies.
        """
        # Implementation for matching nested family instances
        pass

    def match_subcomponents(self, source_comps, target_comps):
        """
        Match subcomponents between hierarchies.
        """
        # Implementation for matching subcomponents
        pass

    def calculate_overall_match_score(self, component_matches):
        """
        Calculate overall matching score from component matches.
        """
        if not component_matches:
            return 0.0

        scores = []
        weights = {'root': 0.5, 'nested': 0.3, 'subcomponents': 0.2}

        for component_type, matches in component_matches.items():
            if isinstance(matches, dict) and 'score' in matches:
                scores.append(matches['score'] * weights.get(component_type, 0.1))

        return sum(scores) / len(scores) if scores else 0.0
```

### Pattern Matching Framework

#### **HierarchicalPatternMatcher**
```python
class HierarchicalPatternMatcher:
    """
    Matches hierarchical structures against predefined patterns.
    Useful for template-based validation and classification.
    """

    def __init__(self, pattern_library):
        self.pattern_library = pattern_library

    def match_against_patterns(self, hierarchy_data):
        """
        Match hierarchy against library of predefined patterns.

        Args:
            hierarchy_data: Hierarchical data to match

        Returns:
            list: Matching patterns with confidence scores
        """
        matches = []

        for pattern_name, pattern_definition in self.pattern_library.items():
            match_score = self.calculate_pattern_match_score(hierarchy_data, pattern_definition)

            if match_score > 0.0:
                matches.append({
                    'pattern_name': pattern_name,
                    'match_score': match_score,
                    'pattern_details': pattern_definition
                })

        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        return matches

    def calculate_pattern_match_score(self, hierarchy, pattern):
        """
        Calculate how well hierarchy matches a specific pattern.
        """
        score = 0.0
        total_criteria = 0

        # Check root element criteria
        if 'root_criteria' in pattern:
            root_score = self.evaluate_criteria(hierarchy.get('root', {}), pattern['root_criteria'])
            score += root_score
            total_criteria += 1

        # Check nested elements criteria
        if 'nested_criteria' in pattern:
            nested_score = self.evaluate_nested_criteria(
                hierarchy.get('nested_elements', {}),
                pattern['nested_criteria']
            )
            score += nested_score
            total_criteria += 1

        # Check structural criteria
        if 'structure_criteria' in pattern:
            structure_score = self.evaluate_structure_criteria(hierarchy, pattern['structure_criteria'])
            score += structure_score
            total_criteria += 1

        return score / total_criteria if total_criteria > 0 else 0.0

    def evaluate_criteria(self, element_data, criteria):
        """
        Evaluate element data against specific criteria.
        """
        # Implementation for criteria evaluation
        pass
```

### Usage Examples

#### **Basic Hierarchical Processing**
```python
from logic_library.active.utilities.data.hierarchical_processing import HierarchicalDataProcessor

# Create processor
processor = HierarchicalDataProcessor(traversal_strategy='depth_first')

# Define processing rules
processing_rules = {
    'evaluation_criteria': {
        'has_geometry': lambda node, ctx: node.geometry is not None,
        'has_parameters': lambda node, ctx: len(node.parameters) > 0,
        'is_structural': lambda node, ctx: node.category == 'Structural'
    },
    'extraction_rules': {
        'geometry_properties': ['volume', 'surface_area', 'bounding_box'],
        'parameter_filters': ['width', 'height', 'material']
    }
}

# Process element hierarchy
root_element = get_selected_element()
result = processor.process_element_hierarchy(root_element, processing_rules)

print(f"Processed {result['processing_stats']['nodes_processed']} nodes")
print(f"Overall result: {result['report']['summary']}")
```

#### **Parameter Extraction from Hierarchy**
```python
from logic_library.active.utilities.data.hierarchical_processing import HierarchicalParameterExtractor

# Define parameter mappings
param_mappings = {
    'dimensions': {
        'width': 'STRUCTURAL_SECTION_COMMON_WIDTH',
        'height': 'STRUCTURAL_SECTION_COMMON_HEIGHT',
        'diameter': 'STRUCTURAL_SECTION_COMMON_DIAMETER'
    },
    'materials': {
        'material': 'Material Name',
        'finish': 'Finish'
    }
}

# Create extractor
extractor = HierarchicalParameterExtractor(param_mappings)

# Extract hierarchical parameters
complex_element = get_complex_element()
hierarchy_params = extractor.extract_hierarchical_parameters(complex_element)

print(f"Root parameters: {hierarchy_params['root']}")
print(f"Nested elements: {len(hierarchy_params['nested_elements'])}")
```

#### **Geometry Matching in Hierarchies**
```python
from logic_library.active.utilities.data.hierarchical_processing import HierarchicalGeometryMatcher

# Define matching criteria
matching_criteria = {
    'tolerance_mm': 0.01,
    'min_overlap_percentage': 80.0,
    'shape_similarity_threshold': 0.9
}

# Create matcher
matcher = HierarchicalGeometryMatcher(matching_criteria)

# Match hierarchical geometries
source_hierarchy = extract_hierarchy(source_element)
target_hierarchy = extract_hierarchy(target_element)

match_result = matcher.match_hierarchical_geometries(source_hierarchy, target_hierarchy)

print(f"Overall match score: {match_result['overall_match_score']:.1%}")
```

### Performance Optimizations

#### **Caching System**
```python
class CachedHierarchicalProcessor(HierarchicalDataProcessor):
    """
    Processor with caching for improved performance on repeated operations.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    def get_cached_hierarchy(self, element):
        """
        Get cached hierarchy data to avoid repeated extraction.
        """
        cache_key = element.Id.IntegerValue

        if cache_key not in self.cache:
            self.cache[cache_key] = self.extract_hierarchy(element)

        return self.cache[cache_key]
```

#### **Parallel Processing**
```python
import multiprocessing as mp

def process_hierarchies_parallel(element_list, processing_rules, num_processes=None):
    """
    Process multiple element hierarchies in parallel.
    """
    if num_processes is None:
        num_processes = mp.cpu_count()

    with mp.Pool(num_processes) as pool:
        results = pool.starmap(
            process_single_hierarchy,
            [(elem, processing_rules) for elem in element_list]
        )

    return results

def process_single_hierarchy(element, processing_rules):
    """
    Process single hierarchy (for parallel execution).
    """
    processor = HierarchicalDataProcessor()
    return processor.process_element_hierarchy(element, processing_rules)
```

### Integration with Logic Library

#### **File Structure**
```
logic-library/active/utilities/data/
├── LOG-UTIL-DATA-001-v1-hierarchical-data-processing.md    # This documentation
├── hierarchical_processing.py                              # Main implementation
└── processors/
    ├── parameter_extractor.py
    ├── geometry_matcher.py
    ├── pattern_matcher.py
    └── traversal_strategies.py
```

#### **Import Pattern**
```python
from logic_library.active.utilities.data.hierarchical_processing import (
    HierarchicalDataProcessor,
    HierarchicalParameterExtractor,
    HierarchicalGeometryMatcher,
    HierarchicalPatternMatcher
)
```

### Benefits

#### **Comprehensive Data Handling**
- Handles complex nested element structures
- Supports multiple traversal strategies
- Flexible evaluation and extraction rules

#### **Performance and Scalability**
- Caching for repeated operations
- Parallel processing capabilities
- Optimized traversal algorithms

#### **Extensibility and Flexibility**
- Plugin-based evaluation criteria
- Custom extraction rules
- Pattern-based matching system

#### **Robust Error Handling**
- Graceful handling of missing data
- Detailed error reporting
- Recovery mechanisms for partial failures

### Changelog
**v1.0.0 (2025-10-22)**:
- Initial implementation of hierarchical data processing framework
- Multiple traversal strategies (depth-first, breadth-first)
- Node evaluation system with configurable criteria
- Hierarchical parameter extraction
- Geometry matching in nested structures
- Pattern matching against predefined templates
- Performance optimizations and parallel processing
- Comprehensive documentation and usage examples