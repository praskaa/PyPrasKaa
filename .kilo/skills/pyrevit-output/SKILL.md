---
name: pyrevit-output-window
description: Expert guide for writing pyRevit scripts that use the output window (PyRevitOutputWindow). Use this skill whenever the user asks to display results, tables, charts, progress bars, markdown, HTML, or styled output inside a pyRevit output window. Trigger on phrases like: "tampilkan hasil di output", "print ke output window", "bikin tabel di pyrevit output", "progress bar pyrevit", "chart di output", "linkify element", "print_md", "print_table", "print_html", "log_error", "update_progress", or any request that involves displaying script results to the user via pyRevit's built-in HTML output panel. Also trigger for any pyRevit script where the output presentation is a key concern, even if the user doesn't explicitly say "output window".
---

# pyRevit Output Window Skill

Panduan lengkap menulis script pyRevit yang menggunakan `PyRevitOutputWindow` —
output panel HTML bawaan pyRevit untuk menampilkan hasil analisis, tabel, grafik, progress, dan lainnya.

## Setup Wajib

```python
from pyrevit import script
output = script.get_output()
```

Jangan import `pyrevit.output` langsung — selalu gunakan `script.get_output()`.

---

## Kategori Output & Kapan Memilihnya

| Kebutuhan | Method | Catatan |
|---|---|---|
| Teks biasa | `print(...)` | IronPython print biasa |
| Markdown | `output.print_md(md_str)` | Heading, bold, italic, list, tabel MD |
| HTML mentah | `output.print_html(html_str)` | Bebas gunakan HTML tag |
| Tabel data (cepat) | `output.print_table(...)` | Render via markdown |
| Tabel data (advanced) | `output.print_html_table(...)` | Full CSS control |
| Kode / snippet | `output.print_code(code_str)` | Monospace, background abu |
| Gambar | `output.print_image(img_path)` | Path lokal |
| Grafik / Chart | `output.make_*_chart(...)` | Line, bar, pie, doughnut, radar, dll |
| Divider | `output.insert_divider()` | Garis pemisah horizontal |
| Ganti halaman | `output.next_page()` | Break konten baru |
| Link ke elemen Revit | `output.linkify(element_id)` | Klik → select element |

---

## Pola Umum

### Print Markdown (paling sering dipakai)
```python
output.print_md('## Hasil Analisis')
output.print_md('**Total elemen:** {}'.format(count))
output.print_md('- Item A\n- Item B\n- Item C')
```

### Print Tabel Sederhana
```python
data = [
    ['Kolom A', 'Kolom B', 100],
    ['Kolom C', 'Kolom D', 200],
]
output.print_table(
    table_data=data,
    title="Judul Tabel",
    columns=["Nama", "Info", "Nilai"],
    formats=['', '', '{}px'],
    last_line_style='color:red;'
)
```

### Print Tabel HTML (lebih kaya styling)
```python
data = [['Beam', 'W200x100', 'OK'], ['Column', 'UC203', 'WARNING']]
output.print_html_table(
    table_data=data,
    title="Structural Check",
    columns=["Type", "Section", "Status"],
    formats=['', '', ''],
    column_widths=["150px", "150px", "100px"],
    col_data_align_styles=["left", "left", "center"],
    column_vertical_border_style="border: 1px solid #ccc",
    table_width_style='width:100%',
    row_striping=True,
    repeat_head_as_foot=False
)
```

### Progress Bar
```python
elements = FilteredElementCollector(doc).OfClass(Wall).ToElements()
for i, el in enumerate(elements):
    output.update_progress(i, len(elements))
    # ... proses elemen
output.hide_progress()
```

### Progress Indeterminate (untuk proses tak diketahui durasinya)
```python
output.indeterminate_progress(True)
# ... proses berat
output.indeterminate_progress(False)
```

### Log Panel (status di bagian bawah window)
```python
output.log_info("Memulai proses...")
output.log_success("Selesai: {} elemen diproses".format(count))
output.log_warning("Ada {} elemen yang dilewati".format(skipped))
output.log_error("Gagal pada elemen ID: {}".format(failed_id))
```

### Linkify (klik langsung select element di Revit)
```python
from pyrevit import script
output = script.get_output()

for wall in walls:
    link = output.linkify(wall.Id)
    output.print_md('Wall: {} → {}'.format(wall.Id, link))
```

Catatan: `linkify` mengembalikan HTML string. Gunakan di dalam `print_html` atau `print_md`.

---

## Window Management

