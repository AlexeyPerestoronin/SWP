import re
import shutil
import invoke
import pathlib

from pyswx.api.sldworks.interfaces import IComponent2

import utils

PROJECT_NAME = 'Мастерская-V4'
PROJECT_DIR = pathlib.Path(__file__)
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / 'Инженерная-Стенка (левая сторона)'


class PassOnlyLeftSideSteelComponents(utils.AssemblyComponentsFilter):

    def __call__(self, component: IComponent2, level: int) -> bool:
        component_name = component.name2
        configuration_name = component.referenced_configuration
        is_pass = False
        if level == 0:
            if bool(re.match(r"^Профильный-Каркас-\d", component_name)):
                if configuration_name in ('левый', 'правый'):
                    is_pass = True
            if bool(re.match(r"^Инженерная-Стенка-ЛС-\d", component_name)):
                is_pass = True
        else:
            is_pass = not bool(re.search(r"Верстак-Dim1000x600x50", component_name))

        if is_pass:
            utils.logger.info.log_line(f"{level}-level assembly component '{component_name} ({configuration_name})' passed")
        else:
            utils.logger.warning.log_line(f"{level}-level assembly component-'{component_name} ({configuration_name})' NOT passed")
        return is_pass


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_steel_manufacturing_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_DIR.with_name('Мастерская-V4.SLDASM'), PassOnlyLeftSideSteelComponents())

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

    assert utils.scan_unused_saving_group(saving_groups)
    assert utils.prepare_archive(root_dir=steel_manufacturing_doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство металлических деталей для инженерной стенки с левой стороны",
                                 archive_type='zip',
                                 add_date=True)


@utils.sw_task(doc_string=f"Prepare wood-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_wood_manufacturing_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_DIR.with_name('Деревянные-Конструкции-ЛС.SLDPRT'))

    wood_manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing' / 'Wood'
    shutil.rmtree(wood_manufacturing_doc_folder, ignore_errors=True)

    osb_sheet_12mm = utils.doc_creator.StandardElementsTable(saving_groups)
    osb_sheet_12mm.prepare_data([r"Деревянные-Конструкции-ЛС панели.+"], step=True, dxf=True, save_folder_opt=wood_manufacturing_doc_folder)
    osb_sheet_12mm_material_info = utils.doc_creator.MaterialInfoTable()
    osb_sheet_12mm_material_info.prepare_data([
        ["материал", "OBS"],
        ["толщина", "12мм"],
        ["размер", "2500x1250мм"],
    ])

    osb_sheet_15mm = utils.doc_creator.StandardElementsTable(saving_groups)
    osb_sheet_15mm.prepare_data([r"Деревянные-Конструкции-ЛС полочки.+"], step=True, dxf=True, save_folder_opt=wood_manufacturing_doc_folder)
    osb_sheet_15mm_material_info = utils.doc_creator.MaterialInfoTable()
    osb_sheet_15mm_material_info.prepare_data([
        ["материал", "OBS"],
        ["толщина", "15мм"],
        ["размер", "2500x1250мм"],
    ])

    utils.doc_creator.CNCWoodMillingCuttingDocCreator(f"Инженерная Стенка") \
        .add_table('OBS плита 12мм', osb_sheet_12mm, osb_sheet_12mm_material_info) \
        .add_table('OBS плита 15мм', osb_sheet_15mm, osb_sheet_15mm_material_info) \
        .create(wood_manufacturing_doc_folder)

    assert utils.scan_unused_saving_group(saving_groups)
    assert utils.prepare_archive(root_dir=wood_manufacturing_doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство деревянных деталей для инженерной стенки с левой стороны",
                                 archive_type='zip',
                                 add_date=True)


@utils.sw_task(doc_string=f"Make full documentation for '{PROJECT_NAME}'")
def prepare_full_doc(ctx):
    prepare_steel_manufacturing_doc(ctx)
    prepare_wood_manufacturing_doc(ctx)


collection = invoke.Collection()
collection.add_task(prepare_steel_manufacturing_doc, name="prepare-steel-manufacturing-doc")
collection.add_task(prepare_wood_manufacturing_doc, name="prepare-wood-manufacturing-doc")
collection.add_task(prepare_full_doc, name="prepare-full-doc")
