import re
import shutil
import invoke
import pathlib

from pyswx.api.sldworks.interfaces import IComponent2

import utils

PROJECT_NAME = 'Держатель-Для-Электрощитка'
PROJECT_DIR = pathlib.Path(__file__)
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / PROJECT_NAME


class PassAllExceptFastenersComponents(utils.AssemblyComponentsFilter):

    def __call__(self, component: IComponent2, level: int) -> bool:
        component_name = component.name2
        configuration_name = component.referenced_configuration
        is_pass = False
        if level == 0:
            is_pass = not bool(re.match(r"^hex (nut|bolt) .+", component_name))
        else:
            raise Exception(f"detected component of unexpected level: {component_name}")

        if is_pass:
            utils.logger.info.log_line(f"{level}-level assembly component '{component_name} ({configuration_name})' passed")
        else:
            utils.logger.warning.log_line(f"{level}-level assembly component-'{component_name} ({configuration_name})' NOT passed")
        return is_pass


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_steel_manufacturing_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_DIR.with_name('Держатель-Для-Электрощитка.SLDASM'), PassAllExceptFastenersComponents())

    steel_manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing' / 'Steel'
    shutil.rmtree(steel_manufacturing_doc_folder, ignore_errors=True)

    profile_tube_50_25_2mm = utils.doc_creator.StandardElementsTable(saving_groups)
    profile_tube_50_25_2mm.prepare_data([f"{PROJECT_NAME} несущий-каркас нк-планка"], step=True, dxf=False, save_folder_opt=steel_manufacturing_doc_folder)

    steel_sheet_4mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_4mm.prepare_data([f"{PROJECT_NAME} несущий-каркас (?!нк-планка).+"], step=True, dxf=True, save_folder_opt=steel_manufacturing_doc_folder)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(f"Держатель-Для-Электрощитка") \
        .add_50_25_2mm_steel_profile_tube_table(profile_tube_50_25_2mm) \
        .add_4mm_steel_sheet_table(steel_sheet_4mm) \
        .create(steel_manufacturing_doc_folder)

    assert utils.scan_unused_saving_group(saving_groups, [f"{PROJECT_NAME} электрощиток .+"])
    assert utils.prepare_archive(root_dir=steel_manufacturing_doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство металлических деталей для держателя электрощитка",
                                 archive_type='zip',
                                 add_date=True)


@utils.sw_task(doc_string=f"Make full documentation for '{PROJECT_NAME}'")
def prepare_full_doc(ctx):
    prepare_steel_manufacturing_doc(ctx)


collection = invoke.Collection()
collection.add_task(prepare_steel_manufacturing_doc, name="prepare-steel-manufacturing-doc")
collection.add_task(prepare_full_doc, name="prepare-full-doc")
