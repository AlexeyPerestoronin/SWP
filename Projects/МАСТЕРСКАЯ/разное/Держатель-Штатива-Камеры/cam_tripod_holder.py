import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Держатель-Штатива-Камеры'
PROJECT_DIR = pathlib.Path(__file__)
PROJECT_PATH = PROJECT_DIR.parent / f'{PROJECT_NAME}.SLDPRT'
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / PROJECT_NAME
QUANTITY = lambda x: x


@utils.sw_task(doc_string=f"Prepare solid-bodies-saving-groups for '{PROJECT_NAME}'-project")
def parse_saving_groups(ctx):
    if not hasattr(ctx, 'saving_groups'):
        unique_bodies_manager = utils.UniqueBodiesManager()
        unique_bodies_manager.add_from_project(PROJECT_PATH)
        saving_groups = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies)
        setattr(ctx, 'saving_groups', saving_groups)


@utils.sw_task(doc_string=f"Prepare manufacturing documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

    manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
    shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

    steel_sheet_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_4mm.prepare_data([f"{PROJECT_NAME} пластина-конструкционная .+"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder, quantity_evaluator=QUANTITY)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(PROJECT_NAME) \
        .add_4mm_steel_sheet_table(steel_sheet_4mm)\
        .create(manufacturing_doc_folder)

    assert utils.scan_unused_saving_group(saving_groups, [f"{PROJECT_NAME} (магнит|таймер)"])
    assert utils.prepare_archive(root_dir=manufacturing_doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство металлических деталей для {PROJECT_NAME}",
                                 archive_type='zip',
                                 add_date=True)

collection = invoke.Collection()
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_manufacturing_doc, name="prepare-manufacturing-doc")
