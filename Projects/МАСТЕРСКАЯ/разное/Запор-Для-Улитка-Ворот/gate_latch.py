import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Запор-Для-Ворот-V2'
CONFIGURATION_NAME = '140мм'
PROJECT_DIR = pathlib.Path(__file__).parent
PROJECT_PATH = PROJECT_DIR / 'V2' / f'{PROJECT_NAME}.SLDASM'
DOC_FOLDER = PROJECT_DIR / 'DOC' / PROJECT_NAME
QUANTITY = lambda x: x * 30


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

    manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
    shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

    steel_8mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_8mm.prepare_data([f"{PROJECT_NAME} (улитка|ручка|скоба-\w+)"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder, quantity_evaluator=QUANTITY)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(PROJECT_NAME) \
        .add_8mm_steel_sheet_table(steel_8mm) \
        .create(manufacturing_doc_folder)

    assert utils.prepare_archive(root_dir=manufacturing_doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство металлических деталей для {PROJECT_NAME}-{CONFIGURATION_NAME}",
                                 archive_type='zip',
                                 add_date=True)


@utils.sw_task(doc_string=f"Prepare assembling documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_assembling_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

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
                                        quantity_evaluator=QUANTITY)

    special_elements_table.prepare_data([f"{PROJECT_NAME} фурнитура фур-ПШ-10-26-8"],
                                        step=False,
                                        save_folder_opt=assembling_doc_folder,
                                        special_name_opt='подшипник шариковый 10-26-8',
                                        buy_link_opt='https://ozon.ru/t/cFxthnH',
                                        quantity_evaluator=QUANTITY)

    iso_elements_table = utils.doc_creator.ISOToolboxAssemblyTable(saving_groups)
    iso_elements_table.prepare_data(quantity_evaluator=QUANTITY)

    utils.doc_creator.AssemblyDocCreator(PROJECT_NAME) \
        .add_table("Магниты", special_elements_table) \
        .add_table("ISO-Крепёж", iso_elements_table) \
        .create(assembling_doc_folder)


@utils.sw_task(doc_string=f"Make complex documentation for '{PROJECT_NAME}'",
               pre=[clear_doc_folder, parse_saving_groups, prepare_manufacturing_doc, prepare_assembling_doc])
def make_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    assert utils.scan_unused_saving_group(
        saving_groups,
        skip_elements=[
            f"{PROJECT_NAME} фурнитура фур-ПП-подшипник",
            f"{PROJECT_NAME} фурнитура фур-ПП-п-часть",
        ])


collection = invoke.Collection()
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_manufacturing_doc, name="prepare-manufacturing-doc")
collection.add_task(prepare_assembling_doc, name="prepare-assembling-doc")
collection.add_task(make_doc, name="make-doc")
