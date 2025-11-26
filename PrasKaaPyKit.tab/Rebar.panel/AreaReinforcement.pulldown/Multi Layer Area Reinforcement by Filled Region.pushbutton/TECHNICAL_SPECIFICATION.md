# Spesifikasi Teknis: Multi-Layer Area Reinforcement

## 1. Pendahuluan

Dokumen ini merinci arsitektur teknis, alur data, dan implementasi dari skrip "Multi-Layer Area Reinforcement". Tujuannya adalah untuk memberikan panduan yang jelas bagi developer dalam memahami, memelihara, dan mengembangkan fungsionalitas skrip ini.

Skrip ini mengadopsi pendekatan **Model-View-ViewModel (MVVM)** secara parsial untuk memisahkan antara tampilan (UI) dan logika aplikasi, serta dirancang untuk berintegrasi penuh dengan **PrasKaaPykit Logic Library**.

## 2. Arsitektur MVVM (Model-View-ViewModel)

Arsitektur skrip ini dapat dipecah menjadi tiga komponen utama:

1.  **Model**: Merepresentasikan data inti aplikasi.
    *   **`LayerData` Class**: Bertindak sebagai model untuk setiap baris (lapis tulangan) di dalam `DataGrid`. Class ini mengimplementasikan `INotifyPropertyChanged` untuk memungkinkan data binding dua arah dengan UI. Setiap perubahan pada properti (`Spacing`, `Diameter`, dll.) akan secara otomatis diperbarui di UI, dan sebaliknya.

2.  **View**: Antarmuka pengguna (UI) yang didefinisikan dalam file XAML.
    *   **`MainWindow.xaml`**: Berisi semua elemen visual seperti `DataGrid`, `Button`, `TextBlock`, dan `ComboBox`. View ini bertanggung jawab untuk menampilkan data dari ViewModel dan menangkap interaksi pengguna (klik tombol, input data).

3.  **ViewModel**: Bertindak sebagai perantara antara Model dan View.
    *   **`MultiLayerWindow` Class**: Class utama yang mengelola state aplikasi. Ini berisi `ObservableCollection` dari `LayerData` (model), menangani event dari UI (view), dan menjalankan logika bisnis (misalnya, memanggil Logic Library).

```mermaid
graph TD
    subgraph "View (MainWindow.xaml)"
        A[DataGrid: layersDataGrid]
        B[Button: btnCreate]
    end

    subgraph "ViewModel (MultiLayerWindow Class)"
        C[ObservableCollection<LayerData>]
        D[Event Handlers: on_create(), on_add_layer()]
        E[Logic: Panggil Logic Library]
    end

    subgraph "Model (LayerData Class)"
        F[Properties: Spacing, Diameter, Direction]
    end

    A -- Data Binding --> C;
    B -- Triggers Event --> D;
    D -- Memanipulasi --> C;
    C -- Berisi --> F;
    D -- Menggunakan Data dari --> F;
    E -- Dipanggil oleh --> D;

    classDef m fill:#FADBD8,stroke:#C0392B,stroke-width:2px;
    classDef v fill:#D4E6F1,stroke:#2E86C1,stroke-width:2px;
    classDef vm fill:#D5F5E3,stroke:#28B463,stroke-width:2px;
    class A,B v;
    class C,D,E vm;
    class F m;
```

## 3. Analisis Komponen Detail

### 3.1. `MainWindow.xaml` (View)

File ini mendefinisikan struktur dan tampilan dari UI.

| Kontrol Utama | `x:Name` | Fungsi | Keterangan Binding |
| :--- | :--- | :--- | :--- |
| **DataGrid** | `layersDataGrid` | Menampilkan daftar lapis tulangan yang dapat dikonfigurasi. | `ItemsSource` di-binding ke `ObservableCollection<LayerData>` di ViewModel. Setiap kolom di-binding ke properti di class `LayerData`. |
| **Tombol Toolbar** | `btnAddLayer`, `btnRemove`, dll. | Memanipulasi koleksi `LayerData` (menambah, menghapus, menduplikasi baris). | Setiap tombol memiliki `Click` event handler yang terhubung ke metode di class `MultiLayerWindow`. |
| **Panel Summary** | `txtTotalLayers`, `txtInstanceCount`, `txtMaxCover` | Menampilkan ringkasan data secara real-time. | Diperbarui secara manual oleh metode `update_summary()` di ViewModel setiap kali ada perubahan pada koleksi `LayerData`. |
| **Tombol Aksi** | `btnCreate`, `btnCancel` | Memulai proses pembuatan `AreaReinforcement` atau menutup window. | `btnCreate` memvalidasi data dan memicu alur kerja utama. `btnCancel` menutup window. |
| **Template** | `btnSaveTemplate`, `btnLoadTemplate` | Menyimpan/memuat konfigurasi `LayerData` ke/dari file JSON. | Event handler akan menangani serialisasi dan deserialisasi dari `ObservableCollection`. |

### 3.2. `script.py` (ViewModel & Controller)

File ini berisi logika utama aplikasi.

#### `LayerData` Class (Model)
-   Berisi semua properti untuk satu lapis tulangan (`Position`, `Diameter`, `Spacing`, `Direction`, `BarType`, dll.).
-   Implementasi `INotifyPropertyChanged` sangat krusial untuk memastikan UI selalu sinkron dengan data.

