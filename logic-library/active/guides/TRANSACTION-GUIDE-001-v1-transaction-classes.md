# Panduan Kelas Transaksi (Transaction Classes)

## Pendahuluan

Kelas transaksi di Revit API adalah komponen penting untuk melakukan perubahan pada model. Ada tiga jenis utama: `Transaction`, `SubTransaction`, dan `TransactionGroup`. Semua kelas ini berbagi metode umum dan status yang sama.

## Metode Umum Kelas Transaksi

Ketiga objek transaksi berbagi metode umum berikut:

| Metode | Deskripsi |
|--------|-----------|
| Start | Memulai konteks transaksi |
| Commit | Mengakhiri konteks dan melakukan semua perubahan ke dokumen |
| Rollback | Mengakhiri konteks dan membuang semua perubahan ke dokumen |
| GetStatus | Mengembalikan status saat ini dari objek transaksi |

Selain metode `GetStatus()` yang mengembalikan status saat ini, metode `Start`, `Commit`, dan `Rollback` juga mengembalikan `TransactionStatus` yang menunjukkan apakah metode berhasil atau tidak.

## Nilai TransactionStatus

Nilai `TransactionStatus` yang tersedia meliputi:

| Status | Deskripsi |
|--------|-----------|
| Uninitialized | Nilai awal setelah objek diinstansiasi; konteks belum dimulai |
| Started | Objek transaksi berhasil dimulai (Start dipanggil) |
| RolledBack | Objek transaksi berhasil di-rollback (Rollback dipanggil) |
| Committed | Objek transaksi berhasil di-commit (Commit dipanggil) |
| Pending | Objek transaksi dicoba untuk dikirim atau di-rollback, tetapi karena kegagalan yang proses tidak dapat diselesaikan dan sedang menunggu respons pengguna akhir (dalam dialog modeless). Setelah pemrosesan kegagalan selesai, status akan diperbarui secara otomatis (ke status Committed atau RolledBack). |

## Transaction

Transaksi adalah konteks yang diperlukan untuk membuat perubahan apa pun pada model Revit. Hanya satu transaksi yang dapat dibuka pada satu waktu; nesting tidak diizinkan. Setiap transaksi harus memiliki nama, yang akan tercantum di menu Undo di Revit setelah transaksi berhasil di-commit.

### Contoh Penggunaan Transaksi

```csharp
public void CreatingModelLines(UIApplication uiApplication)
{
    Autodesk.Revit.DB.Document document = uiApplication.ActiveUIDocument.Document;
    Autodesk.Revit.ApplicationServices.Application application = uiApplication.Application;

    // Buat beberapa garis geometri. Garis-garis ini bukan elemen,
    // oleh karena itu tidak perlu dibuat di dalam transaksi dokumen.
    XYZ Point1 = XYZ.Zero;
    XYZ Point2 = new XYZ(10, 0, 0);
    XYZ Point3 = new XYZ(10, 10, 0);
    XYZ Point4 = new XYZ(0, 10, 0);

    Line geomLine1 = Line.CreateBound(Point1, Point2);
    Line geomLine2 = Line.CreateBound(Point4, Point3);
    Line geomLine3 = Line.CreateBound(Point1, Point4);

    // Bidang geometri ini juga transaksi dan tidak memerlukan transaksi
    XYZ origin = XYZ.Zero;
    XYZ normal = new XYZ(0, 0, 1);
    Plane geomPlane = Plane.CreateByNormalAndOrigin(normal, origin);

    // Untuk membuat sketch plane dengan kurva model di dalamnya, kita perlu
    // memulai transaksi karena operasi seperti itu memodifikasi model.

    // Semua dan transaksi apa pun harus diapit dalam blok 'using'
    // atau dijaga dalam blok try-catch-finally
    // untuk menjamin bahwa transaksi tidak out-live scope-nya.
    using (Transaction transaction = new Transaction(document))
    {
        if (transaction.Start("Create model curves") == TransactionStatus.Started)
        {
            // Buat sketch plane di dokumen saat ini
            SketchPlane sketch = SketchPlane.Create(document, geomPlane);

            // Buat elemen ModelLine menggunakan garis geometri dan sketch plane
            ModelLine line1 = document.Create.NewModelCurve(geomLine1, sketch) as ModelLine;
            ModelLine line2 = document.Create.NewModelCurve(geomLine2, sketch) as ModelLine;
            ModelLine line3 = document.Create.NewModelCurve(geomLine3, sketch) as ModelLine;

            // Tanyakan kepada pengguna akhir apakah perubahan akan di-commit atau tidak
            TaskDialog taskDialog = new TaskDialog("Revit");
            taskDialog.MainContent = "Klik [OK] untuk Commit, atau [Cancel] untuk Roll back transaksi.";
            TaskDialogCommonButtons buttons = TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel;
            taskDialog.CommonButtons = buttons;

            if (TaskDialogResult.Ok == taskDialog.Show())
            {
                // Untuk berbagai alasan, transaksi mungkin tidak dapat di-commit
                // jika perubahan yang dibuat selama transaksi tidak menghasilkan model yang valid.
                // Jika commit transaksi gagal atau dibatalkan oleh pengguna akhir,
                // status yang dihasilkan akan menjadi RolledBack alih-alih Committed.
                if (TransactionStatus.Committed != transaction.Commit())
                {
                    TaskDialog.Show("Failure", "Transaksi tidak dapat di-commit");
                }
            }
            else
            {
                transaction.RollBack();
            }
        }
    }
}
```

