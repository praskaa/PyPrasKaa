# LOG-UTIL-IMPORT-001-v1: Library Dependencies Management

## Ringkasan
Modul ini mendokumentasikan praktik terbaik untuk manajemen dependensi library dan penanganan import failure, berdasarkan pengalaman debugging Multi-Layer Area Reinforcement.

## Masalah yang Terjadi
**Error**: Kegagalan import dan fungsi library yang hilang menyebabkan crash atau perilaku tidak terduga
**Gejala**: Aplikasi crash saat startup, fungsi tidak tersedia saat runtime
**Konsekuensi**: User experience buruk, debugging sulit

## Akar Masalah
1. **Asumsi ketersediaan library**: Kode mengasumsikan library selalu tersedia
2. **Import failure silent**: Kegagalan import tidak ditangani dengan baik
3. **Version incompatibility**: Library versi berbeda memiliki API berbeda
4. **Circular dependencies**: Import yang saling bergantung

## Solusi Praktis

### 1. Graceful Import dengan Fallback
```python
# ✅ BENAR: Import dengan fallback yang kuat
def safe_import_library():
    """
    Safe import dengan multiple fallback strategies
    """
    # STRATEGY 1: Try direct import
    try:
        from area_reinforcement import process_multi_layer_area_reinforcement
        return process_multi_layer_area_reinforcement
    except ImportError:
        pass

    # STRATEGY 2: Try alternative import path
    try:
        from lib.area_reinforcement import process_multi_layer_area_reinforcement
        return process_multi_layer_area_reinforcement
    except ImportError:
        pass

    # STRATEGY 3: Try relative import
    try:
        import sys
        import os
        current_dir = os.path.dirname(__file__)
        lib_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'lib')
        if lib_path not in sys.path:
            sys.path.insert(0, lib_path)

        from area_reinforcement import process_multi_layer_area_reinforcement
        return process_multi_layer_area_reinforcement
    except ImportError:
        pass

    # STRATEGY 4: Fallback implementation
    def fallback_multi_layer_area_reinforcement(doc, processor_input, logger=None):
        safe_logger_call(logger, 'warning', "⚠️ area_reinforcement library not available, using fallback")
        safe_logger_call(logger, 'warning', "Fallback: Basic single-layer area reinforcement only")

        # Implementasi fallback minimal
        return create_basic_area_reinforcement(doc, processor_input)

    return fallback_multi_layer_area_reinforcement
```

### 2. Conditional Import dengan Feature Detection
```python
# ✅ BENAR: Import bersyarat dengan feature detection
class LibraryManager:
    """Manajer library dengan feature detection"""

    def __init__(self):
        self.available_features = self._detect_available_features()

    def _detect_available_features(self):
        """Deteksi fitur yang tersedia"""
        features = {}

        # Test area reinforcement
        try:
            from area_reinforcement import process_multi_layer_area_reinforcement
            features['multi_layer_ar'] = True
        except ImportError:
            features['multi_layer_ar'] = False

        # Test rebar utilities
        try:
            from rebar_selection import select_rebar_bar_type
            features['rebar_selection'] = True
        except ImportError:
            features['rebar_selection'] = False

        # Test geometry utilities
        try:
            from geometry_utils import convert_view_to_model_coordinates
            features['geometry_utils'] = True
        except ImportError:
            features['geometry_utils'] = False

        return features

    def get_function(self, function_name, fallback=None):
        """Get function dengan fallback"""
        if function_name == 'process_multi_layer_area_reinforcement':
            if self.available_features.get('multi_layer_ar'):
                from area_reinforcement import process_multi_layer_area_reinforcement
                return process_multi_layer_area_reinforcement
            else:
                return fallback or self._fallback_multi_layer_ar

    def _fallback_multi_layer_ar(self, doc, processor_input, logger=None):
        """Fallback implementation untuk multi-layer AR"""
        safe_logger_call(logger, 'info', "Using fallback: Single layer area reinforcement")

        # Basic implementation
        return create_single_layer_area_reinforcement(doc, processor_input)
```

### 3. Version-Aware Import
```python
# ✅ BENAR: Import dengan penanganan versi
def import_with_version_check():
    """
    Import dengan pengecekan versi library
    """
    try:
        import area_reinforcement as ar_lib

        # Check version
        version = getattr(ar_lib, '__version__', '0.0.0')
        required_version = '1.0.0'

        if version < required_version:
            safe_logger_call(logger, 'warning',
                f"⚠️ area_reinforcement version {version} < required {required_version}")
            return None

        return ar_lib

    except ImportError:
        safe_logger_call(logger, 'error', "❌ area_reinforcement library not found")
        return None
    except AttributeError:
        safe_logger_call(logger, 'warning', "⚠️ area_reinforcement version info not available")
        return None
```

## Best Practices

