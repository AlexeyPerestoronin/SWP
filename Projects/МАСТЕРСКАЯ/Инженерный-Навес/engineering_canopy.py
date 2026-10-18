import re
import invoke
import pathlib
import shutil

import utils
import utils.doc_creator

PROJECT_DIR = pathlib.Path(__file__).parent
DOC_FOLDER = PROJECT_DIR / 'DOC'


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project 'Держатель-Занавески'")
def prepare_entrance_frame_doc(ctx):
    project_name = 'Рамка-Входная'
    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_project(PROJECT_DIR / f'{project_name}.SLDPRT')
    saving_groups = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies)

    doc_folder = DOC_FOLDER / project_name
    shutil.rmtree(doc_folder, ignore_errors=True)

    steel_profile_tube_50_50_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_profile_tube_50_50_4mm.prepare_data([f"{project_name} профильная-труба .+"], step=True, dxf=False, save_folder_opt=doc_folder)

    steel_sheet_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_4mm.prepare_data([f"{project_name} скоба-крепёжная .+"], step=True, dxf=True, save_folder_opt=doc_folder)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(project_name) \
        .add_50_50_4mm_steel_profile_tube_table(steel_profile_tube_50_50_4mm) \
        .add_4mm_steel_sheet_table(steel_sheet_4mm) \
        .create(doc_folder)

    assert utils.prepare_archive(root_dir=doc_folder,
                                 archive_dir=doc_folder.parent,
                                 archive_name=f"ТЗ на производство элементов для входной рамки инженерного навеса",
                                 archive_type='zip',
                                 add_date=True)

    assert utils.scan_unused_saving_group(saving_groups)


collection = invoke.Collection()
collection.add_task(prepare_entrance_frame_doc)
