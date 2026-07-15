import re
import shutil
import invoke
import pathlib

import utils
import utils.doc_creator


@invoke.task()
def create_metal_tech_task(ctx):
    """
    Creates tech-task for metal processing:
    ../DOC
        README.md
        file-1.step
        ...
        file-N.step
    """
    project_name = 'Z-Лифт-V3'
    project_path = pathlib.Path(__file__).with_name(f'{project_name}.SLDPRT')
    doc_save_folder = project_path.with_name(f'{project_name}-DOC')

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_project(project_path)
    saving_groups = utils.prepare_saving_groups_2(unique_bodies_manager.unique_bodies)

    execute = True
    if execute:
        shutil.rmtree(doc_save_folder, ignore_errors=True)

        td_preparator = utils.doc_creator.CNCLaserCuttingDocCreator.TableDataPreparator(
            saving_groups, doc_save_folder, lambda expression, component_full_name: bool(re.match(f"{project_name} {expression}", component_full_name)))
        td_preparator.unused([r"пан-подшипники+инв-подшипники .+"])
        utils.doc_creator.CNCLaserCuttingDocCreator(project_name) \
            .add_table('Лист стальной горячекатанный 4мм', td_preparator.prepare(True, True, [r".+"]), 'https://купитьметалл.рф/product/list-gk-4-st3sp-ps-5') \
            .add_table('Не учтённые элементы', td_preparator.unclassified()) \
            .create(doc_save_folder)


collection = invoke.Collection()
collection.add_task(create_metal_tech_task, name="create-metal-tech-task")
