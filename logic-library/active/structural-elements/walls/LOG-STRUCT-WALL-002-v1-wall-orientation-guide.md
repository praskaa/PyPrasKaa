# Panduan Orientasi Dinding (Wall Orientation Guide)

## Overview
Modul ini menjelaskan cara mengetahui orientasi dinding dalam Revit API untuk keperluan Smart Tag System dalam PrasKaaPyKit.

## Cara Kerja Orientasi Dinding

### 1. Properti Wall.Orientation
```python
# Mendapatkan orientasi dinding
orientation = wall.Orientation  # Mengembalikan XYZ vector
```

**Penjelasan:**
- `Wall.Orientation` adalah properti built-in dari Revit API
- Mengembalikan vektor `XYZ` yang menunjukkan arah normal permukaan dinding
- Vektor ini selalu bernilai 1 (normalized) dan menunjuk ke arah hadap dinding

### 2. Interpretasi Vektor Orientasi

#### Koordinat Kartesian:
- **X > 0**: Dinding menghadap ke Timur (East)
- **X < 0**: Dinding menghadap ke Barat (West)
- **Y > 0**: Dinding menghadap ke Utara (North)
- **Y < 0**: Dinding menghadap ke Selatan (South)

#### Sudut dari Sumbu X:
```python
import math
angle_rad = math.atan2(orientation.Y, orientation.X)
angle_deg = math.degrees(angle_rad)
# Normalisasi ke 0-360 derajat
if angle_deg < 0:
    angle_deg += 360
```

### 3. Arah Kardinal
| Sudut (°) | Arah | Deskripsi |
|-----------|------|-----------|
| 0-22.5    | N    | Utara |
| 22.5-67.5 | NE   | Timur Laut |
| 67.5-112.5| E    | Timur |
| 112.5-157.5| SE | Tenggara |
| 157.5-202.5| S  | Selatan |
| 202.5-247.5| SW | Barat Daya |
| 247.5-292.5| W  | Barat |
| 292.5-337.5| NW | Barat Laut |
| 337.5-360 | N    | Utara |

## Implementasi dalam Smart Tag

### 1. Positioning Tag
```python
def calculate_tag_position(wall, offset_mm=100):
    # Dapatkan orientasi
    orientation = wall.Orientation

    # Dapatkan midpoint dinding
    midpoint = get_wall_midpoint(wall)

    # Konversi offset ke feet
    offset_feet = offset_mm / 304.8

    # Hitung posisi tag
    tag_position = midpoint + (orientation * offset_feet)

    return tag_position
```

### 2. Logika Positioning
- Tag ditempatkan di **midpoint** dinding
- **Offset** diterapkan searah dengan vektor orientasi
- Memastikan tag muncul di sisi luar dinding
- Menghindari tag tertutup oleh geometri dinding

### 3. Midpoint Calculation
```python
def get_wall_midpoint(wall):
    location_curve = wall.Location
    curve = location_curve.Curve

    if isinstance(curve, DB.Line):
        # Untuk dinding lurus
        start = curve.GetEndPoint(0)
        end = curve.GetEndPoint(1)
        midpoint = XYZ(
            (start.X + end.X) / 2,
            (start.Y + end.Y) / 2,
            (start.Z + end.Z) / 2
        )
    else:
        # Untuk dinding curved
        param_mid = curve.GetEndParameter(0) + (curve.GetEndParameter(1) - curve.GetEndParameter(0)) / 2
        midpoint = curve.Evaluate(param_mid, False)

    return midpoint
```

## Penggunaan dalam SmartTagEngine

### 1. Import dan Inisialisasi
```python
from wall_orientation_logic import WallOrientationHandler

class SmartTagEngine:
    def __init__(self, doc):
        self.orientation_handler = WallOrientationHandler(doc)
```

### 2. Dalam Tag Positioning
```python
def calculate_wall_tag_position(self, wall, config):
    # Dapatkan orientasi
    orientation_info = self.orientation_handler.get_wall_facing_direction(wall)

    # Hitung posisi tag
    offset_mm = config.get('offset_mm', 100)
    tag_position = self.orientation_handler.calculate_tag_position(wall, offset_mm)

    return tag_position
```

## Error Handling

### 1. Wall tanpa Orientation
```python
try:
    orientation = wall.Orientation
    if orientation is None:
        # Handle error - wall mungkin corrupted
        return None
except AttributeError:
    # Wall.Orientation tidak tersedia di versi Revit lama
    return None
```

### 2. Wall tanpa Location Curve
```python
location = wall.Location
if not isinstance(location, DB.LocationCurve):
    # Wall mungkin memiliki location yang berbeda
    return None
```

## Testing dan Validation

### 1. Unit Test
```python
def test_wall_orientation():
    # Test dengan dinding menghadap timur
    wall_east = create_test_wall(facing_east=True)
    orientation = wall_east.Orientation

    assert abs(orientation.X - 1.0) < 0.001  # Harus mendekati (1,0,0)
    assert abs(orientation.Y) < 0.001
    assert abs(orientation.Z) < 0.001
```

### 2. Visual Validation
- Tag harus muncul di sisi luar dinding
- Jarak tag sesuai dengan offset yang dikonfigurasi
- Tag tidak tertutup oleh geometri dinding

## Tips dan Best Practices

### 1. Normalisasi Vektor
```python
orientation = wall.Orientation.Normalize()
# Pastikan panjang vektor = 1
```

### 2. Handling Flipped Walls
```python
# Cek apakah wall di-flip
if wall.Flipped:
    orientation = orientation.Negate()
```

### 3. View-dependent Positioning
```python
# Pertimbangkan arah view untuk positioning yang lebih baik
view_direction = view.ViewDirection
dot_product = orientation.DotProduct(view_direction)
if dot_product < 0:
    # Tag di sisi belakang, flip orientation
    orientation = orientation.Negate()
```

## Troubleshooting

### Masalah: Tag muncul di sisi dalam dinding
**Solusi:** Cek orientasi vektor - mungkin perlu dinegasikan

### Masalah: Orientasi tidak konsisten
**Solusi:** Pastikan wall.Orientation dinormalisasi dan divalidasi

### Masalah: Tag position salah pada curved walls
**Solusi:** Gunakan parameter evaluation untuk midpoint yang akurat

## Referensi
- Revit API Documentation: Wall.Orientation property
- PrasKaaPyKit Smart Tag System
- Cartesian coordinate system dalam BIM

---
**File:** `LOG-STRUCT-WALL-002-v1-wall-orientation-guide.md`</search>
</search_and_replace>
**Updated:** 2025-10-12
**Compatibility:** Revit 2020+, pyRevit