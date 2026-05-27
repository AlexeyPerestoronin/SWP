import re
import invoke
import pathlib

from typing import List, Tuple
from pyswx.api.swconst.enumerations import SWDocumentTypesE
from tabulate import tabulate

import utils
import check

def make_md_tabla(data: List[Tuple[str, int]]):
    sorted_data = sorted(data, key=lambda x: x[0])
    return tabulate(sorted_data, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe")

@invoke.task()
def make_doc(ctx):
    """
    Prepare MarkDown documentation in:
    ../DOC
        README.md
        file-1.step
        ...
        file-N.step
    """
    project_path = pathlib.Path(__file__).with_name('Модель-Мастерской-IV.SLDASM')
    check.project_naming(ctx, project_path)

    root_assembly = utils.open_document(project_path, SWDocumentTypesE.SW_DOC_ASSEMBLY).root_assembly

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_assembly(root_assembly)

    save_folder = project_path.with_name('DOC')
    save_paths_and_bodies = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies, save_folder)

    execute = True
    if execute:
        save_folder.mkdir(parents=True, exist_ok=True)
        for reference_component in save_folder.iterdir():
            reference_component.unlink(missing_ok=True)

        profile_tube_50_25_2 = []
        profile_tube_50_50_4 = []
        steel_sheet_4 = []
        steel_sheet_6 = []
        undefined = []

        for (reference_body, quantity, reference_component, step_path) in save_paths_and_bodies:
            component_full_name = step_path.name

            try_detect = lambda expression: bool(re.match(expression, component_full_name))

            if try_detect(r"Гаражный-Комплекс.+?") \
            or try_detect(r"Верстак-Dim1000x600x50 столешница") :
                utils.INFO.log_line(f"detected DOC-unused step-file: {step_path}")
                continue

            # profile_tube_50_25_2
            elif try_detect(r"Опорная-Колонна каркас-полочек.+?") \
              or try_detect(r"Профильный-Каркас Крепёжная-Планка планка-(левая|правая)"):
                profile_tube_50_25_2.append([component_full_name, quantity])

            # profile_tube_50_50_4
            elif try_detect(r"Опорная-Колонна каркас (колонна|каркас-основания-(I|II|III))-(R|L)") \
              or try_detect(r"Перфорированная-Стяжка стяжка-\d+"):
                profile_tube_50_50_4.append([component_full_name, quantity])

            elif try_detect(r"Инженерная-Стенка Горизонтальный-Каркас г-опора"):
                profile_tube_50_50_4.append([component_full_name, quantity])

            # steel_sheet_4
            elif try_detect(r"Опорная-Колонна кронштейн-потолочной-балки") \
              or try_detect(r"Опорная-Колонна кк-горизонтальной-балки") \
              or try_detect(r"Профильный-Каркас Крепёжная-Планка крепёжное-окно") \
              or try_detect(r"Перфорированная-Стяжка ушко"):
                steel_sheet_4.append([component_full_name, quantity])

            elif try_detect(r"Опорная-Колонна кк-полочки-верхний"):
                # 5 (полочек для опоры) * 4 (опоры на верстаке) * 2 (верстака) = 40
                steel_sheet_4.append([component_full_name, 40])

            elif try_detect(r"Опорная-Колонна кк-полочки-нижний"):
                # 5 (полочек на опоре) * 4 (опоры на верстаке) * 2 (верстака) = 40
                steel_sheet_4.append([component_full_name, 40])

            # steel_sheet_6
            elif try_detect(r"Верстак-Dim1000x600x50 т-элемент-6мм-3x3"):
                steel_sheet_6.append([component_full_name, 10])

            elif try_detect(r"Верстак-Dim1000x600x50 уголок-6мм-3x3"):
                steel_sheet_6.append([component_full_name, 10])

            elif try_detect(r"Верстак-Dim1000x600x50 квадрат-6мм-2x2"):
                steel_sheet_6.append([component_full_name, 10])

            else:
                utils.WARNING.log_line(f"detected DOC-unclassified step-file: {step_path}")
                undefined.append([component_full_name, quantity])

            try:
                utils.save_body_from_component_like_step(reference_component, reference_body, step_path)
                utils.SUCCESS.log_line(f"step file created: {step_path}")
            except Exception as error:
                utils.ERROR.log_line(f"step file wasn't created: {error}")

        content = [
            "# Техническое задания на изготовление металлических деталей для «Инженерная Стенка» методом ЧПУ лазерной резки",
            "",
            "❗ **Геометрические параметры всех деталей в STEP-файлах учитывают технологические отступы:**",
            "Траектория реза задается относительно контура детали следующим образом:",
            "- для сквозных отверстий, пазов и иных внутренних элементов, рез выполняется по внутреннему контуру (материал удаляется изнутри контура);",
            "- для наружного контура детали (отрезка заготовки), рез выполняется по внешнему контуру (материал удаляется снаружи контура).",
            "",
            "## Профильная труба 50x25x2мм",
            "[Справочная ссылка для материала](https://купитьметалл.рф/product/truba-pryamougol-50x25x2)",
            "",
            make_md_tabla(profile_tube_50_25_2),
            "",
            "## Профильная труба 50x50x4мм",
            "[Справочная ссылка для материала](https://купитьметалл.рф/product/truba-kvadratnaya-50x50x4)",
            "",
            make_md_tabla(profile_tube_50_50_4),
            "",
            "## Лист стальной горячекатанный 4мм",
            "[Справочная ссылка для материала](https://купитьметалл.рф/product/list-gk-4-st3sp-ps-5)",
            "",
            make_md_tabla(steel_sheet_4),
            "",
            "## Лист стальной горячекатанный 6мм",
            "[Справочная ссылка для материала](https://купитьметалл.рф/product/list-gk-6-st3sp-ps-5)",
            "",
            make_md_tabla(steel_sheet_6),
        ]
        
        if len(undefined) > 0:
            content.extend([
                    "",
                    "## Не учтённые элементы",
                    make_md_tabla(undefined),
                ]
            )

        doc_file = save_folder / pathlib.Path('README.md')
        with open(doc_file, "w", encoding="utf-8") as file:
            file.write("\n".join(content))


collection = invoke.Collection()
collection.add_task(make_doc, name="make-doc")