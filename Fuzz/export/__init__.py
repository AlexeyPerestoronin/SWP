import invoke, pathlib
from typing import List, Tuple, Set, TypeAlias
from pyswx.api.sldworks.interfaces import IModelDoc2, IComponent2, IBody2
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWSaveAsOptionsE, SWSaveAsVersionE, SWBodyTypeE

import utils
import check

SavingGroup: TypeAlias = Tuple[IBody2, IComponent2, pathlib.Path]
SavingGroups: TypeAlias = List[SavingGroup]


def prepare_saving_groups(unique_bodies: utils.UniqueBodiesManager.UniqueBodies, save_folder: pathlib.Path) -> SavingGroups:
    """
    Prepare unique STEP export paths for groups of identical bodies across components.
    """
    result: SavingGroups = []
    for same_bodies in unique_bodies:
        (reference_body, reference_component) = same_bodies[0]
        assembly_names_set: Set[str] = set()
        models_names_set: Set[str] = set()
        folders_names_set: Set[str] = set()
        bodies_names_set: Set[str] = set()
        utils.STATUS.log_line(f"Detected {len(same_bodies)} same bodies:")
        for same_body in same_bodies:
            (reference_body, reference_component) = same_body
            utils.STATUS.log_line(f"* body '{reference_body.name}' in component '{reference_component.name2}'")
            bodies_names_set.add(utils.validate_and_parse_body_name(reference_body).main_name)
            if not reference_component.referenced_configuration:
                body_folder = utils.detect_folder_for_body_in_model(reference_component.get_model_doc2(), reference_body)
            else:
                body_folder = utils.detect_folder_for_body_in_component(reference_component, reference_body)
            if body_folder:
                folders_names_set.add(body_folder)
            valid_model_name = utils.validate_and_parse_component_name(reference_component).valid_model_name
            models_names_set.add(valid_model_name.model_name)
            if valid_model_name.assembly_name:
                assembly_names_set.add(valid_model_name.assembly_name)

        step_file_name = "{assembly_name} {model_name} {folder_name} {body_name} [{quantity}]".format(
            assembly_name='+'.join(assembly_names_set),
            model_name='+'.join(models_names_set),
            folder_name='+'.join(folders_names_set),
            body_name='+'.join(bodies_names_set),
            quantity=len(same_bodies),
        )\
        .replace('  ', ' ', -1)\
        .strip()

        new_save_path = save_folder / pathlib.Path(step_file_name).with_suffix(".step")
        for (body, _, save_path) in result:
            if new_save_path == save_path:
                raise Exception(f"step path '{new_save_path}' for rep-body '{reference_body.name}' is already reserved by body '{body.name}'")
        result.append((reference_body, reference_component, new_save_path))
        utils.STATUS.log_line(f"+ they common save path is '{new_save_path}'")
    return result


@invoke.task(
    help={
        "path": "path to SW-part-project which bodies should be saved as *.step",
        "save-subfolder": "subfolder in model-folder where step filles should be saved (default is None = in the root folder of the SW-project)",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step_from_part(ctx, path: str = None, save_subfolder: str = None, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    """
    check.project_naming(ctx, path)

    root_model = utils.open_document(path, SWDocumentTypesE.SW_DOC_PART).root_model

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_model(root_model)

    save_folder = root_model.get_path_name().parent
    if save_subfolder:
        save_folder = save_folder / pathlib.Path(save_subfolder)

    save_paths_and_bodies = prepare_saving_groups(unique_bodies_manager.unique_bodies, save_folder)

    if execute:
        save_folder.mkdir(parents=True, exist_ok=True)
        for reference_component in save_folder.iterdir():
            reference_component.unlink(missing_ok=True)

        for (reference_body, reference_component, step_path) in save_paths_and_bodies:
            try:
                utils.save_body_from_component_like_step(reference_component, reference_body, step_path)
                utils.SUCCESS.log_line(f"step file created: {step_path}")
            except Exception as error:
                utils.ERROR.log_line(f"step file wasn't created: {error}")


@invoke.task(
    help={
        "path": "path to SW-assembly-project which bodies should be saved as *.step",
        "save-subfolder": "subfolder in model-folder where step filles should be saved (default is None = in the root folder of the SW-project)",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step_from_assembly(ctx, path: str = None, save_subfolder: str = None, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    """
    check.project_naming(ctx, path)

    root_assembly = utils.open_document(path, SWDocumentTypesE.SW_DOC_ASSEMBLY).root_assembly

    unique_bodies_manager = utils.UniqueBodiesManager()
    unique_bodies_manager.add_from_assembly(root_assembly)

    save_folder = root_assembly.get_path_name().parent
    if save_subfolder:
        save_folder = save_folder / pathlib.Path(save_subfolder)

    save_paths_and_bodies = prepare_saving_groups(unique_bodies_manager.unique_bodies, save_folder)

    if execute:
        save_folder.mkdir(parents=True, exist_ok=True)
        for reference_component in save_folder.iterdir():
            reference_component.unlink(missing_ok=True)

        for (reference_body, reference_component, step_path) in save_paths_and_bodies:
            try:
                utils.save_body_from_component_like_step(reference_component, reference_body, step_path)
                utils.SUCCESS.log_line(f"step file created: {step_path}")
            except Exception as error:
                utils.ERROR.log_line(f"step file wasn't created: {error}")


collection = invoke.Collection()
collection.add_task(step_from_part, name="step-from-part")
collection.add_task(step_from_assembly, name="step-from-assembly")
