# -*- coding: utf-8 -*-
"""
Merge Material
Merge material A ke material B dan update semua element yang menggunakan material A
Compatible dengan Revit 2024-2026
"""

__title__ = 'Merge\nMaterial'
__author__ = 'PrasKaa Team'
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Merge material A ke material B dan update semua element yang menggunakan material A.
Compatible dengan Revit 2024-2026.

How-to:
1. Click the tool button
2. Select Material A (sumber/yang akan diganti)
3. Select Material B (target/yang akan dipakai)
4. Konfirmasi action
5. Semua element dengan Material A akan diubah ke Material B
6. Material A akan dihapus

Notes:
- Requires both materials to exist in the project
- Updates all elements that use the source material
- Deletes the source material after merge

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import revit, forms, script

doc = revit.doc
uidoc = revit.uidoc

def get_all_materials():
    """Mendapatkan semua material di dokumen"""
    collector = FilteredElementCollector(doc).OfClass(Material)
    materials = list(collector)
    return sorted(materials, key=lambda m: m.Name)

def get_elements_with_material(material_id):
    """Mendapatkan semua element yang menggunakan material tertentu"""
    elements = []
    
    # Cek semua element yang bisa punya material
    collectors = [
        FilteredElementCollector(doc).OfClass(FamilyInstance),
        FilteredElementCollector(doc).OfClass(Wall),
        FilteredElementCollector(doc).OfClass(Floor),
        FilteredElementCollector(doc).OfClass(RoofBase),
        FilteredElementCollector(doc).OfClass(Ceiling),
        FilteredElementCollector(doc).OfClass(HostObjAttributes)
    ]
    
    for collector in collectors:
        for elem in collector:
            try:
                # Cek material id parameter
                mat_param = elem.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
                if mat_param and mat_param.AsElementId() == material_id:
                    elements.append(elem)
                    continue
                
                # Cek structural material
                struct_mat_param = elem.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
                if struct_mat_param and struct_mat_param.AsElementId() == material_id:
                    elements.append(elem)
                    continue
                
                # Cek paint material
                for geom_obj in elem.Geometry[Options()]:
                    if hasattr(geom_obj, 'MaterialElementId'):
                        if geom_obj.MaterialElementId == material_id:
                            elements.append(elem)
                            break
            except:
                continue
    
    return elements

def update_element_material(elem, old_material_id, new_material_id):
    """Update material pada element"""
    updated = False
    
    try:
        # Update material id parameter
        mat_param = elem.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
        if mat_param and not mat_param.IsReadOnly:
            if mat_param.AsElementId() == old_material_id:
                mat_param.Set(new_material_id)
                updated = True
        
        # Update structural material
        struct_mat_param = elem.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
        if struct_mat_param and not struct_mat_param.IsReadOnly:
            if struct_mat_param.AsElementId() == old_material_id:
                struct_mat_param.Set(new_material_id)
                updated = True
    except:
        pass
    
    return updated

def get_element_id_value(element_id):
    """Mendapatkan nilai ID yang compatible dengan semua versi Revit"""
    try:
        # Revit 2024+
        return element_id.Value
    except:
        # Revit 2023 dan sebelumnya
        return element_id.IntegerValue

def main():
    # Get all materials
    all_materials = get_all_materials()
    
    if not all_materials:
        forms.alert('Tidak ada material di dokumen ini.', exitscript=True)
    
    # Create material dictionary for selection
    material_dict = {'{} (ID: {})'.format(m.Name, get_element_id_value(m.Id)): m for m in all_materials}
    material_names = sorted(material_dict.keys())
    
    # Select source material (Material A - yang akan diganti)
    source_material_name = forms.SelectFromList.show(
        material_names,
        title='Pilih Material Sumber (Material A - yang akan diganti)',
        button_name='Select',
        multiselect=False
    )
    
    if not source_material_name:
        script.exit()
    
    source_material = material_dict[source_material_name]
    
    # Remove source material from target options
    target_material_names = [name for name in material_names if name != source_material_name]
    
    # Select target material (Material B - yang akan dipakai)
    target_material_name = forms.SelectFromList.show(
        target_material_names,
        title='Pilih Material Target (Material B - yang akan dipakai)',
        button_name='Select',
        multiselect=False
    )
    
    if not target_material_name:
        script.exit()
    
    target_material = material_dict[target_material_name]
    
    # Confirm action
    confirm_msg = 'Anda akan merge:\n\n' \
                  'Material A (Sumber): {}\n' \
                  'Material B (Target): {}\n\n' \
                  'Semua element dengan Material A akan diubah ke Material B,\n' \
                  'dan Material A akan dihapus.\n\n' \
                  'Lanjutkan?'.format(source_material.Name, target_material.Name)
    
    if not forms.alert(confirm_msg, yes=True, no=True):
        script.exit()
    
    # Start transaction
    t = Transaction(doc, 'Merge Material')
    t.Start()
    
    try:
        updated_count = 0
        source_material_id = source_material.Id
        target_material_id = target_material.Id
        
        # Get all elements with source material
        output = script.get_output()
        output.print_md('## Memproses Material Merge')
        output.print_md('**Material Sumber:** {}'.format(source_material.Name))
        output.print_md('**Material Target:** {}'.format(target_material.Name))
        output.print_md('---')
        
        # Update all elements
        all_elements = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
        
        for elem in all_elements:
            if update_element_material(elem, source_material_id, target_material_id):
                updated_count += 1
        
        # Try to delete source material
        try:
            doc.Delete(source_material_id)
            material_deleted = True
        except:
            material_deleted = False
        
        t.Commit()
        
        # Show results
        output.print_md('### Hasil:')
        output.print_md('- **Element diupdate:** {}'.format(updated_count))
        
        if material_deleted:
            output.print_md('- **Material sumber dihapus:** Ya')
        else:
            output.print_md('- **Material sumber dihapus:** Tidak (mungkin masih digunakan di tempat lain)')
        
        output.print_md('---')
        output.print_md('✅ **Merge material selesai!**')
        
        forms.alert('Merge material selesai!\n\n'
                   '{} element telah diupdate.'.format(updated_count),
                   title='Success')
        
    except Exception as e:
        t.RollBack()
        forms.alert('Error: {}'.format(str(e)), title='Error')

if __name__ == '__main__':
    main()