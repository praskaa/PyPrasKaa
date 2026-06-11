# Orange Line Color Override

## Deskripsi

**Orange Line Color Override** adalah tool cepat untuk mengubah warna garis proyeksi dan pola pada elemen yang dipilih dalam view aktif. Tool ini mengatur override warna garis menjadi orange (RGB: 255, 128, 0) dengan pattern color override aktif.

Tool ini bagian dari suite Line Color tools yang memungkinkan BIM modelers untuk dengan cepat mengubah tampilan elemen untuk presentasi, debugging, atau organisasi visual tanpa mengubah properties elemen secara permanen.

## Fitur Utama

- **Quick Color Override**: Mengubah warna garis proyeksi dengan satu klik
- **Pattern Color Included**: Override pattern color bersama line color
- **Temporary Override**: Perubahan bersifat temporary (view-specific)
- **Predefined Color**: Warna orange yang telah dioptimalkan untuk visibility
- **Selection-Based**: Bekerja pada elemen yang dipilih atau semua elemen

## Cara Kerja

### Override Mechanism
1. **Element Selection**: Menggunakan selection aktif atau semua elemen jika tidak ada selection
2. **Graphic Override**: Menerapkan OverrideGraphicSettings pada view
3. **Color Application**: Set projection line color ke orange (255, 128, 0)
4. **Pattern Override**: Mengaktifkan pattern color override dengan warna yang sama
5. **View-Specific**: Override hanya berlaku pada view aktif

### Color Specification
```python
# RGB Values untuk Orange
RED = 255
GREEN = 128
BLUE = 0
PATTERN_OVERRIDE = True
```

## Langkah Penggunaan

### Basic Usage
1. Jalankan script dari Line Color panel → Colors1 stack → Orange
2. **Select Elements**: Pilih elemen yang ingin di-override (atau biarkan kosong untuk semua)
3. **Automatic Override**: Warna garis otomatis berubah menjadi orange
4. **Pattern Included**: Pattern fill juga menggunakan warna orange

### Advanced Usage
- **Multiple Selection**: Pilih beberapa elemen untuk override bersamaan
- **View Switching**: Override berlaku per view, switch view untuk melihat efek berbeda
- **Reset**: Gunakan "Reset" button untuk menghapus semua overrides

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Terinstall dengan graphicOverrides module
- **Selection**: Elemen yang dipilih atau view dengan elemen

### Project Requirements
- **View Type**: Mendukung semua view types dengan graphic overrides
- **Element Types**: Semua Revit elements yang mendukung graphic overrides

## Color Properties

### Orange Color Specification
- **Hex**: #FF8000
- **RGB**: (255, 128, 0)
- **Usage**: Optimal untuk highlighting dan attention-grabbing
- **Contrast**: High contrast untuk visibility

### Override Scope
- **Projection Lines**: Garis proyeksi dalam view
- **Cut Lines**: Garis potong dalam section views
- **Fill Patterns**: Pattern fills dengan warna yang sama
- **View-Specific**: Hanya berlaku pada view aktif

## Tips Penggunaan

### Best Practices
- **Temporary Use**: Gunakan untuk presentation atau debugging
- **Color Coding**: Gunakan orange untuk elements yang perlu attention
- **View Management**: Buat view khusus untuk overrides
- **Reset When Done**: Selalu reset overrides sebelum final plotting

### Workflow Integration
- **Presentation Prep**: Highlight critical elements dengan orange
- **Debugging**: Identifikasi problematic elements dengan warna mencolok
- **Team Coordination**: Gunakan orange untuk coordination issues
- **Quality Control**: Visual check untuk elements yang perlu review

### Troubleshooting
- **No Effect**: Pastikan elemen terlihat dalam view aktif
- **Wrong Color**: Check RGB values dalam script
- **Not Persistent**: Overrides hilang saat view di-regenerate

## Teknologi

### Core Technologies
- **pyRevit**: Framework untuk Revit automation
- **Revit API**: OverrideGraphicSettings untuk graphic overrides
- **graphicOverrides Module**: Custom module untuk color utilities

### Implementation
```python
from graphicOverrides import setProjLines
setProjLines(255, 128, 0, True)  # Orange with pattern override
```

## Integration dengan Tools Lain

### Complementary Tools
- **Other Color Tools**: Red, Green, Blue untuk color coding
- **Line&PatternColor**: Custom color picker dengan config
- **Reset Tool**: Menghapus semua color overrides

### Color Suite
- **Colors1 Stack**: Green, Orange, Red (basic colors)
- **Colors2 Stack**: Azure, Blue, Magenta (cool colors)
- **Colors3 Stack**: Grey, Light Grey, Reset (neutral)
- **Custom Tools**: LineColor, Line&PatternColor (advanced)

## Versi

- **Versi**: 1.0
- **Penulis**: David Vadkerti
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+
- **Dependencies**: graphicOverrides module

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - Line Color.panel/Colors1/Orange**
*Quick Orange Color Override untuk BIM Presentation*