# LOG-UTIL-CONSOLE-001-v1: PyRevit Console Output Behavior

## Ringkasan
Modul ini mendokumentasikan perilaku output konsol pyRevit dan praktik terbaik untuk manajemen logging, berdasarkan pengalaman debugging Multi-Layer Area Reinforcement.

## Masalah yang Terjadi
**Error**: Output konsol duplikat dan pemisahan konsol yang tidak diinginkan
**Gejala**: Pesan sukses muncul berkali-kali, konsol terpisah untuk setiap pemanggilan
**Konsekuensi**: User experience buruk, sulit melacak progress operasi

## Akar Masalah
1. **Output setelah transaction commit**: pyRevit membuat konsol baru untuk setiap output
2. **Multiple logging points**: Berbagai fungsi melakukan output sendiri
3. **Timing yang salah**: Logging di titik yang tidak tepat dalam workflow
4. **Silent failures**: Beberapa operasi gagal tanpa logging yang memadai

## Solusi Praktis

### 1. Pola Output Timing yang Benar
```python
# ✅ BENAR: Collect results silently, print summary before commit
def process_multi_step_operation(doc, processor_input, logger=None):
    t = Transaction(doc, "Multi-Step Operation")
    t.Start()

    try:
        # STEP 1: Collect semua results secara silent
        all_results = []
        for step in steps:
            result = execute_step_silently(step, logger)
            all_results.append(result)

        # STEP 2: Print summary SEBELUM commit
        safe_logger_call(logger, 'info', "## 📊 **Ringkasan Operasi**")
        safe_logger_call(logger, 'info', f"Created {len(all_results)} elements")

        for i, result in enumerate(all_results, 1):
            safe_logger_call(logger, 'info', f"• Step {i}: {result.status}")

        safe_logger_call(logger, 'info', "\n💾 **Menyimpan perubahan...**")

        # STEP 3: Commit transaction
        t.Commit()

        # STEP 4: SILENT - Tidak ada output setelah commit
        return all_results

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        raise e
```

### 2. Fungsi Safe Logger dengan Fallback
```python
def safe_logger_call(logger, method_name, message, *args, **kwargs):
    """
    Safe logger method call dengan fallback untuk pyRevit compatibility
    """
    if logger:
        try:
            method = getattr(logger, method_name)
            return method(message, *args, **kwargs)
        except AttributeError:
            # Fallback ke print biasa untuk pyRevit logger
            print("[{}] {}".format(method_name.upper(), message))
    return None
```

### 3. Kategori Logging yang Konsisten
```python
# Standard logging levels untuk pyRevit
LOG_LEVELS = {
    'debug': 'debug',      # Detail teknis untuk debugging
    'info': 'info',        # Informasi progress normal
    'warning': 'warning',  # Peringatan yang tidak critical
    'error': 'error',      # Error yang perlu perhatian
    'critical': 'error'    # Error critical (pakai error level pyRevit)
}

def log_with_level(logger, level, message):
    """Log dengan level yang konsisten"""
    safe_logger_call(logger, LOG_LEVELS.get(level, 'info'), message)
```

## Best Practices

### 1. Timing Output Rules
- **Collect results first**: Lakukan semua operasi secara silent
- **Print summary before commit**: Output detail sebelum transaction commit
- **Silent after commit**: Hindari output setelah commit untuk mencegah konsol baru
- **Exception logging**: Selalu log exception dengan detail

### 2. Message Format Standards
```python
# Konsisten message formatting
MESSAGE_FORMATS = {
    'start': "## 🔧 **Memulai: {}**",
    'progress': "• {}: {}",
    'success': "## ✅ **Berhasil: {}**",
    'error': "## ❌ **Error: {}**",
    'warning': "## ⚠️ **Peringatan: {}**",
    'saving': "\n💾 **Menyimpan perubahan...**"
}

def format_message(type_key, *args):
    """Format message dengan konsisten"""
    template = MESSAGE_FORMATS.get(type_key, "{}")
    return template.format(*args)
```

