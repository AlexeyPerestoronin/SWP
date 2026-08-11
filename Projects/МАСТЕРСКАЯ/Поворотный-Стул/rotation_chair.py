import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Поворотный-Стул'
PROJECT_PATH = pathlib.Path(__file__).with_name(f'{PROJECT_NAME}.SLDASM')
DOC_FOLDER = PROJECT_PATH.with_name(f'{PROJECT_NAME} DOC')


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
def prepare_metal_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

    manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing' / 'Metal'
    shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

    steel_8mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_8mm.prepare_data([f"{PROJECT_NAME} часть-верхняя чв-.+"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder)
    steel_8mm.prepare_data([f"{PROJECT_NAME} часть-нижняя чн-(ножка|площадка|проставка-основания)"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder)

    steel_6mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_6mm.prepare_data([f"{PROJECT_NAME} часть-нижняя чн-платформа-колеса"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(PROJECT_NAME) \
        .add_8mm_steel_sheet_table(steel_8mm) \
        .add_6mm_steel_sheet_table(steel_6mm) \
        .create(manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Prepare wood-manufacturing documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_wood_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

    wood_manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing' / 'Wood'
    shutil.rmtree(wood_manufacturing_doc_folder, ignore_errors=True)

    hight_quality_plywood_25mm = utils.doc_creator.StandardElementsTable(saving_groups)
    hight_quality_plywood_25mm.prepare_data([f"{PROJECT_NAME} сидушка"], step=True, dxf=True, save_folder_opt=wood_manufacturing_doc_folder)
    material_info_table = utils.doc_creator.MaterialInfoTable()
    material_info_table.prepare_data([
            ["материал", "фанера"],
            ["толщина", "25мм"],
            ["сорт", "1 или 2 (приоритет меньшей итоговой стоимости)"],
            ["древесина", "не имеет значения (приоритет меньшей итоговой стоимости)"],
            ["исходный размер", "не имеет значения (приоритет меньшей итоговой стоимости)"],
            ["влагостойкость", "обязательна"],
            ["шлифование", "обязательно включая края"],
            ["ламинирование", "обязательно с одной стороны"],
        ])

    utils.doc_creator.CNCWoodMillingCuttingDocCreator(PROJECT_NAME) \
        .add_table('Фанера 25мм высококачественная', hight_quality_plywood_25mm, material_info_table) \
        .create(wood_manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Prepare assembling documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_assembling_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

    assembling_doc_folder = DOC_FOLDER / 'Assembling'
    shutil.rmtree(assembling_doc_folder, ignore_errors=True)

    special_elements_table = utils.doc_creator.SpecialElementsAssemblyTable(saving_groups)
    special_elements_table.prepare_data([f"Колесо-Большегрузное платформа"],
                                        step=False,
                                        save_folder_opt=assembling_doc_folder,
                                        special_name_opt=f'колесо (опорное, поворотно, большегрузное)',
                                        buy_link_opt='https://ozon.ru/t/mUy1dDT')
    special_elements_table.prepare_data([f"Поворотный-Стул домкрат д-часть-1"],
                                        step=False,
                                        save_folder_opt=assembling_doc_folder,
                                        special_name_opt=f'домкрат',
                                        buy_link_opt='https://ozon.ru/t/CrlxSgd')

    iso_elements_table = utils.doc_creator.ISOToolboxAssemblyTable(saving_groups)
    iso_elements_table.prepare_data()

    utils.doc_creator.AssemblyDocCreator(PROJECT_NAME) \
        .add_table("Опорные колёса", special_elements_table) \
        .add_table("ISO-Крепёж", iso_elements_table) \
        .create(assembling_doc_folder)


@utils.sw_task(doc_string=f"Wrapping documentation for the project '{PROJECT_NAME}' to ZIP archive")
def convert_doc_to_zip(ctx):
    DOC_FOLDER.with_suffix('.zip').unlink(missing_ok=True)
    shutil.make_archive(base_name=DOC_FOLDER, root_dir=DOC_FOLDER, format='zip')


@utils.sw_task(doc_string=f"Make complex documentation for '{PROJECT_NAME}'",
               pre=[clear_doc_folder, parse_saving_groups, prepare_metal_manufacturing_doc, prepare_wood_manufacturing_doc, prepare_assembling_doc, convert_doc_to_zip])
def make_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    for saving_group in saving_groups:
        if saving_group.mark is None:
            save_file_name = str(saving_group.save_file_name)
            unused_elements = [
                'Поворотный-Стул домкрат д-часть-2',
                'Поворотный-Стул домкрат д-часть-3',
                'Колесо-Большегрузное каталка кат-колесо',
                'Колесо-Большегрузное каталка кат-резина',
                'Колесо-Большегрузное каталка кат-стойка',
                'Колесо-Большегрузное каталка плт-ось',
            ]
            if save_file_name in unused_elements:
                utils.logger.info.log_line(f"detected unused elements '{save_file_name}'")
            else:
                utils.logger.error.log_line(f"detected unclassified elements '{save_file_name}'")


collection = invoke.Collection()
collection.add_task(clear_doc_folder, name="clear-doc-folder")
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_metal_manufacturing_doc, name="prepare-metal-manufacturing-doc")
collection.add_task(prepare_wood_manufacturing_doc, name="prepare-wood-manufacturing-doc")
collection.add_task(prepare_assembling_doc, name="prepare-assembling-doc")
collection.add_task(convert_doc_to_zip, name="convert-doc-to-zip")
collection.add_task(make_doc, name="make-doc")
