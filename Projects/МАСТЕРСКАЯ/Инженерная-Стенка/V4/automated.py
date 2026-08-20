import sys
import invoke
import pathlib
import shutil

import utils


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project 'Скоба-Стыковочная'")
def prepare_docking_bracket_doc(ctx):
    project_dir = pathlib.Path(__file__)
    doc_folder = project_dir.parent / 'DOC' / 'Скоба-Стыковочная'

    saving_groups = utils.prepare_saving_groups_for_project(project_dir.with_name('Крепёжная-Планка.SLDPRT'))

    shutil.rmtree(doc_folder, ignore_errors=True)

    steel_sheet_2mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_2mm.prepare_data([r"Крепёжная-Планка скоба-стыковочная"], step=True, dxf=True, save_folder_opt=doc_folder, quantity_evaluator=lambda x: (2 + 2 + 1) * 5 * 2 + 10)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(f"Скоба-Стыковочная") \
        .add_2mm_steel_sheet_table(steel_sheet_2mm) \
        .create(doc_folder)

    assert utils.prepare_archive(root_dir=doc_folder,
                                 archive_dir=doc_folder.parent,
                                 archive_name=f"ТЗ на производство стыковочных скоб для инженерной стенки",
                                 archive_type='zip',
                                 add_date=True)

@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project 'Фрезерная-Направляющая'")
def prepare_milling_guide_doc(ctx):
    project_dir = pathlib.Path(__file__)
    doc_folder = project_dir.parent / 'DOC' / 'Фрезерная-Направляющая'

    saving_groups = utils.prepare_saving_groups_for_project(project_dir.with_name('Крепёжная-Планка.SLDPRT'))

    shutil.rmtree(doc_folder, ignore_errors=True)

    steel_sheet_2mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_2mm.prepare_data([r"Крепёжная-Планка фрезерная-направляющая"], step=True, dxf=False, save_folder_opt=doc_folder)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(f"Фрезерная-Направляющая") \
        .add_2mm_steel_sheet_table(steel_sheet_2mm) \
        .create(doc_folder)



collection = invoke.Collection()
collection.add_task(prepare_docking_bracket_doc)
collection.add_task(prepare_milling_guide_doc)

# add sub tasks

current_dir = str(pathlib.Path(__file__).resolve().parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import engineering_wall_ls

collection.add_collection(engineering_wall_ls.collection, name="engineering-wall-ls")
