# PrasKaa PyKit Hooks Documentation

Dokumentasi lengkap untuk semua Hooks yang tersedia di PrasKaa PyKit Extension. Hooks ini dirancang untuk memberikan kontrol dan monitoring terhadap berbagai event dalam Revit.

## 📋 Daftar Isi

- [Overview](#overview)
- [Kategori Hooks](#kategori-hooks)
  - [App Initialization Hooks](#app-initialization-hooks)
  - [Command Before Execution Hooks](#command-before-execution-hooks)
  - [Document Event Hooks](#document-event-hooks)
  - [Family Loading Hooks](#family-loading-hooks)
  - [File Import Hooks](#file-import-hooks)
- [Detail Fungsi Hooks](#detail-fungsi-hooks)
- [Lokasi Penyimpanan Log](#lokasi-penyimpanan-log)
- [Konfigurasi](#konfigurasi)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

Hooks dalam PrasKaa PyKit adalah event handlers yang dipicu oleh berbagai aksi dalam Revit. Mereka digunakan untuk:
- Monitoring aktivitas pengguna
- Validasi proses tertentu
- Pemberian peringatan kepada pengguna
- Logging aktivitas untuk audit trail
- Memastikan kepatuhan terhadap standar perusahaan

## 📂 Kategori Hooks

### 1. App Initialization Hooks

| Hook | File | Fungsi |
|------|------|--------|
| **App Init** | `app-init.py` | Inisialisasi aplikasi saat Revit startup |

### 2. Command Before Execution Hooks

| Hook | File | Fungsi |
|------|------|--------|
| **Link CAD** | `command-before-exec[ID_FILE_CADFORMAT_LINK].py` | Peringatan sebelum link file CAD |
| **Shared Parameters** | `command-before-exec[ID_FILE_EXTERNAL_PARAMETERS].py` | Peringatan untuk parameter eksternal |
| **Import CAD** | `command-before-exec[ID_FILE_IMPORT].py` | Peringatan untuk import file CAD |
| **In Place Component** | `command-before-exec[ID_INPLACE_COMPONENT].py` | Peringatan untuk komponen in-place |
| **Architectural Column** | `command-before-exec[ID_OBJECTS_COLUMN].py` | Peringatan untuk pembuatan kolom arsitektural |
| **Ramp** | `command-before-exec[ID_OBJECTS_RAMP].py` | Peringatan untuk pembuatan ramp |
| **Roof by Extrusion** | `command-before-exec[ID_ROOF_EXTRUSION].py` | Peringatan untuk roof by extrusion |
| **Project Parameters** | `command-before-exec[ID_SETTINGS_PROJECT_PARAMETERS].py` | Peringatan untuk parameter proyek |

### 3. Document Event Hooks

| Hook | File | Fungsi |
|------|------|--------|
| **Doc Changed** | `doc-changed.py` | Monitoring perubahan dokumen |
| **Doc Closing** | `doc-closing.py` | Peringatan saat menutup dokumen |
| **Doc Opened** | `doc-opened.py` | Logging waktu pembukaan dokumen |
| **Doc Opening** | `doc-opening.py` | Monitoring proses pembukaan dokumen |
| **Doc Saved** | `doc-saved.py` | Logging waktu penyimpanan dokumen |
| **Doc Saving** | `doc-saving.py` | Monitoring proses penyimpanan dokumen |
| **Doc Synced** | `doc-synced.py` | Logging waktu sync dokumen |
| **Doc Syncing** | `doc-syncing.py` | Monitoring proses sync dokumen |
| **Doc Updater** | `doc-updater.py` | Auto-update door/window swing parameters |

### 4. Family Loading Hooks

| Hook | File | Fungsi |
|------|------|--------|
| **Family Loading** | `family-loading.py` | Monitoring dan validasi saat load family |

### 5. File Import Hooks

| Hook | File | Fungsi |
|------|------|--------|
| **File Imported** | `file-imported.py` | Peringatan untuk file yang di-import |

## 🔍 Detail Fungsi Hooks

### 1. App Initialization Hooks

#### `app-init.py`
**Lokasi**: `hooks/app-init.py`

**Fungsi Utama**:
- Inisialisasi konfigurasi saat Revit startup
- Setup path untuk library dan custom tools
- Validasi versi Revit dan memberikan peringatan jika versi tidak sesuai
- Menampilkan mass message dari server
- Setup logging untuk aktivitas tools

**Konfigurasi yang di-set**:
- `hookLogs`: Path untuk log hooks
- `revitBuildLogs`: Path untuk log build Revit
- `revitBuilds`: Informasi build Revit
- `massMessagePath`: Path untuk mass message
- `syncLogPath`: Path untuk log sync
- `openingLogPath`: Path untuk log pembukaan file
- `dashboardsPath`: Path untuk dashboards
- `language`: Bahasa yang digunakan
- `telemetry`: Setup untuk telemetry logging

### 2. Command Before Execution Hooks

Semua hooks dalam kategori ini memberikan peringatan dialog sebelum mengeksekusi command tertentu:

#### `command-before-exec[ID_FILE_CADFORMAT_LINK].py`
- **Peringatan**: Sebelum link file CAD ke dalam Revit
- **Opsi**: Continue, Cancel, More Info
- **Log**: Ya, ke server

#### `command-before-exec[ID_FILE_EXTERNAL_PARAMETERS].py` 
- **Peringatan**: Sebelum mengedit shared parameters
- **Opsi**: View list, Edit, Cancel, More Info
- **Log**: Ya, ke server

#### `command-before-exec[ID_FILE_IMPORT].py`
- **Peringatan**: Sebelum import file CAD
- **Status**: Hook ini masih dalam development (commented out)
- **Log**: Tidak aktif

#### `command-before-exec[ID_INPLACE_COMPONENT].py` 
- **Peringatan**: Sebelum membuat komponen in-place
- **Opsi**: Create, Cancel, More Info
- **Log**: Ya, ke server

#### `command-before-exec[ID_OBJECTS_COLUMN].py` **TIDAK BUTUH**
- **Peringatan**: Sebelum membuat kolom arsitektural
- **Opsi**: Create, Cancel, More Info
- **Log**: Ya, ke server

#### `command-before-exec[ID_OBJECTS_RAMP].py` **TIDAK BUTUH**
- **Peringatan**: Sebelum membuat ramp
- **Opsi**: Create, Cancel, More Info
- **Log**: Ya, ke server

#### `command-before-exec[ID_ROOF_EXTRUSION].py` **TIDAK BUTUH**
- **Peringatan**: Sebelum membuat roof by extrusion
- **Opsi**: Create, Cancel, More Info
- **Log**: Ya, ke server

#### `command-before-exec[ID_SETTINGS_PROJECT_PARAMETERS].py`
- **Peringatan**: Sebelum mengedit project parameters
- **Opsi**: View list, Edit, Cancel, More Info
- **Log**: Ya, ke server

### 3. Document Event Hooks

#### `doc-changed.py`
- **Fungsi**: Monitoring perubahan pada dokumen
- **Output**: IDs dari elemen yang diubah/dihapus
- **Log**: Tidak ada log file khusus

#### `doc-closing.py`
- **Fungsi**: Peringatan saat menutup dokumen dengan multiple views terbuka
- **Opsi**: Save list of opened views, Skip, More info
- **Log**: Menyimpan list views yang terbuka ke file HTML

#### `doc-opened.py`
- **Fungsi**: Logging waktu pembukaan dokumen
- **Output**: Waktu yang dibutuhkan untuk membuka file
- **Log**: `[central_filename]_Open.log`

#### `doc-opening.py`
- **Fungsi**: Monitoring proses pembukaan dokumen
- **Output**: Timestamp saat mulai membuka file
- **Log**: `[local_filename]_Open.tmp` (temporary file)

#### `doc-saved.py`
- **Fungsi**: Logging waktu penyimpanan dokumen
- **Output**: Waktu yang dibutuhkan untuk save
- **Log**: `[central_filename]_Save.log`

#### `doc-saving.py`
- **Fungsi**: Monitoring proses penyimpanan dokumen
- **Output**: Timestamp saat mulai save
- **Log**: `[local_filename]_Save.tmp` (temporary file)

#### `doc-synced.py`
- **Fungsi**: Logging waktu sync dokumen
- **Output**: Waktu yang dibutuhkan untuk sync
- **Log**: `[central_filename]_Sync.log`

#### `doc-syncing.py`
- **Fungsi**: Monitoring proses sync dokumen
- **Output**: Timestamp saat mulai sync
- **Log**: `[local_filename]_Sync.tmp` (temporary file)

#### `doc-updater.py`
- **Fungsi**: Auto-update door/window swing parameters
- **Output**: Update parameter 'Door Swing' dan 'Window Flip'
- **Log**: Tidak ada log file khusus

### 4. Family Loading Hooks

#### [`hooks/family-loading.py`](hooks/family-loading.py:1)
- **Fungsi**: Monitoring dan validasi saat load family
- **Validasi**: Ukuran file family (warning jika > 1MB)
- **Log**: Nama file log mengikuti pola `[central_filename]_FamilyLoad.log`
- **Lokasi Log (default)**: `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\FamilyLoad`
- **Konfigurasi**: Path log dapat diubah melalui parameter [`familyloadLogPath`](config/ct_config.ini:1) di file [`config/ct_config.ini`](config/ct_config.ini:1). Nilai default juga didefinisikan di [`lib/customOutput.py`](lib/customOutput.py:1).
- **Format Entry**: timestamp TAB username TAB family_name TAB family_path TAB size_bytes TAB document_title (contoh: `2025-08-26 22:22:28\tptade\tConcrete_Column_Rectangular\tF:\...\t1851392\tB_FLUEPIPE`)
- **Debugging**:
  - Selama pengembangan, fungsi debug menulis ke file `debug.log` di folder log. Untuk mengaktifkan/non-aktifkan debug secara lokal, edit flag DEBUG_MODE di [`hooks/family-loading.py`](hooks/family-loading.py:1).
  - Debug sebaiknya hanya diaktifkan saat troubleshooting karena menghasilkan banyak output.
- **Catatan Operasional**:
  - Setelah melakukan perubahan pada hook, restart Revit agar hook yang diperbarui aktif.
  - Pastikan folder log memiliki permission tulis; gunakan path default atau sesuaikan dengan struktur perusahaan.
  - Jika parameter konfigurasi tidak ditemukan, hook akan menggunakan fallback ke path default di atas.

### 5. File Import Hooks

#### `file-imported.py`
- **Fungsi**: Peringatan untuk file yang di-import
- **Validasi**: Import di 3D view
- **Opsi**: Continue, Cancel, Undo, More Info
- **Log**: Ya, ke server

## 📁 Lokasi Penyimpanan Log

### Default Log Paths

| Tipe Log | Lokasi Default | Konfigurasi |
|----------|----------------|-------------|
| **Hooks Log** | `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\hooksLogs` | `hookLogs` |
| **Revit Build Logs** | `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\revitBuildLogs` | `revitBuildLogs` |
| **Sync Logs** | `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\syncTimeLogs` | `syncLogPath` |
| **Opening Logs** | `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\openingTimeLogs` | `openingLogPath` |
| **Family Loading Logs** | Project directory atau Documents folder | Dinamis |
| **Telemetry Logs** | `F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\toolsLogs` | `telemetry` |

### Struktur File Log

#### Format Log
```
[Timestamp] [Duration] [Username] [Action] [Details]
```

#### Contoh Log Entry
```
2024-01-15 14:30:25	00:00:03.5	john.doe	Document Opened	Project_Model.rvt
```

## ⚙️ Konfigurasi

### File Konfigurasi
- **Primary**: `config/ct_config.ini`
- **Backup**: `pyRevit_config.ini` (user config)

### Parameter Konfigurasi

```ini
[DEFAULT]
hookLogs=F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\hooksLogs
revitBuildLogs=F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\revitBuildLogs
syncLogPath=F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\syncTimeLogs
openingLogPath=F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\openingTimeLogs
massMessagePath=F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\massMessage
dashboardsPath=F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\dashboards
language=0
wiki=https://praskaapykit.notion.site/wiki
```

### Disable Hooks (Optional)
Untuk menonaktifkan hooks tertentu, buat file konfigurasi:
```
hooksConfig.txt
```
Dengan format:
```
[HOOK_DISABLE]
LinkCAD=1
SharedParameters=1
```

## 🚀 Best Practices

### 1. Monitoring Aktivitas
- Review log files secara berkala untuk identifikasi masalah
- Gunakan dashboard untuk visualisasi data log

### 2. Validasi Proses
- Pastikan semua peringatan hooks dipahami oleh tim
- Dokumentasikan alasan untuk setiap peringatan

### 3. Konfigurasi
- Sesuaikan path log sesuai dengan struktur folder perusahaan
- Backup log files secara berkala

### 4. Performance
- Monitor ukuran log files untuk menghindari masalah storage
- Gunakan log rotation untuk file yang besar

## 🔧 Troubleshooting

### Masalah Umum

#### 1. Hooks Tidak Muncul
**Solusi**:
- Cek file `hooksConfig.txt` untuk disable hooks
- Pastikan file konfigurasi tidak korup
- Restart Revit

#### 2. Log Tidak Tersimpan
**Solusi**:
- Cek permission folder log
- Pastikan path konfigurasi benar
- Cek disk space

#### 3. Error Dialog
**Solusi**:
- Cek log file untuk detail error
- Pastikan semua dependencies ter-install
- Update PrasKaa PyKit ke versi terbaru

### Debug Mode
Untuk debug, tambahkan parameter di `ct_config.ini`:
```ini
[DEBUG]
debugMode=1
verboseLogging=1
```

## 📊 Contoh Penggunaan

### 1. Monitoring Waktu Pembukaan File
```bash
# Cek log pembukaan file
type "F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\openingTimeLogs\Project_Model_Open.log"
```

### 2. Analisis Sync Performance
```bash
# Cek log sync
type "F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\syncTimeLogs\Project_Model_Sync.log"
```

### 3. Validasi Family Loading
```bash
# Cek log family loading
type "C:\Users\[username]\Documents\family_load_log.txt"
```

## 📞 Support

Untuk pertanyaan atau masalah terkait hooks:
1. Cek dokumentasi ini terlebih dahulu
2. Review log files untuk troubleshooting
3. Hubungi tim support PrasKaa PyKit

## 🔄 Changelog

### v1.0.0 - Initial Release
- ✅ Dokumentasi lengkap untuk semua hooks
- ✅ Lokasi log yang jelas untuk setiap hook
- ✅ Konfigurasi yang dapat disesuaikan
- ✅ Best practices dan troubleshooting guide

---

**© 2024 PrasKaa PyKit Extension - All rights reserved**