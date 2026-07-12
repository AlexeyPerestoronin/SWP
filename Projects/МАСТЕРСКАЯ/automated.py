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
    save_paths_and_bodies = utils.prepare_saving_groups_2(unique_bodies_manager.unique_bodies)

    execute = True
    if execute:
        save_folder.mkdir(parents=True, exist_ok=True)
        for reference_component in save_folder.iterdir():
            reference_component.unlink(missing_ok=True)

        steel_sheet_6mm = []
        steel_sheet_4mm = []
        undefined = []

        for (reference_body, quantity, reference_component, save_file_name) in save_paths_and_bodies:
            component_full_name = str(save_file_name)

            try_detect = lambda expression: bool(re.match(f"Верстак-Dim1000x600x50 {expression}", component_full_name))

            if try_detect(r"столешница"):
                utils.info.log_line(f"detected DOC-unused step-file: {component_full_name}")
                continue
            # steel_sheet_6mm
            elif try_detect(r".+-6мм.+"):
                steel_sheet_6mm.append([component_full_name, 10])
            # steel_sheet_4mm
            elif try_detect(r"крепёжный-уголок"):
                steel_sheet_4mm.append([component_full_name, 4])
            else:
                utils.warning.log_line(f"detected DOC-unclassified step-file: {save_file_name}")
                undefined.append([component_full_name, quantity])

            step_file = save_folder / save_file_name.with_suffix('.step')
            utils.save_body_from_component_like_step(reference_component, reference_body, step_file)
            utils.success.log_line(f"STEP file created: {step_file}")
            dxf_file = save_folder / save_file_name.with_suffix('.dxf')
            utils.save_body_from_component_like_dxf(reference_component, reference_body, dxf_file)
            utils.success.log_line(f"DXF file created: {dxf_file}")

        content = [
            "# Техническое задания на изготовление металлических деталей для «Верстак-Dim1000x600x50» методом ЧПУ лазерной резки",
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
            "## Лист стальной горячекатанный 6мм",
            "[Справочная ссылка для материала](https://купитьметалл.рф/product/list-gk-6-st3sp-ps-5)",
            "",
            make_md_tabla(steel_sheet_6mm),
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
