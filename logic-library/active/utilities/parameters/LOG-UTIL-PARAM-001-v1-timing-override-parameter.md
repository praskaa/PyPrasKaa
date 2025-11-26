# LOG-UTIL-PARAM-001-v1: Timing Override Parameter

## Ringkasan
Modul ini mendokumentasikan praktik terbaik untuk timing override parameter di Revit API, khususnya untuk Area Reinforcement dan elemen struktur lainnya.

## Masalah yang Terjadi
**Error**: Parameter override gagal secara silent selama pembuatan elemen
**Gejala**: Elemen berhasil dibuat tetapi parameter tidak berubah sesuai setting
**Konsekuensi**: Fungsi tidak bekerja sesuai ekspektasi user

## Akar Masalah
1. **Timing yang Salah**: Override dilakukan sebelum elemen ada
2. **Transaction Scope**: Override di luar transaksi yang tepat
3. **Parameter ReadOnly**: Mencoba override parameter yang tidak bisa diubah
4. **Type vs Instance**: Override di tempat yang salah (type vs instance)

## Solusi Praktis

### 1. Pola Timing yang Benar
```python
# ✅ BENAR: Sequence yang tepat
def process_with_parameter_override(doc, processor_input, logger=None):
    t = Transaction(doc, "Create and Configure Element")
    t.Start()

    try:
        # STEP 1: Buat elemen terlebih dahulu
        element = create_element_safe(doc, processor_input, logger)
        if not element:
            raise ValueError("Failed to create element")

        # STEP 2: Override parameter di dalam transaksi yang sama
        override_results = override_element_parameters(element, processor_input, logger)

        # STEP 3: Logging detail sebelum commit
        log_override_results(override_results, logger)

        # STEP 4: Commit semua operasi sekaligus
        t.Commit()

        return element

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        raise e
```

### 2. Fungsi Override Parameter yang Robust
```python
def override_area_reinforcement_parameters(area_reinforcement, parameter_overrides=None, logger=None):
    """
    Override parameter dengan validasi dan error handling yang komprehensif
    """
    if not area_reinforcement:
        return {'success': False, 'message': 'Invalid element', 'overrides': []}

    # Default overrides
    default_overrides = {
        'Layout Rule': 3,  # Maximum Spacing
    }

    # Merge dengan provided overrides
    overrides = default_overrides.copy()
    if parameter_overrides:
        overrides.update(parameter_overrides)

    results = {
        'success': True,
        'message': 'Parameter override completed',
        'overrides': []
    }

    try:
        # Override setiap parameter
        for param_name, value in overrides.items():
            success = apply_single_parameter_override(
                area_reinforcement, param_name, value, logger
            )
            results['overrides'].append({
                'parameter': param_name,
                'value': value,
                'success': success
            })

            if not success:
                results['success'] = False
                results['message'] = 'Some parameter overrides failed'

    except Exception as e:
        results['success'] = False
        results['message'] = f'Error during parameter override: {str(e)}'

    return results
```

### 3. Single Parameter Override dengan Fallback
```python
def apply_single_parameter_override(element, param_name, value, logger=None):
    """
    Override single parameter dengan multiple fallback strategies
    """
    try:
        # STRATEGY 1: Override pada instance element
        success = set_parameter_value_safe(element, param_name, value)
        if success:
            safe_logger_call(logger, 'debug', f"✓ Instance override: {param_name} = {value}")
            return True

        # STRATEGY 2: Override pada element type
        element_type_id = element.GetTypeId()
        element_type = element.Document.GetElement(element_type_id)

        success = set_parameter_value_safe(element_type, param_name, value)
        if success:
            safe_logger_call(logger, 'debug', f"✓ Type override: {param_name} = {value}")
            return True

        # STRATEGY 3: Override dengan parameter ID (jika tersedia)
        param_id = get_parameter_id_by_name(param_name)
        if param_id:
            success = set_parameter_by_id_safe(element, param_id, value)
            if success:
                safe_logger_call(logger, 'debug', f"✓ ID override: {param_name} = {value}")
                return True

        safe_logger_call(logger, 'warning', f"⚠️ Failed to override: {param_name}")
        return False

    except Exception as e:
        safe_logger_call(logger, 'error', f"❌ Exception in override: {param_name} - {str(e)}")
        return False
```

## Parameter Override Strategies

### 1. Area Reinforcement Parameters
```python
# Parameter yang umum digunakan untuk Area Reinforcement
AREA_REINFORCEMENT_PARAMETERS = {
    # Layout settings
    'Layout Rule': 3,  # 0=Min Spacing, 1=Fixed, 2=Spacing+Number, 3=Max Spacing

    # Direction settings (0=disabled, 1=enabled)
    'Bottom/Interior Major Direction': 1,
    'Bottom/Interior Minor Direction': 0,
    'Top/Exterior Major Direction': 1,
    'Top/Exterior Minor Direction': 0,

    # Bar type settings (ElementId)
    'Bottom/Interior Major Bar Type': bar_type_id,
    'Bottom/Interior Minor Bar Type': bar_type_id,
    'Top/Exterior Major Bar Type': bar_type_id,
    'Top/Exterior Minor Bar Type': bar_type_id,

    # Spacing settings (dalam unit Revit - biasanya mm)
    'Bottom Major Spacing': 150.0,
    'Bottom Minor Spacing': 200.0,
    'Top Major Spacing': 150.0,
    'Top Minor Spacing': 200.0,

    # Cover offset settings
    'Additional Bottom Cover Offset': 0.0,
    'Additional Top Cover Offset': 0.0,
}
```