## SubTransaction

`SubTransaction` dapat digunakan untuk melampirkan satu set operasi modifikasi model. Sub-transaksi bersifat opsional. Mereka tidak diperlukan untuk memodifikasi model. Mereka adalah alat kemudahan untuk memungkinkan pemisahan logis tugas yang lebih besar menjadi yang lebih kecil. Sub-transaksi hanya dapat dibuat dalam transaksi yang sudah dibuka dan harus ditutup (di-commit atau di-rollback) sebelum transaksi ditutup (di-commit atau di-rollback). Tidak seperti transaksi, sub-transaksi dapat di-nest, tetapi sub-transaksi yang di-nest apa pun harus ditutup sebelum sub-transaksi yang melingkupinya ditutup. Sub-transaksi tidak memiliki nama, karena mereka tidak muncul di menu Undo di Revit.

## TransactionGroup

`TransactionGroup` memungkinkan pengelompokan bersama beberapa transaksi independen, yang memberikan pemilik grup kesempatan untuk menangani banyak transaksi sekaligus. Ketika grup transaksi akan ditutup, grup tersebut dapat di-rollback, yang berarti bahwa semua transaksi yang sebelumnya di-commit yang termasuk dalam grup akan di-rollback. Jika tidak di-rollback, grup dapat di-commit atau diasimilasi. Dalam kasus pertama, semua transaksi yang di-commit (dalam grup) akan dibiarkan seperti apa adanya. Dalam kasus terakhir, transaksi dalam grup akan digabungkan bersama menjadi satu transaksi yang akan memiliki nama grup.

Grup transaksi hanya dapat dimulai ketika tidak ada transaksi yang terbuka, dan harus ditutup hanya setelah semua transaksi yang terlampir ditutup (di-rollback atau di-commit). Grup transaksi dapat di-nest, tetapi grup yang di-nest apa pun harus ditutup sebelum grup yang melingkupinya ditutup. Grup transaksi bersifat opsional. Mereka tidak diperlukan untuk membuat modifikasi pada model.

### Contoh Penggunaan TransactionGroup

