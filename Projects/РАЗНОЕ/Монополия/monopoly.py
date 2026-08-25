import re
import shutil
import invoke
import pathlib

from pyswx.api.sldworks.interfaces import IComponent2

import utils
import utils.doc_creator

PROJECT_NAME = 'Монополия'
PROJECT_DIR = pathlib.Path(__file__)
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / PROJECT_NAME


class PassAllExceptFastenersComponents(utils.AssemblyComponentsFilter):

    def __call__(self, component: IComponent2, level: int) -> bool:
        component_name = component.name2
        configuration_name = component.referenced_configuration
        is_pass = False
        if level == 0:
            is_pass = bool(re.match(r"Игровая-Платформа", component_name))
        else:
            raise Exception(f"detected component of unexpected level: {component_name}")

        if is_pass:
            utils.logger.info.log_line(f"{level}-level assembly component '{component_name} ({configuration_name})' passed")
        else:
            utils.logger.warning.log_line(f"{level}-level assembly component-'{component_name} ({configuration_name})' NOT passed")
        return is_pass


@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_platform_doc(ctx):
    saving_groups = utils.prepare_saving_groups_for_project(PROJECT_DIR.with_name(f"{PROJECT_NAME}.SLDASM"), PassAllExceptFastenersComponents())

    doc_folder = DOC_FOLDER
    shutil.rmtree(doc_folder, ignore_errors=True)

    pla_filament = utils.doc_creator.StandardElementsTable(saving_groups)
    pla_filament.prepare_data([f"Игровая-Платформа база"], step=True, dxf=False, save_folder_opt=doc_folder)

    utils.doc_creator.CNC3DPrintingDocCreator(f"Монополия") \
        .add_PLA(pla_filament) \
        .create(doc_folder)


collection = invoke.Collection()
collection.add_task(prepare_platform_doc)
