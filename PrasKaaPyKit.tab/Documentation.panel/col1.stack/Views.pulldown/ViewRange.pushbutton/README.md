# View Range 3D Visualization

## Deskripsi

**View Range 3D Visualization** adalah tool canggih untuk memvisualisasikan view range planes dalam tampilan 3D interaktif di Autodesk Revit. Tool ini menampilkan top clip plane, cut plane, bottom clip plane, dan view depth plane sebagai bidang berwarna transparan dalam 3D view, memungkinkan pengguna untuk memahami dan menganalisis range view secara visual.

Tool ini sangat berguna untuk BIM modelers dan architects yang perlu memahami dan mengoptimalkan view range settings untuk dokumentasi yang akurat dan konsisten.

## Fitur Utama

- **3D Plane Visualization**: Menampilkan view range planes sebagai bidang berwarna transparan
- **Real-time Updates**: Update otomatis saat view atau selection berubah
- **Interactive WPF UI**: Interface modern dengan reactive data binding
- **Elevation Display**: Menampilkan elevasi semua planes dengan unit yang benar
- **Cross-Version Compatibility**: Mendukung Revit 2020-2026 dengan API fallbacks
- **Event-driven Updates**: Responsive terhadap view activation dan selection changes
- **Color-coded Planes**: Warna berbeda untuk setiap jenis plane (Orange, Red, Blue, Green)
- **Section Box Support**: Mendukung section box dan crop box visualization

## Cara Kerja

### Arsitektur Sistem
1. **WPF Window**: Interface utama dengan reactive data binding
2. **3D Server**: pyRevit dc3dserver untuk geometry visualization
3. **Event Handlers**: Monitoring view activation dan selection changes
4. **Context Manager**: Singleton pattern untuk state management
5. **Geometry Generation**: Real-time mesh creation untuk plane visualization

### Plane Visualization
- **Top Clip Plane**: Orange - Batas atas view range
- **Cut Plane**: Red - Plane potong utama
- **Bottom Clip Plane**: Blue - Batas bawah view range
- **View Depth Plane**: Green - Kedalaman view (untuk section views)

### Data Flow
```
View Selection → Context Update → Geometry Calculation → 3D Mesh Generation → WPF Display
```

## Langkah Penggunaan

### Setup Awal
1. Jalankan script dari Helper panel
2. **WPF Window** akan muncul menampilkan view range information
3. **Activate 3D View**: Pastikan 3D view aktif untuk visualization
4. **Select Source View**: Pilih plan atau section view di Project Browser

### Working with Views
1. **Plan Views**: Pilih plan view untuk melihat top clip, cut plane, bottom clip, view depth
2. **Section Views**: Pilih section view untuk melihat cut plane dan view depth
3. **Crop Box**: Pastikan crop box aktif pada source view
4. **Section Box**: Gunakan section box pada 3D view untuk area yang lebih besar

### Reading Information
- **Elevation Values**: Ditampilkan dalam unit project (mm, feet, etc.)
- **Plane Colors**: Visual indicator untuk setiap jenis plane
- **Status Messages**: Feedback real-time tentang view compatibility
- **Unit Labels**: Label unit sesuai project settings

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Latest version dengan dc3dserver support
- **Windows**: .NET Framework untuk WPF
- **Graphics**: DirectX compatible untuk 3D rendering

### Project Requirements
- **3D View**: Minimal satu 3D view untuk visualization
- **Plan/Section Views**: Source views dengan crop box aktif
- **View Range**: Views dengan defined view range settings

## Interface Components

### WPF Window Elements
- **Message Display**: Status dan instruction messages
- **Elevation Readouts**: Real-time elevation values untuk semua planes
- **Color Indicators**: Visual brushes untuk setiap plane type
- **Unit Display**: Project unit labels

### 3D Visualization
- **Transparent Planes**: 50% transparency untuk visibility
- **Solid Edges**: Black edges untuk definition
- **Real-time Updates**: Instant refresh saat context berubah
- **Geometry Accuracy**: Precise corner calculations dari crop/section boxes

## Technical Implementation

### Core Classes
- **Context**: Singleton untuk state management dan unit conversion
- **MainViewModel**: Reactive WPF data binding
- **MainWindow**: WPF window dengan XAML integration
- **SimpleEventHandler**: External event handling untuk UI updates

### Key Technologies
- **WPF**: Windows Presentation Foundation untuk modern UI
- **Reactive Extensions**: Real-time data binding
- **3D Geometry**: pyRevit dc3dserver untuk mesh generation
- **Event System**: Revit UI events untuk responsiveness

