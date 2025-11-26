# PrasKaaPyKit v2.0.0 - Advanced Revit Productivity Suite

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/praskaa/pyrevit-tools/wiki)
[![Revit](https://img.shields.io/badge/Revit-2018--2026-green.svg)](https://www.autodesk.com/products/revit/overview)
[![License](https://img.shields.io/badge/license-Proprietary-orange.svg)](LICENSE)

> **Paket alat produktivitas Revit canggih untuk rekayasa struktur dan alur kerja BIM**

PrasKaaPyKit adalah ekstensi pyRevit komprehensif yang dirancang untuk meningkatkan produktivitas dan merampingkan alur kerja di Autodesk Revit. Ekstensi ini menyediakan alat canggih untuk pemodelan, dokumentasi, kontrol kualitas, dan utilitas yang sangat diperlukan untuk proyek BIM berskala besar.

## 🎯 Fitur Utama

### 🏗️ **Modeling Tools - Alat Pemodelan Canggih**
- **Dimension Tools**: Auto-dimension untuk kolom dan dinding dengan akurasi tinggi
- **Join Tools**: Penggabungan elemen struktur cerdas dengan prioritas shearwall/corewall
- **Framing Tools**: Manipulasi elemen rangka dengan kontrol kemiringan

### 📋 **Documentation Suite - Suite Dokumentasi**
- **Sheet Management**: Pengelolaan lembar dengan penomoran otomatis
- **View Management**: Kontrol tampilan dengan filter dan pengaturan crop view
- **Annotation Tools**: Penandaan cerdas dan penempatan detail otomatis
- **Wall Detail Generator**: Generator detail dinding dengan template lengkap

### 🎨 **CAD Integration - Integrasi CAD**
- **Line Color Tools**: Kontrol warna garis dengan preset dan custom picker
- **Pattern Tools**: Manajemen pola garis dengan override cerdas

### 🔍 **Quality Control - Kontrol Kualitas**
- **EXR Tools**: Validasi dan transfer marking untuk kolom dan rangka
- **Validation Tools**: Pemeriksaan tipe mark dan pemuatan tipe otomatis
- **Matching Tools**: Pencocokan elemen dengan toleransi cerdas

### 👥 **Family Management - Manajemen Family**
- **Type Generator**: Pembuatan tipe family massal dari CSV
- **Profile Updates**: Pembaruan profil dengan konversi unit otomatis
- **Template System**: Sistem template dengan repositori terpusat

### 🛠️ **Utility Tools - Alat Utilitas**
- **Grid Management**: Kontrol grid dengan toggle 2D/3D dan tabel grid
- **Adaptive Points**: Utilitas titik adaptif dengan kontrol penuh
- **Detail Items**: Inspeksi dan penghitungan detail item

### 🏗️ **Rebar Tools - Alat Rebar**
- **Area Reinforcement**: Pembuatan reinforcement area multi-layer dari filled region
- **Rebar Inspection**: Inspeksi parameter dan tipe rebar

## 📊 Statistik Ekstensi

- **Total Scripts**: 50+ alat individual
- **Categories**: 8 kategori utama
- **Revit Support**: 2018-2026
- **Language**: Bahasa Indonesia (dokumentasi utama)
- **Architecture**: Modular dengan shared libraries (lib/) dan dokumentasi spesifikasi (logic-library/)

## 🚀 Quick Start

### Instalasi
1. Install pyRevit 4.7.11 atau yang lebih baru
2. Download PrasKaaPyKit dari repository
3. Copy folder ekstensi ke direktori pyRevit extensions
4. Restart Revit dan aktifkan ekstensi

### Penggunaan Dasar
1. Buka tab **PrasKaaPyKit** di Revit ribbon
2. Pilih kategori alat yang diperlukan
3. Ikuti petunjuk di tooltip atau README masing-masing alat
4. Lihat hasil di console pyRevit untuk detail proses

## 📚 Dokumentasi Lengkap

### 📖 **Dokumentasi per Kategori**

| Kategori | Deskripsi | Jumlah Alat |
|----------|-----------|-------------|
| **Modeling** | Alat pemodelan struktur canggih | 8 alat |
| **Documentation** | Suite dokumentasi lengkap | 12 alat |
| **Line Color** | Kontrol warna garis dan pola | 15 alat |
| **QualityControl** | Validasi dan kontrol kualitas | 6 alat |
| **Templates** | Manajemen family dan template | 4 alat |
| **Utilities** | Alat utilitas umum | 6 alat |
| **Rebar** | Alat reinforcement | 5 alat |
| **Families** | Utilitas family | 2 alat |

### 🔗 **Link Dokumentasi**

#### **📚 Dokumentasi Utama**
- [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md) - 🆕 Panduan arsitektur lengkap dan prinsip desain
- [IMPORT_GUIDELINES.md](IMPORT_GUIDELINES.md) - 🆕 Best practices import dan pola yang benar
- [CHANGELOG.md](CHANGELOG.md) - Riwayat versi dan perubahan
- [CONTRIBUTING.md](CONTRIBUTING.md) - Panduan kontribusi untuk developers

#### **🔧 Dokumentasi Teknis**
- [Wall Detail Generator](PrasKaaPyKit.tab/Documentation.panel/col4.stack/Wall.pulldown/Wall%20Detail%20Generator.pushbutton/) - Dokumentasi komprehensif alat
- [Logic Library](logic-library/) - Spesifikasi dan design documents (dokumentasi saja)

**⚠️ PENTING**: Baca `ARCHITECTURE_GUIDE.md` dan `IMPORT_GUIDELINES.md` sebelum development!

## 🏗️ Arsitektur Teknis

### Struktur Ekstensi
```
PrasKaaPyKit.extension/
├── PrasKaaPyKit.tab/          # Main pyRevit tab
│   ├── bundle.yaml            # Konfigurasi utama ekstensi
│   └── [Panel].panel/         # 8 panel utama
│       ├── bundle.yaml        # Konfigurasi panel
│       └── [Tool].pulldown/   # Grup alat
│           └── [Script].pushbutton/ # Alat individual
│               ├── script.py  # 🟢 Kode utama (executable)
│               ├── README.md  # 🟢 Dokumentasi alat
│               ├── icon.png   # 🟢 Ikon alat
│               └── bundle.yaml # 🟢 Konfigurasi alat
├── lib/                       # 🟢 SHARED LIBRARIES (importable)
│   ├── Snippets/              # UI utilities
│   ├── parameters/            # Parameter utilities
│   └── *.py                   # Shared code modules
├── logic-library/             # 🔴 DOCUMENTATION ONLY (no import)
│   └── */                     # Design docs, API specs
├── ARCHITECTURE_GUIDE.md      # 🆕 Panduan arsitektur lengkap
├── IMPORT_GUIDELINES.md       # 🆕 Best practices import
├── README.md                  # 🆕 Dokumentasi utama ini
├── CONTRIBUTING.md            # 🆕 Panduan kontribusi
└── CHANGELOG.md               # Riwayat versi
```

**Color Coding:**
- 🟢 **Green**: Files yang bisa dieksekusi/diakses langsung
- 🔴 **Red**: Files yang HANYA untuk dokumentasi (jangan import)

### Teknologi Inti
- **pyRevit Framework**: Platform ekstensi utama
- **Revit API**: Akses penuh ke Revit Object Model
- **.NET Integration**: WPF UI dan Windows Forms
- **Python Libraries**: Standard dan custom utilities

## 🎯 Target Pengguna

### 👷 **Structural Engineers**
- Automatisasi pemodelan elemen struktur
- Kontrol kualitas elemen BIM
- Dokumentasi teknis otomatis

### 📐 **BIM Modelers**
- Workflow pemodelan efisien
- Manajemen tampilan dan sheet
- Integrasi CAD dan kontrol warna

### 🔍 **Quality Assurance Teams**
- Validasi model otomatis
- Transfer marking dan matching
- Inspeksi parameter massal

### 📋 **Documentation Specialists**
- Generator detail otomatis
- Manajemen annotation cerdas
- Kontrol tampilan advanced

## 🔧 Persyaratan Sistem

### Software Requirements
- **Autodesk Revit**: 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- **pyRevit**: 4.7.11 atau yang lebih baru
- **Windows**: 10/11 (64-bit)
- **.NET Framework**: 4.8 atau yang lebih baru

### Hardware Recommendations
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Multi-core processor
- **Storage**: 500MB free space untuk ekstensi

## 📈 Roadmap

### Version 2.1 (Upcoming)
- [ ] Enhanced multi-language support
- [ ] Cloud collaboration features
- [ ] Advanced reporting capabilities
- [ ] Mobile companion app

### Long-term Vision
- [ ] AI-powered automation
- [ ] Real-time collaboration
- [ ] Extended platform support
- [ ] Custom scripting framework

## 🤝 Kontribusi

Kami menyambut kontribusi dari komunitas! Sebelum berkontribusi, pastikan membaca dokumentasi berikut:

### 📖 **Dokumentasi Wajib Dibaca**
1. [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md) - Prinsip arsitektur dan struktur folder
2. [IMPORT_GUIDELINES.md](IMPORT_GUIDELINES.md) - Panduan import dan best practices
3. [CONTRIBUTING.md](CONTRIBUTING.md) - Panduan kontribusi lengkap

### Cara Berkontribusi
1. **📚 Baca dokumentasi** arsitektur dan import guidelines
2. Fork repository
3. Buat branch fitur baru: `git checkout -b feature/nama-fitur`
4. **Ikuti import guidelines** - import dari `lib/`, bukan `logic-library/`
5. Implementasi perubahan dengan coding standards
6. **Test imports** menggunakan pola yang benar
7. Tambahkan/update dokumentasi
8. Submit pull request dengan referensi ke guidelines

## 📞 Dukungan

### Resources
- **Wiki**: [PrasKaaPyKit Wiki](https://github.com/praskaa/pyrevit-tools/wiki)
- **Issues**: [GitHub Issues](https://github.com/praskaa/pyrevit-tools/issues)
- **Discussions**: [GitHub Discussions](https://github.com/praskaa/pyrevit-tools/discussions)

### Contact
- **Email**: support@praskaa.com
- **LinkedIn**: [PrasKaa Team](https://linkedin.com/company/praskaa)

## 📄 Lisensi

PrasKaaPyKit adalah ekstensi proprietary yang dikembangkan oleh Tim PrasKaa untuk keperluan internal dan profesional BIM workflow.

## 🙏 Acknowledgments

Terima kasih kepada:
- **pyRevit Community**: Untuk framework yang powerful
- **Autodesk Revit Team**: Untuk platform BIM yang excellent
- **Contributors**: Untuk kontribusi dan feedback berharga
- **Beta Testers**: Untuk testing dan validasi ekstensif

---

**PrasKaaPyKit v2.0.0** - *Meningkatkan Produktivitas BIM di Indonesia*

**Developed by**: PrasKaa Team
**Version**: 2.0.0
**Release Date**: November 2024
**Compatibility**: Revit 2018-2026