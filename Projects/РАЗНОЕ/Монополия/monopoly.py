import re
import shutil
import invoke
import pathlib

from pyswx.api.sldworks.interfaces import IComponent2

import utils
import utils.doc_creator

PROJECT_NAME = 'Монополия'
PROJECT_DIR = pathlib.Path(__file__)
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / PROJECT_NAME

@utils.sw_task(doc_string=f"Prepare wood-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_wood_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_DIR.with_name(f"Карта.SLDPRT"))

    doc_folder = DOC_FOLDER / 'Manufacturing' / 'Wood'
    shutil.rmtree(doc_folder, ignore_errors=True)

    polywood = utils.doc_creator.StandardElementsTable(saving_groups)
    polywood.prepare_data([r"Карта (путь-внешний|путь-внутренний|круг)"], step=True, dxf=False, save_folder_opt=doc_folder)
    polywood_material_info = utils.doc_creator.MaterialInfoTable()
    polywood_material_info.prepare_data([
        ["материал", "фанера"],
        ["толщина", "12мм"],
        ["сорт", "1 (первый)"],
        ["наличие ламинирования", "допускается, но только двустороннее"],
        ["влагозащита", "допускается, но не обязательно"],
    ])

    utils.doc_creator.CNCWoodMillingDocCreator(f"Монополия") \
        .add_table('Фанера 12мм', polywood, polywood_material_info) \
        .create(doc_folder)

    assert utils.prepare_archive(root_dir=doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство деревянных деталей для монополии",
                                 archive_type='zip',
                                 add_date=True)


collection = invoke.Collection()
collection.add_task(prepare_wood_doc)