```csharp
public void CompoundOperation(Autodesk.Revit.DB.Document document)
{
    // Semua dan grup transaksi apa pun harus diapit dalam blok 'using' atau dijaga dalam
    // blok try-catch-finally untuk menjamin bahwa grup tidak out-live scope-nya.
    using (TransactionGroup transGroup = new TransactionGroup(document, "Level and Grid"))
    {
        if (transGroup.Start() == TransactionStatus.Started)
        {
            // Kita akan memanggil dua metode, masing-masing memiliki transaksi lokal.
            // Untuk operasi majemuk kita dianggap berhasil, kedua transaksi
            // individu harus berhasil. Jika salah satu gagal, kita akan roll back grup kita,
            // terlepas dari transaksi apa pun yang mungkin sudah di-commit.

            if (CreateLevel(document, 25.0) && CreateGrid(document, new XYZ(0,0,0), new XYZ(10,0,0)))
            {
                // Proses asimilasi akan menggabungkan dua (atau lebih) transaksi yang di-commit
                // bersama dan akan menetapkan nama grid ke transaksi yang dihasilkan satu,
                // yang akan menjadi satu-satunya item dari operasi majemuk ini yang muncul di menu undo.
                transGroup.Assimilate();
            }
            else
            {
                // Karena kita tidak dapat berhasil menyelesaikan setidaknya satu operasi
                // individu, kita akan roll back seluruh grup, yang akan
                // undo transaksi apa pun yang sudah di-commit saat grup ini terbuka.
                transGroup.RollBack();
            }
        }
    }
}

public bool CreateLevel(Autodesk.Revit.DB.Document document, double elevation)
{
    // Semua dan transaksi apa pun harus diapit dalam blok 'using'
    // blok atau dijaga dalam blok try-catch-finally untuk menjamin bahwa transaksi tidak out-live scope-nya.
    using (Transaction transaction = new Transaction(document, "Creating Level"))
    {
        // Harus memulai transaksi untuk dapat memodifikasi dokumen

        if( TransactionStatus.Started == transaction.Start())
        {
            if (null != Level.Create(document, elevation))
            {
                // Untuk berbagai alasan, transaksi mungkin tidak dapat di-commit
                // jika perubahan yang dibuat selama transaksi tidak menghasilkan model yang valid.
                // Jika commit transaksi gagal atau dibatalkan oleh pengguna akhir,
                // status yang dihasilkan akan menjadi RolledBack alih-alih Committed.
                return (TransactionStatus.Committed == transaction.Commit());
            }

            // Karena kita tidak dapat membuat level, kita akan roll back transaksi
            // (meskipun pada kasus yang disederhanakan ini kita tahu tidak ada perubahan lain)

            transaction.RollBack();
        }
    }
    return false;
}

public bool CreateGrid(Autodesk.Revit.DB.Document document, XYZ p1, XYZ p2)
{
    // Semua dan transaksi apa pun harus diapit dalam blok 'using'
    // blok atau dijaga dalam blok try-catch-finally untuk menjamin bahwa transaksi tidak out-live scope-nya.
    using (Transaction transaction = new Transaction(document, "Creating Grid"))
    {
        // Harus memulai transaksi untuk dapat memodifikasi dokumen
        if (TransactionStatus.Started == transaction.Start())
        {
            // Kita membuat garis dan menggunakannya sebagai argumen untuk membuat grid
            Line gridLine = Line.CreateBound(p1, p2);

            if ((null != gridLine) && (null != Grid.Create(document, gridLine)))
            {
                if (TransactionStatus.Committed == transaction.Commit())
                {
                return true;
                }
            }

            // Karena kita tidak dapat membuat grid, kita akan roll back transaksi
            // (meskipun pada kasus yang disederhanakan ini kita tahu tidak ada perubahan lain)

            transaction.RollBack();
        }
    }
    return false;
}
```

## Transaksi dalam Event

### Memodifikasi dokumen selama event

Event tidak secara otomatis membuka transaksi. Oleh karena itu, dokumen tidak akan dimodifikasi selama event kecuali handler event memodifikasi dokumen dengan membuat perubahan di dalam transaksi. Jika handler event membuka transaksi, diperlukan bahwa handler tersebut juga menutupnya (commit atau roll back), jika tidak semua perubahan akan dibuang.

Harap diperhatikan bahwa modifikasi dokumen aktif tidak diizinkan selama beberapa event (misalnya event DocumentClosing). Jika handler event mencoba membuat modifikasi selama event tersebut, pengecualian akan dilempar. Dokumentasi event menunjukkan apakah event tersebut read-only atau tidak.

### Event DocumentChanged

Event DocumentChanged dimunculkan setelah setiap transaksi mendapat commit, undo, atau redo. Ini adalah event read-only, dirancang untuk memungkinkan Anda menjaga data eksternal tetap sinkron dengan status database Revit. Untuk memperbarui database Revit sebagai respons terhadap perubahan di elemen, gunakan framework Dynamic Model Update.

## Opsi Penanganan Kegagalan (Failure Handling Options)

