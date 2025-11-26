# Create Filter Section by Subcategory

## Deskripsi

**Create Filter Section by Subcategory** adalah tool untuk membuat parameter filter di Revit berdasarkan parameter "Sub Category" (shared/project parameter). Tool ini secara otomatis membuat filter yang menampilkan semua section views, callouts, dan elevations KECUALI yang memiliki subcategory tertentu.

Tool ini sangat berguna untuk mengontrol visibility section views dalam proyek BIM, memungkinkan filtering berdasarkan subcategory untuk presentasi yang lebih clean dan terorganisir.

## Fitur Utama

- **Automatic Filter Creation**: Buat parameter filter otomatis berdasarkan subcategory
- **Multi-Category Support**: Filter berlaku untuk Sections, Callouts, dan Elevations
- **Smart Naming**: Generate nama filter otomatis dari input subcategory
- **Duplicate Prevention**: Check existing filters untuk menghindari duplikasi
- **Parameter Validation**: Validasi keberadaan parameter "Sub Category"
- **Transaction Safety**: Semua operasi dalam Revit transaction
- **User-Friendly Input**: Input format dengan contoh dan validation

## Cara Kerja

### Algoritma Filter Creation
1. **User Input**: Prompt untuk nama subcategory (format: xx.x_TypeofSubCategory)
2. **Name Processing**: Parse input dan generate nama filter yang readable
3. **Parameter Lookup**: Cari parameter "Sub Category" dalam project
4. **Rule Creation**: Buat filter rule "NOT EQUALS" untuk exclude subcategory
5. **Category Assignment**: Assign ke Sections, Callouts, dan Elevations
6. **Filter Creation**: Buat ParameterFilterElement baru
7. **Validation**: Check duplikasi nama filter

### Filter Logic
```python
# Filter menampilkan semua elements KECUALI yang memiliki subcategory tertentu
filter_rule = DB.ParameterFilterRuleFactory.CreateNotEqualsRule(
    param_id,           # Sub Category parameter
    sub_category_input, # Input user
    False               # case-sensitive
)
```

## Langkah Penggunaan

### Basic Usage
1. Jalankan script dari DrawingSet panel → Views pulldown
2. **Input Subcategory**: Masukkan nama subcategory dengan format `xx.x_TypeofSubCategory`
3. **Automatic Processing**: Script akan generate nama filter dan create filter
4. **Success Notification**: Toast notification akan muncul jika berhasil

### Input Format Examples
```
Input: "01.1_StructuralFraming"
Output Filter: "Selection - Potongan Structural Framing"

Input: "02.2_ArchitecturalWalls"
Output Filter: "Selection - Potongan Architectural Walls"

Input: "03.3_MEP_Ductwork"
Output Filter: "Selection - Potongan Mep Ductwork"
```

## Contoh Penggunaan

### Skenario: Filter Structural Sections
```
Input: "01.1_StructuralFraming"
Result: Filter "Selection - Potongan Structural Framing"

Filter akan menampilkan:
✅ Architectural sections
✅ MEP sections
✅ Other subcategories
❌ Structural framing sections
```

### Skenario: Presentation Cleanup
```
Input: "99.9_TempConstruction"
Result: Filter "Selection - Potongan Temp Construction"

Filter akan hide semua temporary construction sections
untuk clean presentation drawings
```

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Terinstall dan aktif
- **Parameter**: Project/shared parameter "Sub Category" harus ada

### Project Requirements
- **Sub Category Parameter**: Parameter text/string untuk subcategory classification
- **Section Views**: Minimal satu section/callout/elevation view
- **Filter Permissions**: User dapat create parameter filters

## Parameter Setup

### Required Parameter
- **Name**: "Sub Category"
- **Type**: Text/String parameter
- **Scope**: Project/Shared parameter
- **Usage**: Untuk classify section subcategories

### Parameter Values Examples
```
01.1_StructuralFraming
02.2_ArchitecturalWalls
03.3_MEP_Ductwork
04.4_SiteWork
99.9_TempConstruction
```

## Output dan Categories

### Target Categories
Filter diterapkan ke tiga built-in categories:
- **OST_Sections**: Section views
- **OST_Callouts**: Callout views
- **OST_Elev**: Elevation views

### Filter Behavior
- **Inclusive Display**: Menampilkan semua kecuali subcategory yang disebutkan
- **Case Sensitive**: Matching case-sensitive untuk parameter values
- **View-specific**: Filter dapat di-apply per view

## Error Handling

### Common Errors
- **Parameter Not Found**: Parameter "Sub Category" tidak ada dalam project
- **Duplicate Filter**: Filter dengan nama sama sudah ada
- **Invalid Input**: Input subcategory kosong atau invalid
- **Transaction Failure**: Database operation gagal

### Error Messages
- **Parameter Error**: "Project/Shared Parameter 'Sub Category' tidak ditemukan"
- **Filter Exists**: "A filter with the name: [name] already exists"
- **Creation Error**: "Error creating filter: [details]"

## Tips Penggunaan

### Best Practices
- **Consistent Naming**: Gunakan format `xx.x_CategoryName` untuk subcategory
- **Filter Organization**: Buat filters untuk setiap major category
- **View Templates**: Assign filters ke view templates untuk consistency
- **Documentation**: Dokumentasi subcategory naming convention

### Workflow Integration
- **Pre-Presentation**: Buat filters sebelum membuat presentation views
- **Quality Control**: Gunakan filters untuk verify section categorization
- **Team Coordination**: Share subcategory naming standards dengan team

### Troubleshooting
- **Filter Not Working**: Check parameter values dan case sensitivity
- **No Effect**: Verify filter di-apply ke view yang benar
- **Performance**: Too many filters dapat slow down view regeneration

## Teknologi

### Core Technologies
- **Language**: Python dengan IronPython
- **API**: Revit Database API untuk parameter filters
- **UI**: pyRevit forms untuk user input
- **Transaction**: Revit Transaction untuk data safety

### Key Classes
- **ParameterFilterElement**: Container untuk filter definition
- **ElementParameterFilter**: Filter logic implementation
- **ParameterFilterRuleFactory**: Rule creation utilities

### Filter Components
- **Filter Rule**: NOT EQUALS rule untuk exclusion logic
- **Categories**: ElementId collection untuk target categories
- **Parameter Reference**: ParameterElement.Id untuk rule binding

## Integration

### Complementary Tools
- **View Management**: Tools untuk apply filters ke views
- **Parameter Tools**: Utilities untuk manage shared parameters
- **Template Tools**: View templates dengan pre-assigned filters

### Workflow Position
- **Setup Phase**: Buat filters di awal project setup
- **Documentation Phase**: Apply filters untuk clean drawings
- **Presentation Phase**: Use filters untuk client presentations

## Versi

- **Versi**: 1.0
- **Penulis**: Cline + PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+
- **Based on**: Dynamo graph adaptation

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - DrawingSet.panel/Views/Create Filter Section by Subcategory**
*Professional View Filtering Tools untuk BIM Documentation*