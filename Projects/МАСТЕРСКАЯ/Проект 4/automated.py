import re
import invoke
import pathlib

from pyswx.api.swconst.enumerations import SWDocumentTypesE
from tabulate import tabulate

import utils
import check

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
    project_path = pathlib.Path(__file__).with_name('Инженерная-Стенка.SLDASM')
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

        prepare_step_file = True
        if prepare_step_file:
            for (reference_body, quantity, reference_component, step_path) in save_paths_and_bodies:
                try:
                    utils.save_body_from_component_like_step(reference_component, reference_body, step_path)
                    utils.SUCCESS.log_line(f"step file created: {step_path}")
                except Exception as error:
                    utils.ERROR.log_line(f"step file wasn't created: {error}")

        prepare_doc_info = True
        if prepare_doc_info:
            profile_tube_50_25_2 = []
            profile_tube_50_50_4 = []
            steel_sheet_4 = []
            steel_sheet_6 = []
            undefined = []
            
            for (_reference_body, quantity, _reference_component, step_path) in save_paths_and_bodies:
                component_full_name = step_path.name
                if bool(re.match(r"Опорная-Колонна каркас-полочек.+?", component_full_name)):
                    profile_tube_50_25_2.append([component_full_name, quantity])
                elif bool(re.match(r"Опорная-Колонна (колонна|каркас-основания).*?", component_full_name)):
                    profile_tube_50_50_4.append([component_full_name, quantity])
                elif bool(re.match(r"Инженерная-Стенка Горизонтальный-Каркас г-опора", component_full_name)):
                    profile_tube_50_50_4.append([component_full_name, quantity])
                elif bool(re.match(r"Опорная-Колонна кронштейн-потолочной-балки", component_full_name)):
                    steel_sheet_4.append([component_full_name, quantity])
                elif bool(re.match(r"Инженерная-Стенка Верстак.+?", component_full_name)):
                    steel_sheet_6.append([component_full_name, quantity])
                else:
                    undefined.append([component_full_name, quantity])

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
                tabulate(profile_tube_50_25_2, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe"),
                "",
                "## Профильная труба 50x50x4мм",
                "[Справочная ссылка для материала](https://купитьметалл.рф/product/truba-kvadratnaya-50x50x4)",
                "",
                tabulate(profile_tube_50_50_4, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe"),
                "",
                "## Лист стальной горячекатанный 4мм",
                "[Справочная ссылка для материала](https://купитьметалл.рф/product/list-gk-4-st3sp-ps-5)",
                "",
                tabulate(steel_sheet_4, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe"),
                "",
                "## Лист стальной горячекатанный 6мм",
                "[Справочная ссылка для материала](https://купитьметалл.рф/product/list-gk-6-st3sp-ps-5)",
                "",
                tabulate(steel_sheet_6, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe"),
            ]
            
            if len(undefined) > 0:
                content.extend([
                        "",
                        "## Не учтённые элементы",
                        tabulate(undefined, headers=["Деталь-файл", "Количество (штук)"], tablefmt="pipe"),
                    ]
                )

            doc_file = save_folder / pathlib.Path('README.md')
            with open(doc_file, "w", encoding="utf-8") as file:
                file.write("\n".join(content))


collection = invoke.Collection()
collection.add_task(make_doc, name="make-doc")