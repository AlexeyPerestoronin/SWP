import invoke, pathlib
from typing import List, Tuple
from pyswx.api.sldworks.interfaces import IAssemblyDoc, IModelDoc2, IComponent2, IBody2
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWSaveAsOptionsE, SWSaveAsVersionE, SWBodyTypeE

import utils
import check


def make_common_save_path_for_unique_bodies(parent_model: IModelDoc2, save_folder: pathlib.Path, bodies: List[IBody2]) -> List[Tuple[pathlib.Path, IBody2, int]]:
    """
    TODO: need to provide some comment...
    """
    model_name = parent_model.get_path_name().stem
    results: List[Tuple[pathlib.Path, IBody2, int]] = []
    unique_bodies_sets = utils.get_unique_bodies(bodies)
    for unique_bodies_set in unique_bodies_sets:
        utils.STATUS.log_line(f"detected {len(unique_bodies_set)} unique bodies {[body.name for body in unique_bodies_set]}")
        quantity = len(unique_bodies_set)
        common_name = ' + '.join(set([utils.validate_and_parse_body_name(body).main_name for body in unique_bodies_set]))
        representative_body = unique_bodies_set[0]
        body_folder_name = utils.detect_folder_for_body(parent_model, representative_body) if '+' not in common_name else None
        if body_folder_name:
            step_file_name = pathlib.Path(f"{model_name} {body_folder_name} {common_name}")
        else:
            step_file_name = pathlib.Path(f"{model_name} {common_name}")
        common_save_path = save_folder / step_file_name
        for (save_path, save_body, _) in results:
            if common_save_path == save_path:
                raise Exception(f"step path '{common_save_path}' for rep-body '{representative_body.name}' is already reserved by body '{save_body.name}'")
        results.append((common_save_path, representative_body, quantity))
    return results


@invoke.task(
    help={
        "path": "path to SW-part-project which bodies should be saved as *.step",
        "save-subfolder": "subfolder in model-folder where step filles should be saved (default is None = in the root folder of the SW-project)",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step_from_part(ctx, path: str = None, save_subfolder: str = None, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    Note: for each solid-body will be created unique file in same directory with the SW-project: <Name of SW-part-project> <Name of solid-body>.step
    """
    check.project_naming(ctx, path)
    check.folders_naming(ctx, path)
    check.bodies_naming(ctx, path)

    root_model = utils.open_document(path, SWDocumentTypesE.SW_DOC_PART).root_model
    assert root_model

    save_folder = root_model.get_path_name().parent
    if save_subfolder:
        save_folder = save_folder / pathlib.Path(save_subfolder)
    component = root_model.configuration_manager.active_configuration.get_root_component3(True)
    bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)
    save_paths_and_bodies = make_common_save_path_for_unique_bodies(root_model, save_folder, bodies)
    for (step_path, body, quantity) in save_paths_and_bodies:
        step_path = step_path.with_name(f"{step_path.stem} [{quantity}]").with_suffix(".step")
        if execute:
            try:
                root_model.clear_selection2(True)
                assert body.select_2(False)
                step_path.parent.mkdir(parents=True, exist_ok=True)
                root_model.extension.save_as_3(name=step_path,
                                               version=SWSaveAsVersionE.SW_SAVE_AS_CURRENT_VERSION,
                                               options=SWSaveAsOptionsE.SW_SAVE_AS_OPTIONS_SILENT,
                                               export_data=None,
                                               advanced_save_as_options=None)
                utils.SUCCESS.log_line(f"step file created: {step_path}")
            except Exception as error:
                utils.ERROR.log_line(f"cannot create step file '{step_path}': {error}")
        else:
            utils.INFO.log_line(f"defined path for unique solid-body: {step_path}")


@invoke.task(
    help={
        "path": "path to SW-assembly-project which bodies should be saved as *.step",
        "save-subfolder": "subfolder in model-folder where step filles should be saved (default is None = in the root folder of the SW-project)",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step_from_assembly(ctx, path: str = None, save_subfolder: str = None, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    Note: for each solid-body will be created unique file in same directory with the SW-project: <Name of SW-part-project> <Name of solid-body>.step
    """
    check.project_naming(ctx, path)

    root_assembly = IAssemblyDoc(utils.open_document(path, SWDocumentTypesE.SW_DOC_ASSEMBLY).root_model.com_object)
    save_folder = root_assembly.get_path_name().parent
    if save_subfolder:
        save_folder = save_folder / pathlib.Path(save_subfolder)

    def enumerate_component_body(component: IComponent2, offset: int = 1):
        component_type = component.get_type()
        if component_type == SWDocumentTypesE.SW_DOC_PART:
            model = component.get_model_doc2()
            assert utils.validate_and_parse_model_name(model)
            bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)
            assert utils.validate_and_parse_bodies_names(bodies)
            # save_paths_and_bodies = make_common_save_path_for_unique_bodies(model, save_folder, bodies)

            # model_path = model.get_path_name()
            # active_configuration_description = model.configuration_manager.active_configuration.description
            # print(f" - model path is '{model_path}' in configuration '{active_configuration_description}'")
            # for (i, body) in enumerate(bodies, 1):
            #     print(f"{'\t' * offset}{i} body name is '{body.name}'")
        elif component_type == SWDocumentTypesE.SW_DOC_ASSEMBLY:
            for sub_component in component.get_children():
                print(f"{'\t' * offset}sub-component name is '{sub_component.name2}'")
                enumerate_component_body(sub_component, offset + 1)
        else:
            raise Exception(f"unexpected type of mode: f{component_type}")

    for component in root_assembly.get_components(True):
        print(f"component name is '{component.name2}'")
        enumerate_component_body(component)


collection = invoke.Collection()
collection.add_task(step_from_part, name="step-from-part")
collection.add_task(step_from_assembly, name="step-from-assembly")
