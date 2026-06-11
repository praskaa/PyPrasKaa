# Reset Line Color Overrides

## Deskripsi

**Reset Line Color Overrides** adalah tool untuk menghapus semua graphic overrides (warna garis dan pola) dari elemen yang dipilih dalam view aktif. Tool ini mengembalikan tampilan elemen ke kondisi default tanpa override warna.

Tool ini penting dalam workflow BIM untuk membersihkan temporary color overrides yang telah diterapkan untuk presentation atau debugging, memastikan bahwa elemen kembali ke tampilan standard sebelum final plotting atau delivery.

## Fitur Utama

- **Complete Reset**: Menghapus semua graphic overrides dari selected elements
- **Selection-Based**: Bekerja hanya pada elemen yang dipilih
- **Safe Operation**: Menggunakan clear OverrideGraphicSettings
- **Transaction Protected**: Semua perubahan dalam Revit transaction
- **Validation Required**: Memastikan minimal satu elemen terpilih

## Cara Kerja

### Reset Mechanism
1. **Element Selection**: Mendapatkan selection aktif dari user
2. **Validation**: Memastikan minimal satu elemen terpilih
3. **Transaction Start**: Membuat Revit transaction untuk perubahan
4. **Clear Overrides**: Menerapkan OverrideGraphicSettings kosong pada setiap elemen
5. **Transaction Commit**: Menyimpan perubahan

### Technical Implementation
```python
# Create clear graphic settings (no overrides)
clear_settings = DB.OverrideGraphicSettings()

# Apply to each selected element
for element in selection:
    revit.active_view.SetElementOverrides(element.Id, clear_settings)
```

## Langkah Penggunaan

### Basic Usage
1. Jalankan script dari Line Color panel → Colors3 stack → Reset
2. **Select Elements**: Pilih elemen yang ingin di-reset overrides-nya
3. **Automatic Reset**: Semua graphic overrides otomatis dihapus
4. **Default Appearance**: Elemen kembali ke tampilan standard

### Advanced Usage
- **Multiple Selection**: Pilih banyak elemen untuk reset bersamaan
- **Selective Reset**: Reset hanya elemen tertentu yang perlu dikembalikan
- **View-Specific**: Reset berlaku per view (overrides adalah view-specific)

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Terinstall dan aktif
- **Selection**: Minimal satu elemen harus dipilih

### Project Requirements
- **View Type**: Mendukung semua view types dengan graphic overrides
- **Element Types**: Elemen yang memiliki graphic overrides aktif

## Operation Details

### What Gets Reset
- **Projection Line Color**: Warna garis proyeksi kembali ke default
- **Cut Line Color**: Warna garis potong kembali ke default
- **Pattern Fill Color**: Warna fill pattern kembali ke default
- **Line Weight Overrides**: Ketebalan garis kembali ke default
- **Pattern Overrides**: Pattern style kembali ke default

### What Stays Unchanged
- **Element Properties**: Actual element properties tidak berubah
- **Family Types**: Type properties tetap sama
- **View Properties**: View settings tidak terpengaruh
- **Model Geometry**: Actual geometry tidak berubah

## Tips Penggunaan

### Best Practices
- **Before Plotting**: Selalu reset overrides sebelum final plotting
- **Clean Presentation**: Pastikan semua overrides dihapus untuk deliverables
- **Selective Reset**: Reset hanya elemen yang perlu dikembalikan
- **Regular Cleanup**: Lakukan reset secara berkala selama development

### Workflow Integration
- **Presentation Phase**: Reset sebelum client presentations
- **Plotting Phase**: Reset sebelum PDF generation
- **Delivery Phase**: Reset sebelum project handover
- **Quality Control**: Pastikan deliverables bebas dari temporary overrides

### Troubleshooting
- **No Selection**: Pastikan minimal satu elemen terpilih
- **No Effect**: Elemen mungkin tidak memiliki overrides aktif
- **Transaction Failed**: Check model permissions dan worksharing status

## Teknologi

### Core Technologies
- **pyRevit**: Framework untuk Revit automation
- **Revit API**: OverrideGraphicSettings dan SetElementOverrides
- **Transaction System**: Safe database modifications

### Implementation Details
```python
from pyrevit import revit, DB, forms

# Get selection
selection = revit.get_selection()

# Validate selection
if len(selection) > 0:
    with revit.Transaction('Line Color'):
        # Create clear settings
        clear_settings = DB.OverrideGraphicSettings()
        
        # Apply to each element
        for element in selection:
            revit.active_view.SetElementOverrides(element.Id, clear_settings)
else:
    forms.alert('You must select at least one element.', exitscript=True)
```

## Integration dengan Tools Lain

### Complementary Tools
- **Color Tools**: Semua color override tools (Green, Red, Blue, etc.)
- **Line&PatternColor**: Custom color picker
- **LineColor**: Custom line color tool

### Workflow Position
- **End of Presentation**: Reset setelah presentation work selesai
- **Pre-Plotting**: Reset sebelum generating final plots
- **Quality Assurance**: Reset untuk clean deliverables

### Related Tools
- **View Templates**: Untuk permanent view settings
- **Visibility Settings**: Untuk element visibility control
- **Graphic Display Options**: Untuk global view settings

## Contoh Penggunaan

### Skenario: Pre-Plotting Cleanup
```
1. Project presentation selesai dengan berbagai color overrides
2. Jalankan Reset tool
3. Pilih semua elemen yang di-override
4. Overrides dihapus, tampilan kembali ke default
5. Generate final plots dengan tampilan clean
```

### Skenario: Selective Reset
```
1. Beberapa elemen masih perlu override untuk review
2. Pilih hanya elemen yang sudah final
3. Jalankan Reset pada selected elements
4. Elemen final kembali ke default, others tetap di-override
5. Lanjutkan work dengan elemen yang masih perlu review
```

## Error Handling

### Common Errors
- **No Elements Selected**: User diminta memilih minimal satu elemen
- **Transaction Failure**: Operasi dibatalkan dengan error message
- **Permission Issues**: Check worksharing permissions

### Recovery
- **Partial Success**: Jika beberapa elemen gagal, yang lain tetap diproses
- **Rollback**: Transaction rollback jika terjadi error critical
- **User Feedback**: Clear error messages untuk troubleshooting

## Versi

- **Versi**: 1.0
- **Penulis**: David Vadkerti
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+
- **Dependencies**: pyRevit framework

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - Line Color.panel/Colors3/Reset**
*Reset Graphic Overrides untuk Clean BIM Deliverables*