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


@invoke.task(help={
    "extended-content": "include additional section in ready documentation (default: True)",
})
def make_doc_for_workbench_1000_600(ctx, extended_content: bool = True):
    """
    Prepare MarkDown documentation:
    ../DOC
        README.md
        file-1.step
        ...
        file-N.step
    """

    project_path = pathlib.Path(__file__).with_name('Верстак-Dim1000x600x50.SLDPRT')
    check.project_naming(ctx, project_path)
    root_model = utils.open_document(project_path, SWDocumentTypesE.SW_DOC_PART).root_model

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_model(root_model)

    save_folder = project_path.with_name('DOC_for_workbench_1000x600')
    save_paths_and_bodies = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies, save_folder)

    execute = True
    if execute:
        save_folder.mkdir(parents=True, exist_ok=True)
        for reference_component in save_folder.iterdir():
            reference_component.unlink(missing_ok=True)

        steel_sheet_4mm = []
        undefined = []

        for (reference_body, quantity, reference_component, step_path) in save_paths_and_bodies:
            component_full_name = step_path.name

            try_detect = lambda expression: bool(re.match(f"{expression}", component_full_name))

            # steel_sheet_8mm
            if try_detect(r"nothing to find"):
                pass
            else:
                utils.warning.log_line(f"detected DOC-unclassified step-file: {step_path}")
                undefined.append([component_full_name, quantity])

            try:
                utils.save_body_from_component_like_step(reference_component, reference_body, step_path)
                utils.success.log_line(f"step file created: {step_path}")
            except Exception as error:
                utils.error.log_line(f"step file wasn't created: {error}")

        content = [
            "# Техническое задания на изготовление металлических деталей для «Верстак-Dim1000x600x50» методом ЧПУ лазерной резки",
            "",
            "❗ **Геометрические параметры всех деталей в STEP-файлах учитывают технологические отступы:**",
            "Траектория реза задается относительно контура детали следующим образом:",
            "- для сквозных отверстий, пазов и иных внутренних элементов, рез выполняется по внутреннему контуру (материал удаляется изнутри контура);",
            "- для наружного контура детали (отрезка заготовки), рез выполняется по внешнему контуру (материал удаляется снаружи контура).",
            "",
            "❗В случае, если фактические параметры металлических заготовок будут отличаться от заданных, прошу сообщить отдельно для внесения корректировок в проект изделия!",
            "",
            "## Лист стальной горячекатанный 4мм",
            "[Справочная ссылка для материала](https://купитьметалл.рф/product/list-gk-4-st3sp-ps-5)",
            "",
            make_md_tabla(steel_sheet_4mm),
        ]

        if len(undefined) > 0:
            content.extend([
                "",
                "## Не учтённые элементы",
                make_md_tabla(undefined),
            ])

        doc_file = save_folder / pathlib.Path('README.md')
        with open(doc_file, "w", encoding="utf-8") as file:
            file.write("\n".join(content))


collection = invoke.Collection()
collection.add_task(make_doc_for_workbench_1000_600, name="make-doc-for-workbench-1000-600")
