import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Запор-Для-Ворот'
CONFIGURATION_NAME = '140мм'
PROJECT_PATH = pathlib.Path(__file__).with_name(f'{PROJECT_NAME}.SLDASM')
DOC_FOLDER = PROJECT_PATH.with_name(f'{PROJECT_NAME} ({CONFIGURATION_NAME}) DOC')
QUANTITY_EVALUATOR=lambda x: x * 10


@utils.sw_task(doc_string=f"Clear folder with '{PROJECT_NAME}'-project documentation")
def clear_doc_folder(ctx):
    shutil.rmtree(DOC_FOLDER, ignore_errors=True)


@utils.sw_task(doc_string=f"Prepare solid-bodies-saving-groups for '{PROJECT_NAME}'-project")
def parse_saving_groups(ctx):
    if not hasattr(ctx, 'saving_groups'):
        unique_bodies_manager = utils.UniqueBodiesManager()
        unique_bodies_manager.add_from_project(PROJECT_PATH, configuration=CONFIGURATION_NAME)
        saving_groups = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies)
        setattr(ctx, 'saving_groups', saving_groups)


@utils.sw_task(doc_string=f"Prepare manufacturing documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    execute = True
    if execute:
        manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
        shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

        steel_8vv = utils.doc_creator.LaserCuttingManufacturingElementsTable(saving_groups)
        steel_8vv.prepare_data([f"{PROJECT_NAME} (улитка|ручка|скоба-\w+)"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder, quantity_evaluator=lambda x: x * 10)

        utils.doc_creator.CNCLaserCuttingDocCreator(PROJECT_NAME) \
            .add_8mm_steel_sheet_table(steel_8vv) \
            .create(manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Prepare assembling documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_assembling_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    execute = True
    if execute:
        assembling_doc_folder = DOC_FOLDER / 'Assembling'
        shutil.rmtree(assembling_doc_folder, ignore_errors=True)

        if CONFIGURATION_NAME == '140мм':
            weld_on_metal_hinge_buy_link = 'https://ozon.ru/t/v0F2iIx'
        elif CONFIGURATION_NAME == '160мм':
            raise Exception(f'weld-on metal hinge is not detected on Ozon')
        else:
            raise Exception(f'unexpected configuration: {CONFIGURATION_NAME}')

        special_elements_table = utils.doc_creator.SpecialElementsAssemblyTable(saving_groups)
        special_elements_table.prepare_data([f"{PROJECT_NAME} фурнитура фур-ПП-м-часть"],
                                            step=False,
                                            save_folder_opt=assembling_doc_folder,
                                            special_name_opt=f'петля приварная {CONFIGURATION_NAME}',
                                            buy_link_opt=weld_on_metal_hinge_buy_link,
                                            quantity_evaluator=QUANTITY_EVALUATOR)

        special_elements_table.prepare_data([f"{PROJECT_NAME} фурнитура фур-ПШ-10-26-8"],
                                            step=False,
                                            save_folder_opt=assembling_doc_folder,
                                            special_name_opt='подшипник шариковый 10-26-8',
                                            buy_link_opt='https://ozon.ru/t/cFxthnH',
                                            quantity_evaluator=QUANTITY_EVALUATOR)

        iso_elements_table = utils.doc_creator.ISOToolboxAssemblyTable(saving_groups)
        iso_elements_table.prepare_data(quantity_evaluator=QUANTITY_EVALUATOR)

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
            save_file_name = str(saving_group.save_file_name)
            unused_elements = [
                f"{PROJECT_NAME} фурнитура фур-ПП-подшипник",
                f"{PROJECT_NAME} фурнитура фур-ПП-п-часть",
            ]
            if save_file_name in unused_elements:
                utils.logger.info.log_line(f"detected unused elements '{save_file_name}'")
            else:
                utils.logger.error.log_line(f"detected unclassified elements '{save_file_name}'")


collection = invoke.Collection()
collection.add_task(clear_doc_folder, name="clear-doc-folder")
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_manufacturing_doc, name="prepare-manufacturing-doc")
collection.add_task(prepare_assembling_doc, name="prepare-assembling-doc")
collection.add_task(convert_doc_to_zip, name="convert-doc-to-zip")
collection.add_task(make_doc, name="make-doc")
