import re
import invoke
import pathlib
import shutil

import utils

from pyswx.api.sldworks.interfaces import IComponent2


PROJECT_NAME = 'Кронштейн-Многоколенчатый'
PROJECT_DIR = pathlib.Path(__file__).parent
PROJECT_PATH = PROJECT_DIR / f'{PROJECT_NAME}.SLDASM'
DOC_FOLDER = PROJECT_DIR / 'DOC' / PROJECT_NAME
QUANTITY = lambda x: x * 2

class SkipAssemblyComponents(utils.AssemblyComponentsFilter):

    def __call__(self, component: IComponent2, level: int) -> bool:
        component_name = component.name2
        configuration_name = component.referenced_configuration
        is_pass = False
        if level == 0: is_pass = bool(re.match(f"{PROJECT_NAME}", component_name))

        if is_pass:
            utils.logger.info.log_line(f"{level}-level assembly component '{component_name} ({configuration_name})' passed")
        else:
            utils.logger.warning.log_line(f"{level}-level assembly component-'{component_name} ({configuration_name})' NOT passed")
        return is_pass


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_manufacturing_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_PATH, SkipAssemblyComponents())

    manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
    shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

    steel_profile_tube_40_20_2mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_profile_tube_40_20_2mm.prepare_data([f"{PROJECT_NAME} штанга-т\d"], step=True, dxf=False, save_folder_opt=manufacturing_doc_folder, quantity_evaluator=QUANTITY)

    steel_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_4mm.prepare_data([f"{PROJECT_NAME} (ушко|скоба-т\d)"], step=True, dxf=True, save_folder_opt=manufacturing_doc_folder, quantity_evaluator=QUANTITY)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(PROJECT_NAME) \
        .add_40_20_2mm_steel_profile_tube_table(steel_profile_tube_40_20_2mm) \
        .add_4mm_steel_sheet_table(steel_4mm) \
        .create(manufacturing_doc_folder)

    assert utils.prepare_archive(root_dir=manufacturing_doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство металлических деталей для {PROJECT_NAME}",
                                 archive_type='zip',
                                 add_date=True)

    assert utils.scan_unused_saving_group(saving_groups)

collection = invoke.Collection()
collection.add_task(prepare_manufacturing_doc)