#### `MultiLayerWindow` Class (ViewModel)
-   **`__init__()`**: Menginisialisasi window, memuat XAML, dan menyiapkan data binding serta event handler.
-   **`_setup_data()`**: Membuat `ObservableCollection` untuk `LayerData` dan mengambil data dari Revit (misalnya, daftar `RebarBarType` yang tersedia).
-   **`_setup_event_handlers()`**: Menghubungkan tombol-tombol di UI ke metode Python (`on_add_layer`, `on_create`, dll.).
-   **Event Handlers (`on_...`)**: Metode-metode ini berisi logika untuk merespons interaksi pengguna. Contoh: `on_add_layer` akan membuat instance baru dari `LayerData` dan menambahkannya ke `ObservableCollection`.
-   **`on_create()`**: Metode paling penting. Ini akan:
    1.  Mengambil konfigurasi `LayerData` dari `ObservableCollection`.
    2.  Memvalidasi input pengguna.
    3.  Memanggil `main()` function yang akan mengeksekusi alur kerja utama.

#### `main()` Function (Controller)
-   Ini adalah titik masuk utama setelah UI ditutup dengan sukses.
-   Bertanggung jawab untuk mengorkestrasi panggilan ke **Logic Library**.
-   **Langkah 1: Panggil Geometry Conversion**
    ```python
    # Panggil LOG-UTIL-REBAR-003
    geo_result = convert_filled_region_to_area_reinforcement_geometry(...)
    if not geo_result['success']:
        # Handle error
        return
    ```
-   **Langkah 2: Iterasi & Buat Area Reinforcement**
    -   Logika untuk mengelompokkan `LayerData` menjadi `AreaReinforcement` (misalnya, 2 lapis per `AreaReinforcement`).
    -   Di dalam loop, panggil `LOG-UTIL-REBAR-001`:
    ```python
    # Panggil LOG-UTIL-REBAR-001
    area_reinf = create_area_reinforcement_safe(
        doc, geo_result['curves'], host, ...
    )
    ```
-   **Langkah 3: Panggil Parameter Override**
    -   Setelah `AreaReinforcement` dibuat, siapkan dictionary `overrides` dari `LayerData`.
    -   Panggil `LOG-UTIL-REBAR-002`:
    ```python
    overrides = {
        'Layout Rule': 3,
        'Top Major Spacing': layer.Spacing, # Akan dikonversi otomatis
        'Top Major Bar Type': layer.RebarBarTypeId
        # ... parameter lainnya
    }
    # Panggil LOG-UTIL-REBAR-002
    override_area_reinforcement_parameters(area_reinf, overrides, logger)
    ```

## 4. Alur Data Detail

Alur data dari input pengguna hingga menjadi elemen Revit adalah sebagai berikut:

1.  **Input Pengguna**: Pengguna mengubah nilai di `DataGrid` (misalnya, mengubah `Spacing` dari 150 menjadi 200).
2.  **Data Binding**: Berkat `INotifyPropertyChanged`, properti `Spacing` pada instance `LayerData` yang sesuai di dalam `ObservableCollection` secara otomatis diperbarui.
3.  **Update Summary**: Event handler pada `ObservableCollection` (`CollectionChanged`) atau pemanggilan manual `update_summary()` akan mengkalkulasi ulang nilai di panel summary.
4.  **Tombol "Create" Ditekan**: Metode `on_create()` dipanggil.
5.  **Ekstraksi Konfigurasi**: `on_create()` mengambil daftar `LayerData` dari `ObservableCollection`.
6.  **Orkestrasi Logic Library**: `main()` function dipanggil dan mulai mengeksekusi alur kerja:
    *   `FilledRegion` diubah menjadi `Curve`s.
    *   `Curve`s digunakan untuk membuat `AreaReinforcement`.
    *   Setiap `LayerData` diubah menjadi dictionary `overrides`.
    *   Dictionary `overrides` digunakan untuk mengkonfigurasi `AreaReinforcement` yang baru dibuat.
7.  **Hasil**: Elemen `AreaReinforcement` muncul di model Revit, sudah terkonfigurasi sepenuhnya.

## 5. Rencana Refactoring & Implementasi

Untuk membuat skrip ini berfungsi penuh sesuai desain, langkah-langkah berikut perlu dilakukan:

1.  **Selesaikan UI Binding**: Pastikan semua `ComboBox` di `DataGrid` (`Position`, `Bar Type`, `Direction`) terhubung dengan benar ke `ItemsSource` yang sesuai di ViewModel.
2.  **Implementasi Event Handlers**: Lengkapi logika untuk semua tombol toolbar (`Duplicate`, `Move Up/Down`, `Save/Load Template`).
3.  **Refactor `main()` Function**: Ganti logika pembuatan `AreaReinforcement` yang ada saat ini dengan panggilan ke **Logic Library** yang sudah distandarisasi.
4.  **Buat Logika Pengelompokan Lapis**: Implementasikan fungsi `group_layers_into_instances()` yang secara cerdas mengelompokkan `LayerData` menjadi `AreaReinforcement`. Satu `AreaReinforcement` dapat menampung hingga 4 lapis (Top/Bottom, Major/Minor).
5.  **Buat Logika Pemetaan Parameter**: Buat fungsi yang menerjemahkan `LayerData` menjadi dictionary `overrides` yang siap digunakan oleh `override_area_reinforcement_parameters()`.
6.  **Validasi Input**: Implementasikan `validate_all_layers()` untuk memeriksa input pengguna sebelum proses pembuatan dimulai dan tampilkan pesan error di `txtValidation`.

Dengan mengikuti spesifikasi ini, skrip "Multi-Layer Area Reinforcement" dapat diimplementasikan secara modular, kuat, dan mudah dipelihara, selaras dengan standar kualitas PrasKaaPykit.