Opsi penanganan kegagalan adalah opsi untuk bagaimana kegagalan, jika ada, harus ditangani pada akhir transaksi. Opsi penanganan kegagalan dapat diatur kapan saja sebelum memanggil `Transaction.Commit()` atau `Transaction.RollBack()` menggunakan metode `Transaction.SetFailureHandlingOptions()`. Namun, setelah transaksi di-commit atau di-rollback, opsi kembali ke pengaturan default masing-masing.

Metode `SetFailureHandlingOptions()` mengambil objek `FailureHandlingOptions` sebagai parameter. Objek ini tidak dapat dibuat, harus diperoleh dari transaksi menggunakan metode `GetFailureHandlingOptions()`. Opsi diatur dengan memanggil metode Set yang sesuai, seperti `SetClearAfterRollback()`. Bagian berikut membahas opsi penanganan kegagalan secara lebih detail.

### ClearAfterRollback

Opsi ini mengontrol apakah semua peringatan harus dihapus setelah transaksi di-rollback. Nilai default adalah False.

### DelayedMiniWarnings

Opsi ini mengontrol apakah mini-warnings, jika ada, ditampilkan pada akhir transaksi yang sedang diakhiri, atau jika mereka harus ditunda hingga akhir transaksi berikutnya. Ini biasanya digunakan dalam rantai transaksi ketika tidak diinginkan untuk menampilkan peringatan perantara pada akhir setiap langkah, tetapi lebih suka menunggu hingga penyelesaian seluruh rantai.

Peringatan dapat ditunda untuk lebih dari satu transaksi. Transaksi pertama yang tidak memiliki opsi ini disetel ke True akan menampilkan peringatan sendiri, jika ada, serta peringatan apa pun yang mungkin telah terakumulasi dari transaksi sebelumnya. Nilai default adalah False.

Catatan: Opsi ini diabaikan dalam mode modal (lihat ForcedModalHandling di bawah).

### ForcedModalHandling

Opsi ini mengontrol apakah kegagalan yang terjadi akan ditangani secara modal atau modeless. Default adalah True. Perlu diperhatikan bahwa jika penanganan kegagalan modeless disetel, pemrosesan transaksi mungkin dilakukan secara asinkron, yang berarti bahwa setelah kembali dari panggilan Commit atau RollBack, transaksi belum selesai (status akan menjadi 'Pending').

### SetFailuresPreprocessor

Interface ini, jika disediakan, dipanggil ketika ada kegagalan yang ditemukan pada akhir transaksi. Preprocessor dapat memeriksa kegagalan saat ini dan bahkan mencoba menyelesaikannya. Lihat Posting dan Penanganan Kegagalan untuk informasi lebih lanjut.

### SetTransactionFinalizer

Finalizer adalah interface, yang jika disediakan, dapat digunakan untuk melakukan tindakan kustom pada akhir transaksi. Perlu diperhatikan bahwa finalizer tidak dipanggil ketika metode Commit() atau RollBack() dipanggil, tetapi hanya setelah proses commit atau rollback selesai. Finalizer transaksi harus mengimplementasikan interface `ITransactionFinalizer`, yang memerlukan dua fungsi untuk didefinisikan:

- OnCommitted - dipanggil pada akhir commit transaksi
- OnRolledBack - dipanggil pada akhir rollback transaksi

Catatan: Karena finalizer dipanggil setelah transaksi selesai, dokumen tidak dapat dimodifikasi dari finalizer kecuali transaksi baru dimulai.

## Mendapatkan Geometri Elemen dan AnalyticalElement

Setelah elemen baru dibuat atau elemen dimodifikasi, regenerasi dan auto-joining elemen diperlukan untuk menyebarkan perubahan di seluruh model. Tanpa regenerasi (dan auto-join, ketika relevan), properti Geometry dan AnalyticalElement untuk Elements mungkin tidak dapat diperoleh (dalam kasus membuat elemen baru) atau mungkin tidak valid. Penting untuk memahami bagaimana dan kapan regenerasi terjadi sebelum mengakses Geometry atau AnalyticalElement dari Element.

Meskipun regenerasi dan auto-joining diperlukan untuk menyebarkan perubahan yang dibuat di model, ini dapat memakan waktu. Adalah terbaik jika event ini terjadi hanya sesering yang diperlukan.

