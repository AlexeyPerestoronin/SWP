import invoke
import shutil
import pathlib

import utils
import utils.doc_creator

PROJECT_NAME = 'Платформа-Лифтовая-Поворотная-Концепт'
CONFIGURATION_NAME = None
QUANTITY_EVALUATOR = lambda x: x
PROJECT_PATH = pathlib.Path(__file__).with_name(f'{PROJECT_NAME}.SLDPRT')
DOC_FOLDER = PROJECT_PATH.with_name(f'{PROJECT_NAME} ({CONFIGURATION_NAME}) DOC-x{QUANTITY_EVALUATOR(1)}')


@utils.sw_task(doc_string=f"Clear folder with '{PROJECT_NAME}'-project documentation")
def clear_doc_folder(ctx):
    shutil.rmtree(DOC_FOLDER, ignore_errors=True)


@utils.sw_task(doc_string=f"Prepare solid-bodies-saving-groups for '{PROJECT_NAME}'-project")
def parse_saving_groups(ctx):
    if not hasattr(ctx, 'saving_groups'):
        unique_bodies_manager = utils.UniqueBodiesManager()
        unique_bodies_manager.add_from_project(PROJECT_PATH, configuration=CONFIGURATION_NAME)
        saving_groups = utils.prepare_saving_groups(unique_bodies_manager.unique_bodies)
        setattr(ctx, 'saving_groups', saving_groups)


@utils.sw_task(doc_string=f"Prepare manufacturing documentation for the project '{PROJECT_NAME}'", pre=[parse_saving_groups])
def prepare_manufacturing_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    execute = True
    if execute:
        manufacturing_doc_folder = DOC_FOLDER / 'Manufacturing'
        shutil.rmtree(manufacturing_doc_folder, ignore_errors=True)

        pla = utils.doc_creator.LaserCuttingManufacturingElementsTable(saving_groups)
        pla.prepare_data([f"{PROJECT_NAME} .+"], step=True, dxf=False, save_folder_opt=manufacturing_doc_folder, quantity_evaluator=QUANTITY_EVALUATOR)

        utils.doc_creator.CNCLaserCuttingDocCreator(PROJECT_NAME) \
            .add_table('3D-Printing PLA', pla) \
            .create(manufacturing_doc_folder)


@utils.sw_task(doc_string=f"Wrapping documentation for the project '{PROJECT_NAME}' to ZIP archive")
def convert_doc_to_zip(ctx):
    DOC_FOLDER.with_suffix('.zip').unlink(missing_ok=True)
    shutil.make_archive(base_name=DOC_FOLDER, root_dir=DOC_FOLDER, format='zip')


@utils.sw_task(doc_string=f"Make complex documentation for '{PROJECT_NAME}'", pre=[clear_doc_folder, parse_saving_groups, prepare_manufacturing_doc, convert_doc_to_zip])
def make_doc(ctx):
    saving_groups = getattr(ctx, 'saving_groups')
    for saving_group in saving_groups:
        if saving_group.mark is None:
            save_file_name = str(saving_group.save_file_name)
            unused_elements = []
            if save_file_name in unused_elements:
                utils.logger.info.log_line(f"detected unused elements '{save_file_name}'")
            else:
                utils.logger.error.log_line(f"detected unclassified elements '{save_file_name}'")


collection = invoke.Collection()
collection.add_task(clear_doc_folder, name="clear-doc-folder")
collection.add_task(parse_saving_groups, name="parse-saving-groups")
collection.add_task(prepare_manufacturing_doc, name="prepare-manufacturing-doc")
collection.add_task(convert_doc_to_zip, name="convert-doc-to-zip")
collection.add_task(make_doc, name="make-doc")
