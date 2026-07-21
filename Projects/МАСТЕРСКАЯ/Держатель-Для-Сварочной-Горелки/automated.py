import re
import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Держатель-Для-Сварочной-Горелки'
PROJECT_PATH = pathlib.Path(__file__).with_name(f'{PROJECT_NAME}-Сборка.SLDASM')
DOC_FOLDER = PROJECT_PATH.with_name(f'{PROJECT_NAME}-DOC')


@invoke.task()
def clear_doc_folder(ctx):
    """Clear folder with project documentation!"""
    shutil.rmtree(DOC_FOLDER, ignore_errors=True)


@invoke.task()
def prepare_manufacturing_doc(ctx):
    f"""Prepare manufacturing documentation for the project '{PROJECT_NAME}'"""

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_project(PROJECT_PATH)
    saving_groups = utils.prepare_saving_groups_2(unique_bodies_manager.unique_bodies)

    execute = True
    if execute:
        manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
        shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

        td_preparator = utils.doc_creator.CNCLaserCuttingDocCreator.TableDataPreparator(
            saving_groups, manufacturing_doc_folder, lambda expression, component_full_name: bool(re.match(f"{expression}", component_full_name)))
        td_preparator.unused([f"({PROJECT_NAME} магнит|hex nut .+|hex bolt .+)"])
        utils.doc_creator.CNCLaserCuttingDocCreator(PROJECT_NAME) \
            .add_4mm_steel_sheet_table(td_preparator.prepare(True, True, [f"{PROJECT_NAME} (основание|держатель) .+"], quantity_expression=lambda x :  x * 2)) \
            .add_unclassified_table(td_preparator.unclassified()) \
            .create(manufacturing_doc_folder)


@invoke.task()
def prepare_assembling_doc(ctx):
    f"""Prepare manufacturing documentation for the project '{PROJECT_NAME}'"""
    pass


@invoke.task()
def convert_doc_to_zip(ctx):
    f"""Wrapping documentation for the project '{PROJECT_NAME}' to ZIP archive"""
    pass


collection = invoke.Collection()
collection.add_task(clear_doc_folder, name="clear-doc-folder")
collection.add_task(prepare_manufacturing_doc, name="prepare-manufacturing-doc")
collection.add_task(prepare_assembling_doc, name="prepare-assembling-doc")
collection.add_task(convert_doc_to_zip, name="convert-doc-to-zip")
