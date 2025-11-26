---
id: LOG-UTIL-GROUP-001
version: v1
status: active
category: utilities
element_type: Grid
operation: group
revit_versions: [2024, 2026]
tags: [grid, grouping, direction, parallel, geometry, filtering]
created: 2025-11-05
updated: 2025-11-05
confidence: high
performance: medium
source_file: PrasKaaPyKit.tab/Documentation.panel/col3.stack/Wall.pulldown/Dimension Wall with Grid.pushbutton/script.py
source_location: Lines 158-205
usage_count: 1
---

# LOG-UTIL-GROUP-001-v1: Group Grids by Direction

## Problem Context

Dalam workflow BIM structural, seringkali ada kebutuhan untuk mengelompokkan elemen grid (garis koordinat) berdasarkan arah paralel mereka. Ini penting untuk operasi seperti pembuatan dimensi otomatis, di mana grid yang sejajar harus didimensi bersama dalam satu dimensi line. Tanpa pengelompokan ini, setiap grid akan didimensi secara terpisah, menghasilkan dimensi yang berlebihan dan tidak efisien.

Masalah muncul ketika:
- Grid dipilih secara manual atau otomatis dalam jumlah besar
- Grid memiliki berbagai arah (horizontal, vertikal, diagonal)
- Perlu dimensi yang bersih dan terorganisir berdasarkan orientasi

## Solution Summary

Fungsi ini mengimplementasikan algoritma greedy untuk mengelompokkan grid berdasarkan arah paralel. Algoritma memulai dari grid pertama, mencari semua grid lain yang paralel dengannya, lalu mengulangi untuk grid yang belum dikelompokkan. Grid melengkung diabaikan karena tidak memiliki arah linier yang jelas.

Pendekatan ini memastikan:
- Grid paralel dikelompokkan bersama
- Setiap grid hanya muncul dalam satu grup
- Efisiensi O(n²) untuk n grid, yang acceptable untuk jumlah grid tipikal dalam proyek

## Working Code

```python
def group_grids_by_direction(grids):
    """Group grids by their direction (parallel grids together).
    
    Returns: List of grid groups, each group is a list of grids with same direction
    """
    if not grids:
        return []
    
    groups = []
    used_grids = set()
    
    for grid in grids:
        if grid.Id in used_grids:
            continue
        
        if grid.IsCurved:
            continue
        
        # Start new group with this grid
        crv = grid.Curve
        p = crv.GetEndPoint(0)
        q = crv.GetEndPoint(1)
        grid_dir = (p - q).Normalize()
        
        current_group = [grid]
        used_grids.add(grid.Id)
        
        # Find all other grids parallel to this one
        for other_grid in grids:
            if other_grid.Id in used_grids:
                continue
            
            if other_grid.IsCurved:
                continue
            
            other_crv = other_grid.Curve
            other_p = other_crv.GetEndPoint(0)
            other_q = other_crv.GetEndPoint(1)
            other_dir = (other_p - other_q).Normalize()
            
            if is_parallel(grid_dir, other_dir):
                current_group.append(other_grid)
                used_grids.add(other_grid.Id)
        
        groups.append(current_group)
    
    return groups
```

## Key Techniques

### Parallel Direction Detection
Menggunakan fungsi helper `is_parallel()` yang memeriksa dot product antara dua vektor normal dengan toleransi angular untuk menangani imperfeksi geometri.

### Set-based Tracking
Menggunakan `set` untuk melacak grid yang sudah dikelompokkan, mencegah duplikasi dan memastikan setiap grid hanya dalam satu grup.

### Curve Filtering
Melewati grid melengkung (`IsCurved = True`) karena tidak memiliki arah linier yang dapat dikelompokkan dengan grid lurus.

### Greedy Grouping Algorithm
Algoritma iteratif yang efisien untuk skenario praktis, meskipun kompleksitas waktu O(n²) dalam kasus terburuk.

## Revit API Compatibility

- **Grid.Curve**: Mendapatkan geometri kurva grid
- **Curve.GetEndPoint()**: Mengakses titik akhir untuk menghitung arah
- **XYZ.Normalize()**: Normalisasi vektor untuk perhitungan paralel
- **ElementId**: Tracking unik untuk mencegah duplikasi

Kompatibel dengan Revit 2024 dan 2026 tanpa perubahan API.

## Performance Notes

- **Execution Time**: Medium - O(n²) untuk n grid, tetapi n biasanya kecil (<50) dalam proyek praktis
- **Memory Usage**: Low - hanya menyimpan referensi grid dan set ID
- **Optimization Potential**: Bisa dioptimasi dengan spatial indexing jika n sangat besar

## Usage Examples

### Basic Grid Grouping
```python
# Collect grids from selection or view
grids = uidoc.Selection.GetElementIds().Select(id => doc.GetElement(id)).Where(e => e.Category.Id == BuiltInCategory.OST_Grids)

# Group by direction
grid_groups = group_grids_by_direction(grids)

# Process each group
for group in grid_groups:
    print(f"Group with {len(group)} grids: {[g.Name for g in group]}")
```

### Integration with Dimensioning
```python
# After grouping, create dimensions for each parallel group
for grid_group in grid_groups:
    # Create dimension line for this group
    dimension_line = create_dimension_line_for_group(grid_group)
    # Add dimension to document
```

## Related Logic Entries

- [LOG-UTIL-FILT-001-v1-filter-elements-by-category](logic-library/active/utilities/filtering/LOG-UTIL-FILT-001-v1-filter-elements-by-category.md) - Untuk filtering grid awal
- [LOG-UTIL-GEOM-001-v1-calculate-vector-parallelism](logic-library/active/utilities/geometry/LOG-UTIL-GEOM-001-v1-calculate-vector-parallelism.md) - Fungsi helper is_parallel

## Common Pitfalls

- **Curved Grids**: Pastikan filter grid melengkung, karena mereka tidak memiliki arah linier
- **Zero-length Grids**: Grid dengan panjang nol akan menyebabkan error normalisasi
- **Large Grid Sets**: Untuk >100 grid, pertimbangkan optimasi algoritma

## Production Usage

Digunakan dalam skrip "Dimension Wall with Grid" untuk mengelompokkan grid sebelum membuat dimensi otomatis. Memungkinkan dimensi yang bersih dan terorganisir berdasarkan orientasi grid.