### API Compatibility
```python
# Cross-version unit handling
try:
    # Revit 2025+ API
    units = doc.GetUnits()
    format_options = units.GetFormatOptions(DB.SpecTypeId.Length)
    length_unit = format_options.GetUnitTypeId()
except:
    try:
        # Fallback API
        length_unit = doc.GetUnits().GetFormatOptions(DB.UnitType.UT_Length).DisplayUnits
    except:
        # Final fallback
        length_unit = DB.DisplayUnitType.DUT_MILLIMETERS
```

## Fitur Advanced

### Real-time Synchronization
- **View Activation**: Auto-update saat user switch views
- **Selection Changes**: Responsive terhadap Project Browser selection
- **Document Changes**: Update saat view properties berubah
- **Context Validation**: Continuous validation dari view compatibility

### Geometry Processing
- **Bounding Box Analysis**: Extract corners dari crop/section boxes
- **Transform Applications**: Handle view direction dan coordinate systems
- **Mesh Generation**: Create triangles dan edges untuk 3D display
- **Color Management**: Dynamic color assignment dengan transparency

### Error Handling
- **Graceful Degradation**: Fallback untuk API compatibility issues
- **User Feedback**: Clear messages untuk invalid configurations
- **Exception Safety**: Comprehensive try-catch blocks
- **Logging**: Detailed logging untuk debugging

## Contoh Penggunaan

### Skenario: Plan View Analysis
```
1. Aktifkan 3D view
2. Pilih plan view di Project Browser
3. Tool menampilkan:
   - Top Clip Plane (Orange): 4.50m
   - Cut Plane (Red): 0.00m
   - Bottom Clip Plane (Blue): -2.50m
   - View Depth (Green): -10.00m
4. Visualisasikan range dalam 3D space
```

### Skenario: Section View Setup
```
1. Aktifkan section view dengan crop box
2. Pilih section view di Project Browser
3. Tool menampilkan cut plane dan view depth
4. Adjust view range berdasarkan visual feedback
5. Verify section depth dalam 3D
```

## Tips Penggunaan

### Optimization Tips
- **View Management**: Keep 3D view clean untuk better visualization
- **Selection Focus**: Select hanya satu view di Project Browser
- **Performance**: Close window saat tidak digunakan untuk save resources
- **Unit Awareness**: Verify unit settings untuk accurate readings

### Best Practices
- **Regular Checks**: Use tool untuk verify view range sebelum plotting
- **Team Coordination**: Share understanding tentang plane colors
- **Documentation**: Include screenshots dalam BIM execution plans
- **Training**: Train team members tentang view range concepts

### Troubleshooting
- **No Visualization**: Check 3D view aktif dan crop box enabled
- **Wrong Elevations**: Verify view range settings pada source view
- **Performance Issues**: Close other applications menggunakan graphics
- **API Errors**: Update pyRevit ke latest version

## Integration dengan Workflow

### BIM Documentation
- **View Setup**: Verify view range sebelum creating sheets
- **Quality Control**: Visual check untuk section depths
- **Team Review**: Share 3D visualization untuk coordination
- **Client Presentation**: Clear visualization untuk design reviews

### Modeling Workflow
- **Plan Development**: Understand cut plane impact pada model visibility
- **Section Creation**: Optimize view depth untuk comprehensive sections
- **Detail Views**: Verify crop boundaries untuk detail accuracy
- **Coordination**: Visual check untuk clash detection areas

## Teknologi

### Dependencies
- **pyRevit Framework**: Core functionality dan UI
- **dc3dserver**: 3D geometry visualization
- **WPF**: Modern UI framework
- **.NET Framework**: Windows integration

### Performance Characteristics
- **Memory Usage**: Minimal untuk static visualization
- **CPU Load**: Low dengan event-driven updates
- **Graphics Requirements**: Standard DirectX compatibility
- **Responsiveness**: Real-time updates dengan <100ms latency

## Versi

- **Versi**: 2.0 Enhanced
- **Penulis**: PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020-2026
- **Dependencies**: pyRevit, WPF, dc3dserver

## Changelog

### v2.0 (2024) - Enhanced Release
- ✅ Cross-version API compatibility (2020-2026)
- ✅ Enhanced WPF UI dengan reactive binding
- ✅ Real-time event handling untuk view changes
- ✅ Improved geometry processing dengan transform handling
- ✅ Color-coded visualization dengan transparency
- ✅ Comprehensive error handling dan logging
- ✅ Section box support untuk 3D views

### v1.0 (2023) - Initial Release
- ✅ Basic view range visualization
- ✅ WPF interface prototype
- ✅ Core geometry generation
- ✅ Basic event handling

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - Helper.panel/ViewRange**
*Advanced 3D Visualization Tools untuk BIM View Range Analysis*