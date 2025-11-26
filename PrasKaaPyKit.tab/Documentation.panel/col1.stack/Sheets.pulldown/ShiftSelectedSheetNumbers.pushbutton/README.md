# Shift Selected Sheet Numbers

## Deskripsi

**Shift Selected Sheet Numbers** adalah tool untuk menggeser nomor sheet yang dipilih dengan jumlah yang dapat ditentukan pengguna. Tool ini memungkinkan increment (penambahan) atau decrement (pengurangan) nomor sheet dengan nilai kustom.

Tool ini berguna untuk mengatur ulang penomoran sheet dalam proyek BIM ketika ada perubahan struktur atau penambahan sheet baru.

## Fitur Utama

- **Custom Shift Amount**: Input jumlah pergeseran (positif untuk increment, negatif untuk decrement)
- **Sheet Selection**: Pilih multiple sheets untuk di-shift sekaligus
- **Smart Sorting**: Otomatis sort berdasarkan nomor sheet untuk hasil yang konsisten
- **Transaction Safety**: Semua perubahan dalam Revit transaction
- **Error Handling**: Comprehensive error handling dengan logging

## Cara Kerja

1. **Input Shift Amount**: User memasukkan jumlah pergeseran (contoh: 10, -5, 20)
2. **Select Sheets**: Pilih sheets yang akan di-shift nomornya
3. **Automatic Processing**: Script menggeser nomor sheet sesuai input
4. **Result Logging**: Menampilkan perubahan nomor sheet di log

## Langkah Penggunaan

1. Jalankan script dari Documentation panel → Sheets pulldown → Shift Selected Sheet Numbers
2. **Masukkan Shift Amount**: Input angka pergeseran (positif = increment, negatif = decrement)
3. **Pilih Sheets**: Select sheets yang ingin di-shift
4. **Konfirmasi**: Script akan otomatis memproses perubahan

## Contoh Penggunaan

### Increment Sheet Numbers
```
Input: 10
Sheet A-01 (sebelum: A-01) → Sheet A-11 (sesudah: A-11)
Sheet A-02 (sebelum: A-02) → Sheet A-12 (sesudah: A-12)
```

### Decrement Sheet Numbers
```
Input: -5
Sheet B-10 (sebelum: B-10) → Sheet B-05 (sesudah: B-05)
Sheet B-11 (sebelum: B-11) → Sheet B-06 (sesudah: B-06)
```

## Persyaratan

- **Revit**: 2018+
- **pyRevit**: Terinstall dan aktif
- **Sheets**: Minimal satu sheet ter-select atau dalam selection

## Teknologi

- **Language**: Python dengan IronPython
- **API**: Revit Database API
- **UI**: pyRevit forms untuk user input
- **Core Function**: `coreutils.decrement_str()` untuk string number manipulation

## Versi

- **Versi**: 1.0
- **Penulis**: Kilo Code
- **Compatibility**: Revit 2018-2026

---

**PrasKaaPyKit - Documentation.panel/Sheets/Shift Selected Sheet Numbers**
*Custom Sheet Number Shifting Tool untuk BIM Documentation*