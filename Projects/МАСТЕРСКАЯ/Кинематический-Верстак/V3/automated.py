import re
import shutil
import invoke
import pathlib

from typing import List, Tuple
from pyswx.api.swconst.enumerations import SWDocumentTypesE
from tabulate import tabulate

import utils
import utils.doc_creator
import check


def make_md_tabla(data: List[Tuple[str, int]]):
    sorted_data = sorted(data, key=lambda x: x[0])
    return tabulate(sorted_data, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe")


@invoke.task(help={
    "extended-content": "include additional section in ready documentation (default: True)",
})
def make_doc(ctx, extended_content: bool = True):
    """
    Prepare MarkDown documentation:
    ../DOC
        README.md
        file-1.step
        ...
        file-N.step
    """
    project_name = 'Верстак'
    project_path = pathlib.Path(__file__).with_name(f'{project_name}.SLDPRT')
    check.project_naming(ctx, project_path)
    root_model = utils.open_document(project_path, SWDocumentTypesE.SW_DOC_PART).root_model

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_model(root_model)

    if extended_content:
        utils.warning.log_line(f"Prepare extended content for documentation")
        extended_project_path = pathlib.Path('C:\MyLife\SWP\Projects\МАСТЕРСКАЯ\Верстак-Dim1000x600x50.SLDPRT')
        check.project_naming(ctx, extended_project_path)
        root_model = utils.open_document(extended_project_path, SWDocumentTypesE.SW_DOC_PART).root_model
        unique_bodies_manager.add_from_model(root_model)

    save_folder = project_path.with_name(f'{project_name}-DOC')
    saving_groups = utils.prepare_saving_groups_2(unique_bodies_manager.unique_bodies)

    execute = True
    if execute:
        shutil.rmtree(save_folder, ignore_errors=True)

        td_preparator = utils.doc_creator.CNCLaserCuttingDocCreator.TableDataPreparator(
            saving_groups, save_folder, lambda expression, component_full_name: bool(re.match(f"{expression}", component_full_name)))
        td_preparator.unused([f"Верстак-Dim1000x600x50 (квадрат-6мм-2x2|т-элемент-6мм-3x3|уголок-6мм-3x3|столешница)"])
        utils.doc_creator.CNCLaserCuttingDocCreator(project_name) \
            .add_table('Лист стальной горячекатанный 8мм', td_preparator.prepare(True, True, [f"{project_name} каркас столешница"]), 'https://купитьметалл.рф/product/list-gk-8-st3sp-ps-5') \
            .add_table('Лист стальной горячекатанный 6мм', td_preparator.prepare(True, True, [f"{project_name} каркас юбка-.+", f"{project_name} ножки .+", f"{project_name} .+ рж-.+"]), 'https://купитьметалл.рф/product/list-gk-6-st3sp-ps-5') \
            .add_table('Лист стальной горячекатанный 4мм', td_preparator.prepare(True, True, [f"Верстак-Dim1000x600x50 крепёжный-уголок"], quantity_expression=lambda x :  16), 'https://купитьметалл.рф/product/list-gk-4-st3sp-ps-5') \
            .add_table('Труба стальная прокатная 150-150-5мм', td_preparator.prepare(True, False, [f"{project_name} каркас колонна-опорная"]), 'https://купитьметалл.рф/product/truba-kvadratnaya-150x150x5') \
            .add_table('Труба стальная прокатная 100-50-5мм', td_preparator.prepare(True, False, [f"{project_name} каркас колонна-ножек-.+"]), 'https://купитьметалл.рф/product/truba-pryamougol-100x50x5') \
            .add_table('Не учтённые элементы', td_preparator.unclassified()) \
            .create(save_folder)


collection = invoke.Collection()
collection.add_task(make_doc, name="make-doc")
