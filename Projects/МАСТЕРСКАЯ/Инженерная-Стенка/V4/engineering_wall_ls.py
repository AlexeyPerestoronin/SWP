import re
import shutil
import invoke
import pathlib

from pyswx.api.sldworks.interfaces import IComponent2

import utils
import utils.doc_creator

import utils

PROJECT_NAME = 'Мастерская-V4'
CONFIGURATION_NAME = None
QUANTITY_EVALUATOR = lambda x: x
PROJECT_PATH = pathlib.Path(__file__).with_name(f'{PROJECT_NAME}.SLDASM')
DOC_FOLDER = PROJECT_PATH.with_name(f'Инженерная-Стенка (левая сторона) DOC')


@utils.sw_task(doc_string=f"Clear folder with '{PROJECT_NAME}'-project documentation")
def clear_doc_folder(ctx):
    shutil.rmtree(DOC_FOLDER, ignore_errors=True)


@utils.sw_task(doc_string=f"Prepare solid-bodies-saving-groups for '{PROJECT_NAME}'-project")
def parse_saving_groups(ctx):
    if not hasattr(ctx, 'saving_groups'):

        class PassOnlyLeftSideComponents(utils.AssemblyComponentsFilter):

            def __call__(self, component: IComponent2, level: int) -> bool:
                component_name = component.name2
                configuration_name = component.referenced_configuration
                is_pass = False
                if level == 0:
                    if bool(re.match(r"^Профильный-Каркас-\d", component_name)):
                        if configuration_name in ('левый', 'правый'):
                            is_pass = True
                    elif bool(re.match(r"^Инженерная-Стенка-ЛС-\d", component_name)):
                        is_pass = True
                    if bool(re.match(r"^Деревянные-Конструкции-ЛС-\d", component_name)):
                        is_pass = True
                else:
                    is_pass = not bool(re.search(r"Верстак-Dim1000x600x50", component_name))
                if is_pass:
                    utils.logger.info.log_line(f"{level}-level assembly component '{component_name} ({configuration_name})' passed")
                else:
                    utils.logger.warning.log_line(f"{level}-level assembly component-'{component_name} ({configuration_name})' NOT passed")
                return is_pass

        unique_bodies_manager = utils.UniqueBodiesManager()
        unique_bodies_manager.add_from_project(PROJECT_PATH, configuration=CONFIGURATION_NAME, component_filter=PassOnlyLeftSideComponents())
        saving_groups = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies)
        setattr(ctx, 'saving_groups', saving_groups)


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_steel_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

    steel_manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing' / 'Steel'
    shutil.rmtree(steel_manufacturing_doc_folder, ignore_errors=True)

    profile_tube_50_50_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    profile_tube_50_50_4mm.prepare_data([r"Опорная-Колонна-ЛС каркас к-.+", r"Перфорированная-Стяжка стяжка-\d+"],
                                        step=True,
                                        dxf=False,
                                        save_folder_opt=steel_manufacturing_doc_folder)

    profile_tube_50_25_2mm = utils.doc_creator.StandardElementsTable(saving_groups)
    profile_tube_50_25_2mm.prepare_data([
        r"Опорная-Колонна-ЛС каркас-ящиков кя-.+",
        r"Крепёжная-Планка планка-(левая|правая)",
    ],
                                        step=True,
                                        dxf=False,
                                        save_folder_opt=steel_manufacturing_doc_folder)

    steel_sheet_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_4mm.prepare_data([
        r"Опорная-Колонна-ЛС кк-горизонтальной-балки",
        r"Перфорированная-Стяжка ушко",
        r"Крепёжная-Планка крепёжные-окна ко-окно",
    ],
                                 step=True,
                                 dxf=True,
                                 save_folder_opt=steel_manufacturing_doc_folder)
    steel_sheet_4mm.prepare_data([r"Опорная-Колонна-ЛС кк-полочки-(верхний|нижний)"],
                                 step=True,
                                 dxf=True,
                                 save_folder_opt=steel_manufacturing_doc_folder,
                                 quantity_evaluator=lambda x: 40)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(f"Инженерная Стенка") \
        .add_50_50_4mm_steel_profile_tube_table(profile_tube_50_50_4mm) \
        .add_50_25_2mm_steel_profile_tube_table(profile_tube_50_25_2mm) \
        .add_4mm_steel_sheet_table(steel_sheet_4mm) \
        .create(steel_manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Prepare wood-manufacturing documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_wood_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')

    wood_manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing' / 'Wood'
    shutil.rmtree(wood_manufacturing_doc_folder, ignore_errors=True)

    osb_sheet_12mm = utils.doc_creator.StandardElementsTable(saving_groups)
    osb_sheet_12mm.prepare_data([r"Деревянные-Конструкции-ЛС панели .+"], step=True, dxf=True, save_folder_opt=wood_manufacturing_doc_folder)

    plywood_sheet_15mm = utils.doc_creator.StandardElementsTable(saving_groups)
    plywood_sheet_15mm.prepare_data([r"Деревянные-Конструкции-ЛС полочки .+"], step=True, dxf=True, save_folder_opt=wood_manufacturing_doc_folder)

    utils.doc_creator.CNCWoodMillingCuttingDocCreator(f"Инженерная Стенка") \
        .add_12mm_OSB(osb_sheet_12mm) \
        .add_15mm_plywood(plywood_sheet_15mm) \
        .create(wood_manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Wrapping documentation for the project '{PROJECT_NAME}' to ZIP archive")
def convert_doc_to_zip(ctx):
    DOC_FOLDER.with_suffix('.zip').unlink(missing_ok=True)
    shutil.make_archive(base_name=DOC_FOLDER, root_dir=DOC_FOLDER, format='zip')


@utils.sw_task(doc_string=f"Make complex documentation for '{PROJECT_NAME}'",
               pre=[clear_doc_folder, parse_saving_groups, prepare_steel_manufacturing_doc, prepare_wood_manufacturing_doc, convert_doc_to_zip])
def make_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    for saving_group in saving_groups:
        if saving_group.mark is None:
            save_file_name = str(saving_group.save_file_name)
            unused_elements = [
                # past there names of unused elements
            ]
            if save_file_name in unused_elements:
                utils.logger.info.log_line(f"detected unused elements '{save_file_name}'")
            else:
                utils.logger.error.log_line(f"detected unclassified elements '{save_file_name}'")


collection = invoke.Collection()
collection.add_task(clear_doc_folder, name="clear-doc-folder")
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_steel_manufacturing_doc, name="prepare-steel-manufacturing-doc")
collection.add_task(prepare_wood_manufacturing_doc, name="prepare-wood-manufacturing-doc")
collection.add_task(convert_doc_to_zip, name="convert-doc-to-zip")
collection.add_task(make_doc, name="make-doc")
