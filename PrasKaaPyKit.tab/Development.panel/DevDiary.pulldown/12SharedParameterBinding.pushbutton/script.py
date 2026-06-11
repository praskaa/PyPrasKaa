# -*- coding: utf-8 -*-
"""
FixLastModifiedByBinding.py
Manually bind / fix categories untuk parameter 'LastModifiedBy'.
Author : PrasKaa
"""
import os
from Autodesk.Revit.DB import (
    Transaction, CategorySet, InstanceBinding,
    BuiltInCategory, ExternalDefinitionCreationOptions,
    SpecTypeId, GroupTypeId, ForgeTypeId
)
from System import Guid
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document
app = __revit__.Application

PARAM_NAME      = "LastModifiedBy"
PARAM_GUID      = Guid("f9e795ba-738a-4fb8-984a-093a72d56c53")
PARAM_GROUP_KEY = "PrasKaaParams"

BOUND_CATS = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_Stairs,
    BuiltInCategory.OST_Views,
    BuiltInCategory.OST_Sheets,
]

# ── helpers ───────────────────────────────────────────────────

def _get_current_binding(doc, param_name):
    it = doc.ParameterBindings.ForwardIterator()
    it.Reset()
    while it.MoveNext():
        if it.Key.Name.strip().lower() == param_name.strip().lower():
            return it.Key, it.Current
    return None, None

def _eid_val(eid):
    try:
        return eid.Value
    except AttributeError:
        return eid.IntegerValue

def _bound_cat_ids(binding):
    return set(_eid_val(cat.Id) for cat in binding.Categories)

def _target_cat_ids(doc):
    ids = set()
    for bic in BOUND_CATS:
        cat = doc.Settings.Categories.get_Item(bic)
        if cat is not None and cat.AllowsBoundParameters:
            ids.add(_eid_val(cat.Id))
    return ids

# ── guard ─────────────────────────────────────────────────────

if doc.IsReadOnly or doc.IsDetached:
    forms.alert(
        "Dokumen read-only atau detached.\nBinding tidak dapat dilakukan.",
        title="PrasKaa: Fix Binding",
        warn_icon=True
    )
    script.exit()

# ── cek shared param file ─────────────────────────────────────

sp_path = app.SharedParametersFilename
if not sp_path or not os.path.exists(sp_path):
    forms.alert(
        "Shared Parameter file tidak ditemukan.\n\n"
        "Harap set Shared Parameter file terlebih dahulu di:\n"
        "Manage → Shared Parameters",
        title="PrasKaa: Fix Binding",
        warn_icon=True
    )
    script.exit()

sp_file = app.OpenSharedParameterFile()
if sp_file is None:
    forms.alert(
        "Shared Parameter file tidak dapat dibuka.",
        title="PrasKaa: Fix Binding",
        warn_icon=True
    )
    script.exit()

# ── cari definition by GUID ───────────────────────────────────

defn = None
for grp in sp_file.Groups:
    for d in grp.Definitions:
        if d.GUID == PARAM_GUID:
            defn = d
            break
    if defn:
        break

if defn is None:
    # cek GUID conflict
    for grp in sp_file.Groups:
        for d in grp.Definitions:
            if d.Name.strip().lower() == PARAM_NAME.strip().lower():
                forms.alert(
                    "Parameter '{}' ditemukan di shared param file\n"
                    "tapi GUID berbeda!\n\n"
                    "GUID di file  : {}\n"
                    "GUID expected : {}\n\n"
                    "Harap gunakan Shared Parameter file PrasKaa yang benar.".format(
                        PARAM_NAME, d.GUID, PARAM_GUID
                    ),
                    title="PrasKaa: GUID Conflict",
                    warn_icon=True
                )
                script.exit()

    # tidak ada sama sekali — buat baru
    grp = next((g for g in sp_file.Groups if g.Name == PARAM_GROUP_KEY), None)
    if grp is None:
        grp = sp_file.Groups.Create(PARAM_GROUP_KEY)
    opts = ExternalDefinitionCreationOptions(PARAM_NAME, SpecTypeId.String.Text)
    opts.GUID = PARAM_GUID
    defn = grp.Definitions.Create(opts)

# ── bangun CategorySet ────────────────────────────────────────

cats = CategorySet()
for bic in BOUND_CATS:
    cat = doc.Settings.Categories.get_Item(bic)
    if cat is not None and cat.AllowsBoundParameters:
        cats.Insert(cat)

binding = InstanceBinding(cats)

# ── cek existing binding ──────────────────────────────────────

existing_defn, existing_binding = _get_current_binding(doc, PARAM_NAME)

output = script.get_output()
output.print_md("# Fix: LastModifiedBy Binding\n")

if existing_defn is not None:
    bound_ids  = _bound_cat_ids(existing_binding)
    target_ids = _target_cat_ids(doc)

    if target_ids.issubset(bound_ids):
        output.print_md("**[OK]** Semua categories sudah ter-bind. Tidak ada yang perlu di-fix.")
        script.exit()

    missing_names = []
    for bic in BOUND_CATS:
        cat = doc.Settings.Categories.get_Item(bic)
        if cat and _eid_val(cat.Id) not in bound_ids:
            missing_names.append(cat.Name)

    output.print_md("**[!!]** Partial bind terdeteksi. Categories belum ter-bind:")
    for m in missing_names:
        output.print_md("- {}".format(m))
    output.print_md("\nMenjalankan **ReInsert**...")

    t = Transaction(doc, "PrasKaa: ReInsert LastModifiedBy binding")
    t.Start()
    try:
        doc.ParameterBindings.ReInsert(defn, binding, ForgeTypeId(""))
        t.Commit()
        output.print_md("\n**[OK]** ReInsert berhasil. Semua categories sekarang ter-bind.")
    except Exception as e:
        t.RollBack()
        output.print_md("\n**[!!]** ReInsert gagal: {}".format(str(e)))

else:
    output.print_md("**[!!]** Parameter belum ter-bind sama sekali. Menjalankan **Insert**...")

    t = Transaction(doc, "PrasKaa: Bind LastModifiedBy")
    t.Start()
    try:
        doc.ParameterBindings.Insert(defn, binding, ForgeTypeId(""))
        t.Commit()
        output.print_md("\n**[OK]** Insert berhasil. Parameter sekarang ter-bind.")
    except Exception as e:
        t.RollBack()
        output.print_md("\n**[!!]** Insert gagal: {}".format(str(e)))