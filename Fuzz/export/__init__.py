import invoke, pathlib
from typing import List, Tuple, Set, TypeAlias
from pyswx.api.sldworks.interfaces import IAssemblyDoc, IModelDoc2, IComponent2, IBody2, IBodyFolder
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWSaveAsOptionsE, SWSaveAsVersionE, SWBodyTypeE

import utils
import check


class UniqueBodiesManager:
    SameBodies: TypeAlias = List[Tuple[IBody2, IComponent2]]
    UniqueBodies: TypeAlias = List[SameBodies]

    def __init__(self):
        self.__unique_bodies: UniqueBodiesManager.UniqueBodies = []

    def add_from_assembly(self, assembly: IAssemblyDoc):
        components = assembly.get_components(True)
        while len(components) > 0:
            component = components.pop(0)
            print(f"component name is '{component.name2}'")
            component_type = component.get_type()
            if component_type == SWDocumentTypesE.SW_DOC_PART:
                self.add_from_component(component)
            elif component_type == SWDocumentTypesE.SW_DOC_ASSEMBLY:
                for sub_component in component.get_children():
                    components.append(sub_component)
            else:
                raise Exception(f"unexpected type of mode: f{component_type}")

    def add_from_model(self, model: IModelDoc2):
        component = model.configuration_manager.active_configuration.get_root_component3(True)
        self.add_from_component(component)

    def add_from_component(self, component: IComponent2):
        bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)
        equal_bodies_groups = utils.get_equal_bodies_groups(bodies)
        for equal_bodies_group in equal_bodies_groups:
            same_bodies_from_equal_group: UniqueBodiesManager.SameBodies = [(body, component) for body in equal_bodies_group]
            equal_group_reference_body = equal_bodies_group[0]
            added = False
            for same_bodies in self.__unique_bodies:
                reference_body_in_same_group = same_bodies[0][0]
                if utils.is_two_body_equal(reference_body_in_same_group, equal_group_reference_body):
                    same_bodies.extend(same_bodies_from_equal_group)
                    added = True
                    break
            if not added:
                self.__unique_bodies.append(same_bodies_from_equal_group)

    @property
    def unique_bodies(self) -> UniqueBodies:
        return self.__unique_bodies

def make_common_save_path_for_unique_bodies(parent_model: IModelDoc2, save_folder: pathlib.Path, bodies: List[IBody2], use_cache: bool) -> List[Tuple[pathlib.Path, IBody2, int]]:
    """
    TODO: need to provide some comment...
    """
    model_name = parent_model.get_path_name().stem
    results: List[Tuple[pathlib.Path, IBody2, int]] = []
    unique_bodies_sets = utils.get_equal_bodies_groups(bodies)
    for unique_bodies_set in unique_bodies_sets:
        utils.STATUS.log_line(f"detected {len(unique_bodies_set)} unique bodies {[body.name for body in unique_bodies_set]}")
        quantity = len(unique_bodies_set)
        common_name = ' + '.join(set([utils.validate_and_parse_body_name(body).main_name for body in unique_bodies_set]))
        representative_body = unique_bodies_set[0]
        body_folder_name = utils.detect_folder_for_body_in_model(parent_model, representative_body, use_cache) if '+' not in common_name else None
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
    save_paths_and_bodies = make_common_save_path_for_unique_bodies(root_model, save_folder, bodies, True)
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

    unique_bodies_manager = UniqueBodiesManager()
    unique_bodies_manager.add_from_assembly(root_assembly)

    save_folder = root_assembly.get_path_name().parent
    if save_subfolder:
        save_folder = save_folder / pathlib.Path(save_subfolder)

    save_paths_and_bodies: List[Tuple[IBody2, pathlib.Path]] = []
    for same_bodies in unique_bodies_manager.unique_bodies:
        new_representative_body = same_bodies[0][0]
        bodies_names_set: Set[str] = set()
        models_names_set: Set[str] = set()
        assembly_names_set: Set[str] = set()
        utils.STATUS.log_line("Detected next same bodies:")
        for same_body in same_bodies:
            (body, component) = same_body
            utils.STATUS.log_line(f"* body '{body.name}' in component '{component.name2}'")
            bodies_names_set.add(utils.validate_and_parse_body_name(body).main_name)
            valid_model_name = utils.validate_and_parse_component_name(component).valid_model_name
            models_names_set.add(valid_model_name.model_name)
            if valid_model_name.assembly_name:
                assembly_names_set.add(valid_model_name.assembly_name)
        assembly_name = '+'.join(assembly_names_set)
        model_name = '+'.join(models_names_set)
        body_name = '+'.join(bodies_names_set)
        quantity = len(same_bodies)
        new_save_path = pathlib.Path(save_folder).with_name(f"{assembly_name} {model_name} {body_name} [{quantity}]").with_suffix(".step")
        for (save_path, representative_body) in save_paths_and_bodies:
            if new_save_path == save_path:
                raise Exception(f"step path '{new_save_path}' for rep-body '{new_representative_body.name}' is already reserved by body '{representative_body.name}'")
        utils.STATUS.log_line(f"+ they common save path is '{new_save_path}'")
        save_paths_and_bodies.append((new_representative_body, new_save_path))



collection = invoke.Collection()
collection.add_task(step_from_part, name="step-from-part")
collection.add_task(step_from_assembly, name="step-from-assembly")
