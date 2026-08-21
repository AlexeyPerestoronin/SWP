import re
import invoke
import pathlib
import shutil

import utils
import projects

from pyswx.api.sldworks.interfaces import IComponent2

class PassOnlyDockingBracketComponentsFromLeftSide(utils.AssemblyComponentsFilter):

    def __call__(self, component: IComponent2, level: int) -> bool:
        component_name = component.name2
        configuration_name = component.referenced_configuration
        is_pass = False
        if level == 0:
            if bool(re.match(r"^Профильный-Каркас-\d", component_name)):
                if configuration_name in ('левый', 'правый'):
                    is_pass = True
        else:
            is_pass = bool(re.search(r"Крепёжная-Планка-\d", component_name)) and configuration_name == 'скоба-стыковочная'

        if is_pass:
            utils.logger.info.log_line(f"{level}-level assembly component '{component_name} ({configuration_name})' passed")
        else:
            utils.logger.warning.log_line(f"{level}-level assembly component-'{component_name} ({configuration_name})' NOT passed")
        return is_pass

@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project 'Скоба-Стыковочная'")
def prepare_docking_bracket_doc(ctx):
    project_dir = pathlib.Path(__file__)
    doc_folder = project_dir.parent / 'DOC' / 'Скоба-Стыковочная'

    saving_groups = utils.prepare_saving_groups_for_project(project_dir.with_name('Мастерская-V4.SLDASM'), PassOnlyDockingBracketComponentsFromLeftSide())

    shutil.rmtree(doc_folder, ignore_errors=True)

    steel_sheet_3mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_3mm.prepare_data([r"Крепёжная-Планка скоба-стыковочная"], step=True, dxf=True, save_folder_opt=doc_folder, quantity_evaluator=lambda x: x + 25)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(f"Скоба-Стыковочная") \
        .add_3mm_steel_sheet_table(steel_sheet_3mm) \
        .create(doc_folder)

    assert utils.prepare_archive(root_dir=doc_folder,
                                 archive_dir=doc_folder.parent,
                                 archive_name=f"ТЗ на производство стыковочных скоб для инженерной стенки с левой стороны",
                                 archive_type='zip',
                                 add_date=True)

@utils.sw_task(doc_string=f"Prepare steel-manufacturing documentation for the project 'Фрезерная-Направляющая'")
def prepare_milling_guide_doc(ctx):
    project_dir = pathlib.Path(__file__)
    doc_folder = project_dir.parent / 'DOC' / 'Фрезерная-Направляющая'

    saving_groups = utils.prepare_saving_groups_for_project(project_dir.with_name('Крепёжная-Планка.SLDPRT'))

    shutil.rmtree(doc_folder, ignore_errors=True)

    steel_sheet_2mm = utils.doc_creator.StandardElementsTable(saving_groups)
    steel_sheet_2mm.prepare_data([r"Крепёжная-Планка фрезерная-направляющая"], step=True, dxf=False, save_folder_opt=doc_folder)

    utils.doc_creator.CNCMetalLaserCuttingDocCreator(f"Фрезерная-Направляющая") \
        .add_2mm_steel_sheet_table(steel_sheet_2mm) \
        .create(doc_folder)



collection = invoke.Collection()
collection.add_task(prepare_docking_bracket_doc)
collection.add_task(prepare_milling_guide_doc)

# add sub tasks
projects.load_project_task(collection, pathlib.Path(__file__).parent / 'left_side.py')