### 3. Progress Indication
```python
def show_progress_with_summary(logger, operation_name, steps):
    """
    Show progress dengan summary di akhir
    """
    safe_logger_call(logger, 'info', format_message('start', operation_name))

    results = []
    for i, step in enumerate(steps, 1):
        safe_logger_call(logger, 'info', f"• Step {i}/{len(steps)}: {step.name}")

        result = execute_step(step)
        results.append(result)

        if result.success:
            safe_logger_call(logger, 'info', f"  ✓ {result.message}")
        else:
            safe_logger_call(logger, 'warning', f"  ⚠️ {result.message}")

    # Summary sebelum commit
    successful_steps = [r for r in results if r.success]
    safe_logger_call(logger, 'info', f"\n📊 **Summary: {len(successful_steps)}/{len(steps)} steps successful**")

    return results
```

## Troubleshooting

### Konsol Terpisah untuk Setiap Output
**Penyebab**: Output dilakukan setelah transaction commit
**Solusi**: Pindahkan semua output sebelum commit

### Duplikasi Pesan
**Penyebab**: Multiple functions melakukan output untuk operasi yang sama
**Solusi**: Centralized logging di satu tempat saja

### Silent Failures
**Penyebab**: Exception tidak di-log dengan baik
**Solusi**: Selalu gunakan try-except dengan logging detail

## Contoh Implementasi Lengkap

### Multi-Layer Area Reinforcement dengan Output Management
```python
def process_multi_layer_area_reinforcement(doc, processor_input, logger=None):
    """
    Contoh lengkap dengan output management yang benar
    """
    # DEBUG: Log input (silent untuk user)
    safe_logger_call(logger, 'debug', "=== DEBUG: process_multi_layer_area_reinforcement called ===")

    major_direction = processor_input.get("major_direction", "Y")
    ui_settings = processor_input.get("ui_settings", [])

    # SINGLE TRANSACTION
    t = Transaction(doc, "Create Multi-Layer Area Reinforcement")
    t.Start()

    try:
        created_elements = []

        # Process layers SILENTLY
        for layer_group in separate_layers(ui_settings):
            area_reinf = create_area_reinforcement_safe(
                doc, processor_input["boundary_curves"],
                processor_input["host"], direction_vector, logger
            )
            if area_reinf:
                created_elements.append(area_reinf)

        # Override parameters SILENTLY
        for element in created_elements:
            layer_overrides = calculate_layer_overrides(doc, element, ui_settings)
            override_area_reinforcement_parameters(element, layer_overrides, logger)

        # PRINT SUMMARY BEFORE COMMIT
        safe_logger_call(logger, 'info', "## ⚙️ **Memproses Multi Layer Settings...**")
        safe_logger_call(logger, 'info', "\n## 📊 **Ringkasan Multi-Layer**")
        safe_logger_call(logger, 'info', "---")
        safe_logger_call(logger, 'info', f"Created **{len(created_elements)}** Area Reinforcement elements")

        for i, element in enumerate(created_elements, 1):
            layer_info = get_layer_info_from_element(element)
            safe_logger_call(logger, 'info', f"• AR {i}: ID {element.Id} - Layers: {layer_info}")

        safe_logger_call(logger, 'info', "\n💾 **Menyimpan perubahan...**")

        # COMMIT
        t.Commit()

        # SILENT: No post-commit output
        return created_elements

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        safe_logger_call(logger, 'error', f"❌ Multi-layer creation failed: {str(e)}")
        return []
```

## Kesimpulan
Manajemen output konsol yang benar sangat kritikal untuk user experience yang baik. Dengan mengikuti pola "collect silently, print summary before commit, silent after commit", kita dapat menghindari konsol terpisah dan duplikasi pesan.

**Prinsip Utama**: Semua output detail harus dilakukan sebelum transaction commit, setelah commit harus silent untuk menghindari konsol baru.