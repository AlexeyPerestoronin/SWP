import re
import shutil
import invoke
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Монополия'
PROJECT_DIR = pathlib.Path(__file__)
DOC_FOLDER = PROJECT_DIR.parent / 'DOC' / PROJECT_NAME


@utils.sw_task(doc_string=f"Prepare wood-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_game_field_doc(ctx):
    wood_bodies = r'(путь-внешний|путь-внутренний|круг|подложка)'
    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_project(PROJECT_DIR.parent / 'игровое поле' / 'Карта-v1.SLDPRT')
    unique_bodies = [unique_bodies for unique_bodies in unique_bodies_manager.unique_bodies if re.match(wood_bodies, unique_bodies[0][0].name)]
    saving_groups = utils.prepare_saving_groups(unique_bodies)

    doc_folder = DOC_FOLDER / 'Manufacturing' / 'Wood'
    shutil.rmtree(doc_folder, ignore_errors=True)

    polywood = utils.doc_creator.StandardElementsTable(saving_groups)
    polywood.prepare_data([f"Карта {wood_bodies}"], step=True, dxf=False, save_folder_opt=doc_folder)
    polywood_material_info = utils.doc_creator.MaterialInfoTable()
    polywood_material_info.prepare_data([
        ["материал", "фанера"],
        ["толщина", "10мм"],
        ["сорт", "1 (первый)"],
        ["наличие ламинирования", "допускается, но только двустороннее"],
        ["влагозащита", "допускается, но не обязательно"],
    ])

    utils.doc_creator.CNCWoodMillingDocCreator(f"Монополия") \
        .add_table('Фанера 10мм', polywood, polywood_material_info) \
        .create(doc_folder)

    assert utils.prepare_archive(root_dir=doc_folder,
                                 archive_dir=DOC_FOLDER.parent,
                                 archive_name=f"ТЗ на производство деревянных деталей для игрового поля монополии",
                                 archive_type='zip',
                                 add_date=True)


@utils.sw_task(doc_string=f"Prepare plastic-manufacturing documentation for the project '{PROJECT_NAME}'")
def prepare_organizers_doc(ctx):
    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_project(PROJECT_DIR.parent / 'базовые элементы/Органайзер-Карточек.SLDPRT')
    saving_groups = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies)

    doc_folder = DOC_FOLDER / 'Manufacturing' / 'PLA'
    shutil.rmtree(doc_folder, ignore_errors=True)

    pla = utils.doc_creator.StandardElementsTable(saving_groups)
    pla.prepare_data([f"Органайзер-Карточек .*"], step=True, dxf=False, save_folder_opt=doc_folder)

    utils.doc_creator.CNC3DPrintingDocCreator(f"Монополия") \
        .add_PLA(pla) \
        .create(doc_folder)


collection = invoke.Collection()
collection.add_task(prepare_game_field_doc)
collection.add_task(prepare_organizers_doc)
