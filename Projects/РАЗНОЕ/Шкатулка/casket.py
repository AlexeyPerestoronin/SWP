import re
import shutil
import invoke
import pathlib

from pyswx.api.sldworks.interfaces import IComponent2

import utils
import utils.doc_creator

PROJECT_NAME = 'Шкатулка'
PROJECT_DIR = pathlib.Path(__file__)
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / PROJECT_NAME


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_metal_manufacturing_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_DIR.with_name(f"{PROJECT_NAME}.SLDPRT"))

    doc_folder = DOC_FOLDER / 'Manufacturing' / 'Metal'
    shutil.rmtree(doc_folder, ignore_errors=True)

    aluminum_block = utils.doc_creator.StandardElementsTable(saving_groups)
    aluminum_block.prepare_data([f"{PROJECT_NAME} .+"], step=True, dxf=False, save_folder_opt=doc_folder)
    aluminum_block_material_info = utils.doc_creator.MaterialInfoTable()
    aluminum_block_material_info.prepare_data([
        ["материал", "алюминий"],
        ["минимальный размер заготовки для фрезерования", "параллелограмм 150x100x100мм"],
    ])

    utils.doc_creator.CNCMetalMillingDocCreator(PROJECT_NAME) \
        .add_table('Алюминий', aluminum_block, aluminum_block_material_info) \
        .create(doc_folder)

    assert utils.scan_unused_saving_group(saving_groups)
    assert utils.prepare_archive(root_dir=doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство металлических деталей для подарочной шкатулки",
                                 archive_type='zip',
                                 add_date=True)


collection = invoke.Collection()
collection.add_task(prepare_metal_manufacturing_doc)
