# -*- coding: UTF-8 -*-
"""Translation module for PrasKaaPyKit hooks."""

from pyrevit.userconfig import user_config


def lang():
    """Get current language setting from user config.
    
    Returns:
        str: Language code (e.g., 'EN', 'SK', 'ID')
    """
    try:
        return user_config.PrasKaaToolsSettings.language
    except:
        return 'EN'


hook_texts = {
    'EN': {
        'Link CAD': {
            'text': 'This CAD file will be linked in 3D.\n\n'
                    'For better performance, link CAD files in 2D (wire frame).\n\n'
                    'Do you want to continue?',
            'buttons': ['Cancel', 'Continue', 'More info']
        },
        'Link CAD file in 3D': {
            'text': 'This CAD file will be linked in 3D.\n\n'
                    'For better performance, link CAD files in 2D (wire frame).\n\n'
                    'Do you want to continue?',
            'buttons': ['Cancel', 'Continue', 'More info']
        },
        'In-Place Component': {
            'text': 'You are about to create an In-Place Component.\n\n'
                    'In-Place families can cause performance issues and difficulty in editing.\n\n'
                    'Do you want to continue?',
            'buttons': ['Cancel', 'Continue', 'More info']
        },
        'External Parameters': {
            'text': 'You are about to create External Parameters.\n\n'
                    'This is a legacy feature. Consider using Shared Parameters instead.\n\n'
                    'Do you want to continue?',
            'buttons': ['Cancel', 'Continue', 'More info']
        },
        'Project Parameters': {
            'text': 'You are about to create Project Parameters.\n\n'
                    'Project Parameters are shared across all categories and cannot be scheduled individually.\n\n'
                    'Do you want to continue?',
            'buttons': ['Cancel', 'Continue', 'More info']
        }
    },
    'SK': {
        'Link CAD': {
            'text': 'Tento CAD súbor bude prepojený v 3D.\n\n'
                    'Pre lepší výkon, prepojte CAD súbory v 2D (drôtený model).\n\n'
                    'Chcete pokračovať?',
            'buttons': ['Zrušiť', 'Pokračovať', 'Viac info']
        },
        'Link CAD file in 3D': {
            'text': 'Tento CAD súbor bude prepojený v 3D.\n\n'
                    'Pre lepší výkon, prepojte CAD súbory v 2D (drôtený model).\n\n'
                    'Chcete pokračovať?',
            'buttons': ['Zrušiť', 'Pokračovať', 'Viac info']
        },
        'In-Place Component': {
            'text': 'Chystáte sa vytvoriť komponent na mieste (In-Place).\n\n'
                    'Rodiny na mieste môžu spôsobiť problémy s výkonom a úpravou.\n\n'
                    'Chcete pokračovať?',
            'buttons': ['Zrušiť', 'Pokračovať', 'Viac info']
        },
        'External Parameters': {
            'text': 'Chystáte sa vytvoriť externé parametre.\n\n'
                    'Toto je staršia funkcia. Zvážte použitie zdieľaných parametrov.\n\n'
                    'Chcete pokračovať?',
            'buttons': ['Zrušiť', 'Pokračovať', 'Viac info']
        },
        'Project Parameters': {
            'text': 'Chystáte sa vytvoriť projektové parametre.\n\n'
                    'Projektové parametre sú zdieľané medzi všetkými kategóriami a nemožno ich individuálne plánovať.\n\n'
                    'Chcete pokračovať?',
            'buttons': ['Zrušiť', 'Pokračovať', 'Viac info']
        }
    },
    'ID': {
        'Link CAD': {
            'text': 'File CAD ini akan ditautkan dalam 3D.\n\n'
                    'Untuk performa lebih baik, tautkan file CAD dalam 2D (wire frame).\n\n'
                    'Apakah Anda ingin melanjutkan?',
            'buttons': ['Batal', 'Lanjutkan', 'Info lainnya']
        },
        'Link CAD file in 3D': {
            'text': 'File CAD ini akan ditautkan dalam 3D.\n\n'
                    'Untuk performa lebih baik, tautkan file CAD dalam 2D (wire frame).\n\n'
                    'Apakah Anda ingin melanjutkan?',
            'buttons': ['Batal', 'Lanjutkan', 'Info lainnya']
        },
        'In-Place Component': {
            'text': 'Anda akan membuat Komponen In-Place.\n\n'
                    'Famili In-Place dapat menyebabkan masalah performa dan kesulitan dalam pengeditan.\n\n'
                    'Apakah Anda ingin melanjutkan?',
            'buttons': ['Batal', 'Lanjutkan', 'Info lainnya']
        },
        'External Parameters': {
            'text': 'Anda akan membuat Parameter Eksternal.\n\n'
                    'Ini adalah fitur lawas. Pertimbangkan menggunakan Shared Parameters.\n\n'
                    'Apakah Anda ingin melanjutkan?',
            'buttons': ['Batal', 'Lanjutkan', 'Info lainnya']
        },
        'Project Parameters': {
            'text': 'Anda akan membuat Project Parameters.\n\n'
                    'Project Parameters dibagikan ke semua kategori dan tidak dapat dijadwalkan secara individual.\n\n'
                    'Apakah Anda ingin melanjutkan?',
            'buttons': ['Batal', 'Lanjutkan', 'Info lainnya']
        }
    }
}