### 2. Unit Conversion Handling
```python
def convert_parameter_value(param_name, value, logger=None):
    """
    Konversi nilai parameter berdasarkan tipe dan unit
    """
    # Layout Rule - harus integer
    if param_name == "Layout Rule":
        return int(value)

    # Spacing parameters - UI sudah dalam mm, gunakan langsung
    elif "Spacing" in param_name:
        return float(value)  # Sudah dalam unit yang benar

    # Cover offset - konversi mm ke feet jika diperlukan
    elif "Cover Offset" in param_name:
        return value / 304.8  # mm to feet

    # ElementId parameters
    elif "Bar Type" in param_name:
        return value  # Sudah ElementId

    # Default: return as-is
    return value
```

## Best Practices

### 1. Parameter Validation
```python
def validate_parameter_override(element, param_name, value):
    """
    Validasi parameter sebelum override
    """
    try:
        param = element.LookupParameter(param_name)
        if not param:
            return False, f"Parameter '{param_name}' not found"

        if param.IsReadOnly:
            return False, f"Parameter '{param_name}' is read-only"

        # Validate value type
        if param.StorageType == StorageType.String and not isinstance(value, str):
            return False, f"Parameter '{param_name}' expects string value"

        if param.StorageType == StorageType.Double and not isinstance(value, (int, float)):
            return False, f"Parameter '{param_name}' expects numeric value"

        return True, "Valid"

    except Exception as e:
        return False, str(e)
```

### 2. Batch Override dengan Rollback
```python
def override_parameters_batch(element, parameter_dict, logger=None):
    """
    Override multiple parameters dengan rollback jika gagal
    """
    applied_changes = []

    try:
        for param_name, value in parameter_dict.items():
            # Validate sebelum apply
            is_valid, error_msg = validate_parameter_override(element, param_name, value)
            if not is_valid:
                raise ValueError(f"Validation failed for {param_name}: {error_msg}")

            # Apply parameter
            success = apply_single_parameter_override(element, param_name, value, logger)
            if not success:
                raise ValueError(f"Failed to override {param_name}")

            applied_changes.append((param_name, value))

    except Exception as e:
        # Rollback applied changes
        safe_logger_call(logger, 'warning', f"Rolling back {len(applied_changes)} parameter changes")
        # Note: Revit tidak punya undo mechanism, jadi ini hanya logging

        raise e

    return applied_changes
```

## Troubleshooting

### Parameter Override Gagal
**Penyebab**: Parameter read-only atau timing salah
**Solusi**:
1. Cek `param.IsReadOnly` sebelum override
2. Pastikan override dilakukan setelah element creation
3. Coba override pada element type jika instance gagal

### Nilai Parameter Tidak Berubah
**Penyebab**: Unit conversion salah atau parameter binding
**Solusi**:
1. Verifikasi unit yang diharapkan Revit
2. Cek parameter binding di family/template
3. Gunakan parameter ID jika name lookup gagal

### Exception Selama Override
**Penyebab**: Value type mismatch atau element state invalid
**Solusi**:
1. Validate value type sebelum override
2. Pastikan element masih valid (belum dihapus)
3. Check transaction state

## Contoh Implementasi Lengkap

### Multi-Layer Area Reinforcement dengan Override
```python
def process_layer_group_to_overrides(doc, layer_group, logger=None):
    """
    Convert layer group menjadi parameter overrides
    """
    overrides = {
        "Layout Rule": 3,  # Maximum Spacing
        # Default: semua disabled
        "Bottom/Interior Minor Direction": 0,
        "Bottom/Interior Major Direction": 0,
        "Top/Exterior Minor Direction": 0,
        "Top/Exterior Major Direction": 0
    }

    # Process setiap layer
    for layer_config in layer_group:
        layer_id = layer_config.get("layer_id")

        # Enable visibility
        visibility_param = get_visibility_parameter_name(layer_id)
        overrides[visibility_param] = 1

        # Set bar type
        bar_type_name = layer_config.get("bar_type_name")
        if bar_type_name:
            bar_type_id = find_rebar_bar_type_by_name(doc, bar_type_name)
            if bar_type_id:
                bar_type_param = get_bar_type_parameter_name(layer_id)
                overrides[bar_type_param] = bar_type_id

        # Set spacing (UI sudah dalam mm)
        spacing_mm = layer_config.get("spacing")
        if spacing_mm:
            spacing_param = get_short_spacing_parameter_name(layer_id)
            overrides[spacing_param] = spacing_mm

    return overrides
```

## Kesimpulan
Timing override parameter yang benar sangat kritikal untuk fungsi yang andal. Dengan mengikuti pola "create first, override second, commit last" dan menggunakan validasi yang ketat, kita dapat memastikan parameter override bekerja konsisten.

**Prinsip Utama**: Override parameter harus dilakukan setelah element creation, di dalam transaction yang sama, dengan validasi menyeluruh.