Regenerasi dan auto-joining terjadi secara otomatis ketika transaksi yang memodifikasi model di-commit dengan sukses, atau setiap kali metode `Document.Regenerate()` atau `Document.AutoJoinElements()` dipanggil. Regenerate() dan AutoJoinElements() hanya dapat dipanggil di dalam transaksi terbuka. Perlu diperhatikan bahwa metode Regeneration() dapat gagal, dalam hal ini pengecualian RegenerationFailedException akan dilempar. Jika ini terjadi, perubahan ke dokumen perlu di-rollback dengan rollback transaksi saat ini atau subtransaksi.

Untuk informasi lebih lanjut, lihat Analytical Element dan Geometry.

### Contoh Program

```csharp
public void TransactionDuringElementCreation(UIApplication uiApplication, Level level)
{
    Autodesk.Revit.DB.Document document = uiApplication.ActiveUIDocument.Document;

    // Bangun lokasi garis untuk pembuatan dinding
    XYZ start = new XYZ(0, 0, 0);
    XYZ end = new XYZ(10, 10, 0);
    Autodesk.Revit.DB.Line geomLine = Line.CreateBound(start, end);

    // Semua dan transaksi apa pun harus diapit dalam blok 'using'
    // blok atau dijaga dalam blok try-catch-finally untuk menjamin bahwa transaksi tidak out-live scope-nya.
    using (Transaction wallTransaction = new Transaction(document, "Creating wall"))
    {
       // Untuk membuat dinding, transaksi harus dimulai terlebih dahulu
       if (wallTransaction.Start() == TransactionStatus.Started)
       {
           // Buat dinding menggunakan lokasi garis
           Wall wall = Wall.Create(document, geomLine, level.Id, true);

           // transaksi harus di-commit sebelum Anda dapat
           // mendapatkan nilai Geometry dan AnalyticalPanel.

           if (wallTransaction.Commit() == TransactionStatus.Committed)
           {
               Autodesk.Revit.DB.Options options = uiApplication.Application.Create.NewGeometryOptions();
               Autodesk.Revit.DB.GeometryElement geoelem = wall.get_Geometry(options);
               Autodesk.Revit.DB.Structure.AnalyticalPanel analyticalPanel = (AnalyticalPanel)document.GetElement(AnalyticalToPhysicalAssociationManager.GetAnalyticalToPhysicalAssociationManager(document).GetAssociatedElementId(wall.Id));
           }
       }
    }
}
```

Timeline transaksi untuk contoh ini adalah sebagai berikut:

[Diagram timeline transaksi]

## Transaksi Sementara

Tidak selalu diperlukan untuk commit transaksi. Framework transaksi juga memungkinkan Transaksi untuk di-rollback. Ini berguna ketika ada kesalahan selama pemrosesan transaksi, tetapi juga dapat dimanfaatkan langsung sebagai teknik untuk membuat transaksi sementara.

Menggunakan transaksi sementara dapat berguna untuk jenis analisis tertentu. Misalnya, aplikasi yang mencari mengekstrak properti geometris dari dinding atau objek lain sebelum dipotong oleh bukaan harus menggunakan transaksi sementara dalam kombinasi dengan `Document.Delete()`. Ketika aplikasi menghapus elemen yang memotong elemen target, geometri elemen cut dipulihkan ke keadaan aslinya (setelah dokumen diregenerasi).

Untuk menggunakan transaksi sementara:

1. Instansiasi Transaction menggunakan konstruktor Transaction, dan tetapkan nama.
2. Panggil `Transaction.Start()`
3. Buat perubahan sementara ke dokumen (modifikasi elemen, penghapusan atau pembuatan)
4. Regenerasi dokumen
5. Ekstrak properti geometri dan yang diinginkan
6. Panggil `Transaction.RollBack()` untuk mengembalikan dokumen ke keadaan sebelumnya.

Teknik ini juga berlaku untuk SubTransactions.

---

**Catatan untuk Pengembang pyRevit:** Dokumentasi ini didasarkan pada Revit API .NET. Untuk implementasi Python di pyRevit, gunakan modul `Transaction` dari `Autodesk.Revit.DB`. Pastikan untuk menggunakan konteks `with` atau try-finally untuk memastikan transaksi ditutup dengan benar. Lihat contoh skrip PrasKaaPykit untuk pola penggunaan yang benar.