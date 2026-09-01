import re
import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Держатель-Для-Сварочной-Горелки'
PROJECT_PATH = pathlib.Path(__file__).with_name(f'{PROJECT_NAME}-Сборка.SLDASM')
DOC_FOLDER = PROJECT_PATH.with_name(f'{PROJECT_NAME}-DOC')


@utils.sw_task(doc_string=f"Clear folder with '{PROJECT_NAME}'-project documentation")
def clear_doc_folder(ctx):
    shutil.rmtree(DOC_FOLDER, ignore_errors=True)


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
    execute = True
    if execute:
        manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
        shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

        td_preparator = utils.doc_creator.CNCLaserCuttingDocCreator.TableDataPreparator(
            saving_groups, manufacturing_doc_folder, lambda expression, component_full_name: bool(re.match(f"{PROJECT_NAME} {expression}", component_full_name)))
        utils.doc_creator.CNCLaserCuttingDocCreator(PROJECT_NAME) \
            .add_4mm_steel_sheet_table(td_preparator.prepare([f"(основание|держатель) .+"], step=True, dxf=True)) \
            .create(manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Prepare assembling documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_assembling_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    execute = True
    if execute:
        assembling_doc_folder = DOC_FOLDER / 'Assembling'
        shutil.rmtree(assembling_doc_folder, ignore_errors=True)

        special_elements_table = utils.doc_creator.SpecialElementsAssemblyTable(saving_groups)
        special_elements_table.prepare_data([f"{PROJECT_NAME} магнит"], step=True, save_folder_opt=assembling_doc_folder, buy_link_opt='https://ozon.ru/t/7GG68ot')

        iso_elements_table = utils.doc_creator.ISOToolboxAssemblyTable(saving_groups)
        iso_elements_table.prepare_data()

        utils.doc_creator.AssemblyDocCreator(PROJECT_NAME) \
            .add_table("Магниты", special_elements_table) \
            .add_table("ISO-Крепёж", iso_elements_table) \
            .create(assembling_doc_folder)


@utils.sw_task(doc_string=f"Wrapping documentation for the project '{PROJECT_NAME}' to ZIP archive")
def convert_doc_to_zip(ctx):
    DOC_FOLDER.with_suffix('.zip').unlink(missing_ok=True)
    shutil.make_archive(base_name=DOC_FOLDER, root_dir=DOC_FOLDER, format='zip')


@utils.sw_task(doc_string=f"Make complex documentation for '{PROJECT_NAME}'",
               pre=[clear_doc_folder, parse_saving_groups, prepare_manufacturing_doc, prepare_assembling_doc, convert_doc_to_zip])
def make_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    for saving_group in saving_groups:
        if saving_group.mark is None:
            utils.logger.error.log_line(f"detected unclassified/unused elements '{saving_group.save_file_name}'")


collection = invoke.Collection()
collection.add_task(clear_doc_folder, name="clear-doc-folder")
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_manufacturing_doc, name="prepare-manufacturing-doc")
collection.add_task(prepare_assembling_doc, name="prepare-assembling-doc")
collection.add_task(convert_doc_to_zip, name="convert-doc-to-zip")
collection.add_task(make_doc, name="make-doc")