### 1. Import Strategy Hierarchy
1. **Direct import**: `from library import function`
2. **Path manipulation**: Tambah path ke sys.path
3. **Relative import**: `from .library import function`
4. **Conditional import**: Import berdasarkan kondisi
5. **Fallback implementation**: Implementasi alternatif

### 2. Error Handling Patterns
```python
# Pattern 1: Try-Except dengan logging
try:
    from complex_library import complex_function
except ImportError as e:
    safe_logger_call(logger, 'warning', f"Library not available: {str(e)}")
    complex_function = lambda *args, **kwargs: None

# Pattern 2: Lazy import
def get_complex_function():
    if not hasattr(get_complex_function, '_cached'):
        try:
            from complex_library import complex_function
            get_complex_function._cached = complex_function
        except ImportError:
            get_complex_function._cached = lambda *args, **kwargs: None
    return get_complex_function._cached
```

### 3. Dependency Declaration
```python
# dependencies.py
LIBRARY_DEPENDENCIES = {
    'required': [
        'area_reinforcement',
        'rebar_selection',
        'geometry_utils'
    ],
    'optional': [
        'advanced_analysis',
        'reporting_tools'
    ],
    'versions': {
        'area_reinforcement': '>=1.0.0',
        'rebar_selection': '>=0.5.0'
    }
}

def check_dependencies(logger=None):
    """Check semua dependencies"""
    missing_required = []
    version_issues = []

    for lib in LIBRARY_DEPENDENCIES['required']:
        try:
            __import__(lib)
        except ImportError:
            missing_required.append(lib)

    # Version checks...
    for lib, version_spec in LIBRARY_DEPENDENCIES['versions'].items():
        # Version validation logic
        pass

    if missing_required:
        safe_logger_call(logger, 'error',
            f"❌ Missing required libraries: {', '.join(missing_required)}")
        return False

    return True
```

## Troubleshooting

### ImportError pada Startup
**Penyebab**: Library path tidak ada di sys.path
**Solusi**: Manipulasi sys.path sebelum import

### AttributeError pada Runtime
**Penyebab**: Function tidak ada di library yang di-import
**Solusi**: Feature detection dan fallback implementation

### Version Incompatibility
**Penyebab**: Library versi berbeda memiliki API berbeda
**Solusi**: Version checking dan conditional code

## Contoh Implementasi Lengkap

### Smart Import System
```python
class SmartImporter:
    """
    Smart import system dengan comprehensive fallback
    """

    def __init__(self, logger=None):
        self.logger = logger
        self._cache = {}

    def import_function(self, module_name, function_name, fallback=None):
        """
        Import function dengan intelligent fallback
        """
        cache_key = f"{module_name}.{function_name}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try different import strategies
        function = self._try_direct_import(module_name, function_name)
        if not function:
            function = self._try_path_manipulation(module_name, function_name)
        if not function:
            function = self._try_relative_import(module_name, function_name)
        if not function:
            function = fallback or self._create_stub_function(function_name)

        self._cache[cache_key] = function
        return function

    def _try_direct_import(self, module_name, function_name):
        """Try direct import"""
        try:
            module = __import__(module_name)
            return getattr(module, function_name, None)
        except (ImportError, AttributeError):
            return None

    def _try_path_manipulation(self, module_name, function_name):
        """Try with path manipulation"""
        try:
            import sys
            import os

            # Add common library paths
            current_file = os.path.abspath(__file__)
            extension_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            lib_path = os.path.join(extension_root, 'lib')

            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)

            module = __import__(module_name)
            return getattr(module, function_name, None)
        except (ImportError, AttributeError, OSError):
            return None

    def _try_relative_import(self, module_name, function_name):
        """Try relative import"""
        try:
            import importlib
            module = importlib.import_module(f'.{module_name}', package=__package__)
            return getattr(module, function_name, None)
        except (ImportError, AttributeError):
            return None

    def _create_stub_function(self, function_name):
        """Create stub function untuk missing imports"""
        def stub_function(*args, **kwargs):
            safe_logger_call(self.logger, 'warning',
                f"⚠️ Function '{function_name}' not available (using stub)")
            return None
        return stub_function

# Usage
importer = SmartImporter(logger=output)
process_multi_layer = importer.import_function(
    'area_reinforcement',
    'process_multi_layer_area_reinforcement',
    fallback=lambda doc, input, logger=None: safe_logger_call(logger, 'info', "Fallback: Basic AR")
)
```

## Kesimpulan
Manajemen dependensi library yang baik sangat penting untuk aplikasi yang robust. Dengan menggunakan graceful import, feature detection, dan fallback implementation, kita dapat memastikan aplikasi tetap berfungsi bahkan ketika beberapa library tidak tersedia.

**Prinsip Utama**: Selalu asumsikan library bisa tidak tersedia, berikan fallback yang berguna, dan informasikan user tentang limitations.