# LOG-UTIL-TRANSACTION-001-v1: Transaction Management

## Ringkasan
Modul ini mendokumentasikan praktik terbaik manajemen transaksi di Revit API, berdasarkan pengalaman debugging Multi-Layer Area Reinforcement.

## Masalah yang Terjadi
**Error**: "Transaction already started" dan konflik transaksi bersarang
**Gejala**: Fungsi pembuatan elemen gagal dengan error transaksi yang tidak terduga
**Konsekuensi**: Operasi multi-langkah menjadi tidak dapat diprediksi

## Akar Masalah
1. **Transaksi Bersarang**: Beberapa fungsi mencoba mengelola transaksi sendiri
2. **Scope Transaksi yang Tidak Jelas**: Sulit melacak di mana transaksi dimulai/berakhir
3. **Kegagalan Silent**: Transaksi gagal tanpa logging yang memadai
4. **Timing yang Salah**: Operasi dilakukan di luar scope transaksi yang tepat

## Solusi Praktis

### 1. Pola Single Transaction Scope
```python
# ✅ BENAR: Single transaction untuk semua operasi
def process_multi_layer_area_reinforcement(doc, processor_input, logger=None):
    # SINGLE TRANSACTION untuk semua operasi
    t = Transaction(doc, "Create Multi-Layer Area Reinforcement")
    t.Start()

    try:
        # 1. Buat elemen-elemen terlebih dahulu
        all_results = []
        for group in layer_groups:
            area_reinf = create_area_reinforcement_safe(doc, curves, host, logger)
            all_results.append(area_reinf)

        # 2. Override parameter di dalam transaksi yang sama
        for result in all_results:
            override_area_reinforcement_parameters(result, overrides, logger)

        # 3. Logging detail SEBELUM commit
        safe_logger_call(logger, 'info', "## 📊 Ringkasan Pemrosesan")
        safe_logger_call(logger, 'info', f"Created {len(all_results)} elements")

        # 4. COMMIT semua operasi sekaligus
        t.Commit()

        return all_results

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        raise e
```

### 2. Fungsi Transaction-Agnostic
```python
# ✅ BENAR: Fungsi tidak mengelola transaksi sendiri
def create_area_reinforcement_safe(doc, boundary_curves, host_element, logger=None):
    """Fungsi ini MENGASUMSI transaksi sudah dimulai di tempat lain"""

    # Input validation
    if not doc or not boundary_curves or not host_element:
        safe_logger_call(logger, 'error', "❌ Input validation failed")
        return None

    # Prepare data
    curve_list = prepare_curves(boundary_curves)
    art = get_default_area_reinforcement_type(doc)

    # DIRECT API CALL - no transaction management
    area_reinf = AreaReinforcement.Create(
        doc, host_element, curve_list, direction, art.Id, rbt_id, hook_id
    )

    return area_reinf
```

### 3. Error Handling dengan Transaction Rollback
```python
def safe_transaction_operation(doc, operation_name, operation_func, logger=None):
    """Wrapper untuk operasi dengan transaksi yang aman"""
    t = Transaction(doc, operation_name)

    try:
        t.Start()
        safe_logger_call(logger, 'info', f"🔧 Starting transaction: {operation_name}")

        result = operation_func()

        t.Commit()
        safe_logger_call(logger, 'info', f"✅ Transaction committed: {operation_name}")

        return result

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
            safe_logger_call(logger, 'error', f"❌ Transaction rolled back: {operation_name}")

        safe_logger_call(logger, 'error', f"❌ Operation failed: {str(e)}")
        return None
```

## Best Practices

### 1. Transaction Scope Rules
- **Satu transaksi per operasi logis lengkap**
- **Jangan bersarang transaksi**
- **Commit segera setelah semua operasi selesai**
- **Rollback pada exception**

### 2. Function Design Patterns
```python
# Pattern 1: Main process handles transaction
def main_process():
    t = Transaction(doc)
    t.Start()
    try:
        step1()  # Transaction-agnostic
        step2()  # Transaction-agnostic
        t.Commit()
    except:
        t.RollBack()

# Pattern 2: Wrapper function
def with_transaction(doc, operation_name, func):
    t = Transaction(doc, operation_name)
    t.Start()
    try:
        result = func()
        t.Commit()
        return result
    except:
        t.RollBack()
        return None
```

### 3. Logging Strategy
- **Log sebelum commit**: Detail operasi
- **Silent setelah commit**: Hindari duplikasi output
- **Log rollback**: Debugging kegagalan
- **Exception details**: Untuk troubleshooting

## Contoh Implementasi Lengkap

### Multi-Step Operation dengan Single Transaction
```python
def create_multi_layer_reinforcement(doc, processor_input, logger=None):
    """
    Contoh implementasi lengkap dengan manajemen transaksi yang benar
    """
    major_direction = processor_input.get("major_direction", "X")
    ui_settings = processor_input.get("ui_settings", [])

    # Convert direction
    direction_vector = XYZ(1, 0, 0) if major_direction == "X" else XYZ(0, 1, 0)

    # SINGLE TRANSACTION SCOPE
    t = Transaction(doc, "Create Multi-Layer Area Reinforcement")
    t.Start()

    try:
        created_elements = []

        # Step 1: Create elements (transaction-agnostic)
        for layer_group in separate_layers(ui_settings):
            area_reinf = create_area_reinforcement_safe(
                doc, processor_input["boundary_curves"],
                processor_input["host"], direction_vector, logger
            )
            if area_reinf:
                created_elements.append(area_reinf)

        # Step 2: Override parameters (still in transaction)
        for element in created_elements:
            layer_overrides = calculate_layer_overrides(element, ui_settings)
            override_area_reinforcement_parameters(element, layer_overrides, logger)

        # Step 3: Pre-commit logging
        safe_logger_call(logger, 'info', f"## ✅ Created {len(created_elements)} elements")

        # Step 4: Single commit
        t.Commit()

        # SILENT: No post-commit logging to avoid console splitting

        return created_elements

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        safe_logger_call(logger, 'error', f"❌ Multi-layer creation failed: {str(e)}")
        return []
```

## Troubleshooting

### Error "Transaction already started"
**Penyebab**: Fungsi dipanggil di dalam transaksi yang sudah aktif
**Solusi**: Buat fungsi transaction-agnostic atau gunakan sub-transaction

### Error "Cannot modify document outside transaction"
**Penyebab**: Operasi modifikasi tanpa transaksi aktif
**Solusi**: Pastikan semua modifikasi di dalam scope transaksi

### Memory leaks dari uncommitted transactions
**Penyebab**: Exception mencegah rollback
**Solusi**: Selalu gunakan try-except dengan rollback di finally block

## Kesimpulan
Manajemen transaksi yang benar adalah fondasi untuk aplikasi Revit yang stabil. Dengan mengikuti pola single transaction scope dan fungsi transaction-agnostic, kita dapat menghindari konflik dan memastikan konsistensi data.

**Prinsip Utama**: Satu transaksi per operasi logis, fungsi pembantu tidak mengelola transaksi sendiri.