```python
output.set_title("Laporan Struktur")
output.resize(800, 600)           # lebar, tinggi (px)
output.center()                    # posisikan di tengah layar
output.lock_size()                 # cegah user resize
output.self_destruct(30)           # tutup otomatis setelah N detik
output.close_others()              # tutup output window lain dari command yang sama
output.save_contents(r"C:\laporan.html")  # simpan output ke file HTML
```

---

## Charts

Semua chart menggunakan Chart.js di belakangnya. Return `chart` object, lalu panggil `draw()`.

```python
# Bar Chart
chart = output.make_bar_chart()
chart.options.title = {'display': True, 'text': 'Jumlah per Lantai'}
dataset = chart.data.new_dataset('Balok')
dataset.data = [10, 25, 15, 30]
chart.set_labels(['L1', 'L2', 'L3', 'L4'])
chart.draw()

# Pie Chart
chart = output.make_pie_chart()
dataset = chart.data.new_dataset('Material')
dataset.data = [40, 35, 25]
dataset.backgroundColor = ['#FF6384', '#36A2EB', '#FFCE56']
chart.set_labels(['Beton', 'Baja', 'Precast'])
chart.draw()

# Line Chart
chart = output.make_line_chart()
dataset = chart.data.new_dataset('Defleksi')
dataset.data = [0, 2.5, 5.1, 4.8, 3.2]
chart.set_labels(['P0', 'P1', 'P2', 'P3', 'P4'])
chart.draw()
```

Chart types tersedia: `make_line_chart`, `make_bar_chart`, `make_stacked_chart`,
`make_radar_chart`, `make_polar_chart`, `make_pie_chart`, `make_doughnut_chart`, `make_bubble_chart`.

---

## Custom Styling

```python
# Inject CSS custom
output.add_style('''
    body { font-family: "Segoe UI", sans-serif; }
    table { border-collapse: collapse; }
    .error-row { color: red; font-weight: bold; }
''')

# Inject JavaScript (jarang dipakai, untuk kasus advanced)
output.inject_script('console.log("pyRevit output loaded")')
```

---

## Freeze / Unfreeze (performa)

Untuk output yang banyak, freeze dulu agar tidak flicker:

```python
output.freeze()
for item in large_list:
    output.print_md('- {}'.format(item))
output.unfreeze()
```

---

## Template Script Lengkap

```python
# -*- coding: utf-8 -*-
__title__ = 'Nama Tool'
__doc__ = 'Deskripsi singkat tool ini'

from pyrevit import script, revit, DB
from Autodesk.Revit.DB import FilteredElementCollector

doc = revit.doc
output = script.get_output()

# Setup window
output.set_title("Laporan: {}".format(doc.Title))
output.resize(900, 700)

# Header
output.print_md('# {}'.format(__title__))
output.insert_divider()

# Kumpul data
walls = FilteredElementCollector(doc).OfClass(DB.Wall).ToElements()
data = []
for i, wall in enumerate(walls):
    output.update_progress(i, len(walls))
    try:
        data.append([
            wall.Id.IntegerValue,
            wall.Name,
            '{:.2f}'.format(wall.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH).AsDouble())
        ])
    except Exception as e:
        output.log_warning("Skip wall {}: {}".format(wall.Id, str(e)))

output.hide_progress()

# Output tabel
if data:
    output.print_html_table(
        table_data=data,
        title="Daftar Wall",
        columns=["ID", "Tipe", "Panjang (ft)"],
        column_widths=["80px", "250px", "120px"],
        row_striping=True
    )
    output.log_success("Selesai: {} wall diproses".format(len(data)))
else:
    output.print_md('> **Tidak ada data ditemukan.**')
    output.log_warning("Tidak ada wall di model")
```

---

## Gotchas & Tips

- `print_md` dan `print_table` adalah static method — bisa dipanggil tanpa `self` tapi tetap lewat instance
- `linkify` return HTML string, bukan langsung print — embed ke `print_html` atau `print_md` dengan `{}`.format
- `log_*` methods otomatis `show_logpanel()` — tidak perlu panggil manual
- Untuk tabel panjang (>50 baris), gunakan `print_html_table` dengan `repeat_head_as_foot=True`
- `self_destruct(seconds)` cocok untuk laporan informatif yang tidak perlu dibiarkan terbuka
- `output.freeze()` + `output.unfreeze()` sangat penting untuk loop besar agar UI tidak patah-patah
- `print_code(code_str)` otomatis replace spasi dengan `&nbsp;` — tidak perlu escape manual
