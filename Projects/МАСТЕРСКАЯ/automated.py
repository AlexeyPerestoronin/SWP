import re
import shutil
import invoke
import pathlib

from collections.abc import Callable
from typing import List, Tuple, Optional, TypeAlias, Protocol
from pyswx.api.swconst.enumerations import SWDocumentTypesE
from tabulate import tabulate

import utils
import check


class IDocumentCreator(Protocol):
    """TODO: provide some comment"""

    def create(self, doc_file_path: pathlib.Path):
        ...


class CNCLaserCuttingDocCreator(IDocumentCreator):
    """TODO: provide some comment"""

    class TableDataPreparator:
        """TODO: provide some comment"""

        TableData: TypeAlias = List[Tuple[str, bool, bool, int]]

        def __init__(self, saving_groups: utils.SavingGroups, save_folder: pathlib.Path, base_matcher: Callable[[str, str], bool]):
            self.__marked_saving_groups = [['', saving_group] for saving_group in saving_groups]
            self.__save_folder = save_folder
            self.__base_matcher = base_matcher
            # ---
            self.__save_folder.mkdir(parents=True, exist_ok=True)

        def prepare(self,
                    step: bool,
                    dxf: bool,
                    match_expressions: List[str] = [],
                    *,
                    quantity_expression: Callable[[int], int] = lambda q: q,
                    unused_only: bool = False) -> TableData:
            table_data = []
            for (mark, saving_group) in self.__marked_saving_groups:
                (reference_body, quantity, reference_component, save_file_name) = saving_group
                component_full_name = str(save_file_name)
                if unused_only:
                    if mark != '':
                        table_data.append([component_full_name, step, dxf, quantity_expression(quantity)])
                    else:
                        continue
                for match_expression in match_expressions:
                    if self.__base_matcher(match_expression, component_full_name):
                        if mark != '':
                            raise Exception(f"'{component_full_name}' is already passed by '{mark}'-mark")
                        if step:
                            step_file = self.__save_folder / 'STEP' / save_file_name.with_suffix('.step')
                            utils.save_body_from_component_like_step(reference_component, reference_body, step_file)
                            utils.success.log_line(f"STEP file created: {step_file}")
                        if dxf:
                            dxf_file = self.__save_folder / 'DXF' / save_file_name.with_suffix('.dxf')
                            utils.save_body_from_component_like_dxf(reference_component, reference_body, dxf_file)
                            utils.success.log_line(f"DXF file created: {dxf_file}")
                        mark = 'unused' if step is False and dxf is False else str(match_expression)
                        table_data.append([component_full_name, step, dxf, quantity_expression(quantity)])
                        break
            return table_data

        def unused(self, match_expressions: List[str]):
            self.prepare(False, False, match_expressions)

        def unclassified(self) -> TableData:
            return self.prepare(False, False, unused_only=True)

    def __init__(self, project_name: str):
        self.__content = [
            f"# Техническое задания на изготовление металлических деталей для «{project_name}» методом ЧПУ лазерной резки",
            "",
            "❗ **Геометрические параметры всех деталей в STEP/DXF-файлах учитывают технологические отступы:**",
            "Траектория реза задается относительно контура детали следующим образом:",
            "- для сквозных отверстий, пазов и иных внутренних элементов, рез выполняется по внутреннему контуру (материал удаляется изнутри контура);",
            "- для наружного контура детали (отрезка заготовки), рез выполняется по внешнему контуру (материал удаляется снаружи контура).",
            "",
            "❗В случае если деталь изготавливается при помощи резки листового металла, документация содержит соответствующий DXF файл!",
            "",
            "❗В случае, если фактические параметры металлических заготовок будут отличаться от заданных, прошу сообщить отдельно для внесения корректировок в проект изделия!",
            "",
        ]

    def add_table(self, table_header: str, table_data: TableDataPreparator.TableData, material_link: Optional[str] = None) -> 'CNCLaserCuttingDocCreator':
        try:
            if len(table_data) > 0:
                table_data = sorted(table_data, key=lambda x: x[0])
                table_data = tabulate(table_data, headers=["Деталь-файл", "STEP", "DXF", "Количество (штук)"], tablefmt="pipe")
                self.__content.extend([
                    f"## {table_header}",
                    f"[Справочная ссылка для материала]({material_link})\n" if material_link else "",
                    f"{table_data}",
                    "",
                ])
        except Exception as error:
            raise RuntimeError(f"cannot add '{table_header}'-table in DOC: {error}")
        return self

    def create(self, save_folder: pathlib.Path):
        doc_file_path = save_folder / 'CNC_Laser_Metal_Cutting.md'
        try:
            with open(doc_file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(self.__content))
        except Exception as error:
            raise RuntimeError(f"cannot create DOC in {doc_file_path}: {error}")


@invoke.task()
def make_doc_for_workbench_1000_600(ctx):
    """
    Prepare MarkDown documentation:
    ../DOC
        README.md
        file-1.step
        ...
        file-N.step
    """
    project_name = 'Верстак-Dim1000x600x50'
    project_path = pathlib.Path(__file__).with_name(f'{project_name}.SLDPRT')
    check.project_naming(ctx, project_path)
    root_model = utils.open_document(project_path, SWDocumentTypesE.SW_DOC_PART).root_model

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_model(root_model)

    save_folder = project_path.with_name(f'{project_name}-DOC')
    saving_groups = utils.prepare_saving_groups_2(unique_bodies_manager.unique_bodies)

    execute = True
    if execute:
        shutil.rmtree(save_folder, ignore_errors=True)

        td_preparator = CNCLaserCuttingDocCreator.TableDataPreparator(saving_groups, save_folder,
                                                                      lambda expression, component_full_name: bool(re.match(f"{project_name} {expression}", component_full_name)))
        td_preparator.unused([r"столешница"])
        CNCLaserCuttingDocCreator(project_name) \
            .add_table('Лист стальной горячекатанный 6мм', td_preparator.prepare(True, True, [r".+-6мм.+"], quantity_expression=lambda x :  10), 'https://купитьметалл.рф/product/list-gk-6-st3sp-ps-5') \
            .add_table('Лист стальной горячекатанный 4мм', td_preparator.prepare(True, True, [r"крепёжный-уголок"], quantity_expression=lambda x :  16), 'https://купитьметалл.рф/product/list-gk-4-st3sp-ps-5') \
            .add_table('Не учтённые элементы', td_preparator.unclassified()) \
            .create(save_folder)


collection = invoke.Collection()
collection.add_task(make_doc_for_workbench_1000_600, name="make-doc-for-workbench-1000-600")
