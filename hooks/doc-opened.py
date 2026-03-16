# -*- coding: UTF-8 -*-
from datetime import datetime
from os import path, remove
from pyrevit import revit, forms
from pyrevit.userconfig import user_config
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from customOutput import def_openingLogPath

doc = __eventargs__.Document

# linking IFC models leads to an error because of no document
if doc:
    filePath = doc.PathName
    # getting central file name for log name
    central_path = revit.query.get_central_path(doc)
    fileExtension = filePath[-3:]

    if fileExtension == "rvt":
        # GETTING FILE NAME
        # getting local file name for tmp file name
        try:
            lastBackslash_L = filePath.rindex("\\")
        except:
            # for opened as dettached file
            lastBackslash_L = filePath.rindex("/")

        # just the file name without the extension
        local_file_name = filePath[lastBackslash_L:][:-4]

        # skipped if file is not workshared (when slash is not in filepath)
        try:
            try:
                # for rvt server
                lastBackslash_C = central_path.rindex("/")
            except:
                # for other locations
                lastBackslash_C = central_path.rindex("\\")
            # just the file name without the extension
            central_file_name = central_path[lastBackslash_C:][:-4]
        except:
            central_file_name = local_file_name

        # LOGGING
        # tabulator between data to separate columns of the schedule
        separator = "\t"
        try:
            # reading timestamp from tmp file
            try:
                # if parameter exists in config file
                try:
                    openingLogPath = user_config.PrasKaaToolsSettings.openingLogPath
                # if parameter doesnt exist in config file
                except:
                    openingLogPath = def_openingLogPath

                # Ensure directory exists
                if not os.path.exists(openingLogPath):
                    os.makedirs(openingLogPath, exist_ok=True)

                tmp_file_path = openingLogPath + "\\" + local_file_name + "_Open.tmp"
            except:
                tmp_file_path = " \\\\Srv2\\Z\\customToolslogs\\openingTimeLogs\\" + local_file_name + "_Open.tmp"
            tmp_file = open(tmp_file_path, "r")
            start_time_string = tmp_file.read()
            # converting string to datetime
            start_time = datetime.strptime(start_time_string, "%Y-%m-%d %H:%M:%S")
            tmp_file.close()

            if path.exists(tmp_file_path):
                remove(tmp_file_path)

            end_time_string_seconds = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_time_string_seconds, "%Y-%m-%d %H:%M:%S")

            timeDelta = end_time - start_time

            user_name = doc.Application.Username

            # writing time to log file
            try:
                log_file_path = openingLogPath + "\\" + central_file_name + "_Open.log"
                log_dir = os.path.dirname(log_file_path)
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                log_file = open(log_file_path, "a")
            except:
                log_file_path = "\\\\Srv2\\Z\\customToolslogs\\openingTimeLogs\\" + central_file_name + "_Open.log"
                log_dir = os.path.dirname(log_file_path)
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                log_file = open(log_file_path, "a")
            log_file.write(end_time_string_seconds + separator + str(timeDelta) + separator + user_name + "\n")
            log_file.close()
        except:
            pass

        # ── LastModifiedBy Shared Parameter Binding ───────────────────────────
        from Autodesk.Revit.DB import (
            Transaction, CategorySet, InstanceBinding,
            BuiltInCategory, ExternalDefinitionCreationOptions,
            SpecTypeId, GroupTypeId, ForgeTypeId
        )
        from System import Guid

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

        def _get_current_binding(doc, param_name):
            """Return (InternalDefinition, ElementBinding) jika parameter sudah ter-bind, else (None, None)."""
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
            """Return set of CategoryId yang sudah ter-bind."""
            return set(_eid_val(cat.Id) for cat in binding.Categories)

        def _target_cat_ids(doc):
            """Return set of CategoryId target dari BOUND_CATS."""
            ids = set()
            for bic in BOUND_CATS:
                cat = doc.Settings.Categories.get_Item(bic)
                if cat is not None and cat.AllowsBoundParameters:
                    ids.add(_eid_val(cat.Id))
            return ids

        def ensure_last_modified_by(doc):
            # Skip jika dokumen read-only atau detached
            if doc.IsReadOnly or doc.IsDetached:
                return

            app = doc.Application

            # Cek shared parameter file
            sp_path = app.SharedParametersFilename
            if not sp_path or not os.path.exists(sp_path):
                forms.alert(
                    "Shared Parameter file tidak ditemukan.\n"
                    "Parameter '{}' tidak dapat di-bind.\n\n"
                    "Harap set Shared Parameter file terlebih dahulu di:\n"
                    "Manage → Shared Parameters".format(PARAM_NAME),
                    title="PrasKaa: LastModifiedBy Binding",
                    warn_icon=True
                )
                return

            sp_file = app.OpenSharedParameterFile()
            if sp_file is None:
                forms.alert(
                    "Shared Parameter file tidak dapat dibuka.\n"
                    "Parameter '{}' tidak dapat di-bind.".format(PARAM_NAME),
                    title="PrasKaa: LastModifiedBy Binding",
                    warn_icon=True
                )
                return

            # Cari definition by GUID
            defn = None
            for grp in sp_file.Groups:
                for d in grp.Definitions:
                    if d.GUID == PARAM_GUID:
                        defn = d
                        break
                if defn:
                    break

            if defn is None:
                # GUID tidak ditemukan — cek apakah ada nama sama dengan GUID berbeda (conflict)
                for grp in sp_file.Groups:
                    for d in grp.Definitions:
                        if d.Name.strip().lower() == PARAM_NAME.strip().lower():
                            forms.alert(
                                "Shared Parameter file mengandung parameter '{}'\n"
                                "dengan GUID yang berbeda dari yang diharapkan.\n\n"
                                "GUID di file : {}\n"
                                "GUID expected: {}\n\n"
                                "Harap gunakan Shared Parameter file PrasKaa yang benar.".format(
                                    PARAM_NAME, d.GUID, PARAM_GUID
                                ),
                                title="PrasKaa: GUID Conflict",
                                warn_icon=True
                            )
                            return

                # Tidak ada sama sekali — buat definition baru dengan GUID hardcode
                grp = next((g for g in sp_file.Groups if g.Name == PARAM_GROUP_KEY), None)
                if grp is None:
                    grp = sp_file.Groups.Create(PARAM_GROUP_KEY)
                opts = ExternalDefinitionCreationOptions(PARAM_NAME, SpecTypeId.String.Text)
                opts.GUID = PARAM_GUID
                defn = grp.Definitions.Create(opts)

            # Bangun CategorySet target
            cats = CategorySet()
            for bic in BOUND_CATS:
                cat = doc.Settings.Categories.get_Item(bic)
                if cat is not None and cat.AllowsBoundParameters:
                    cats.Insert(cat)

            binding = InstanceBinding(cats)

            # Cek apakah sudah ter-bind
            existing_defn, existing_binding = _get_current_binding(doc, PARAM_NAME)

            if existing_defn is not None:
                # Sudah ter-bind — cek apakah categories sudah lengkap
                bound_ids  = _bound_cat_ids(existing_binding)
                target_ids = _target_cat_ids(doc)
                if target_ids.issubset(bound_ids):
                    return  # sudah lengkap, skip
                # Partial bind — ReInsert dengan categories lengkap
                t = Transaction(doc, "PrasKaa: ReInsert LastModifiedBy binding")
                t.Start()
                try:
                    doc.ParameterBindings.ReInsert(defn, binding, ForgeTypeId(""))
                    t.Commit()
                except Exception as e:
                    t.RollBack()
            else:
                # Belum ter-bind sama sekali — Insert baru
                t = Transaction(doc, "PrasKaa: Bind LastModifiedBy")
                t.Start()
                try:
                    doc.ParameterBindings.Insert(defn, binding, ForgeTypeId(""))
                    t.Commit()
                except Exception as e:
                    t.RollBack()

        try:
            ensure_last_modified_by(doc)
        except:
            pass
        # ─────────────────────────────────────────────────────────────────────