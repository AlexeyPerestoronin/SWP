import invoke, pathlib

import utils


@invoke.task(
    help={
        "path": "path to SW-part-project which bodies should be saved as *.step",
        "save-subfolder": "subfolder in model-folder where step filles should be saved (default is None = in the root folder of the SW-project)",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step(ctx, path: str = None, save_subfolder: str = None, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    Note: for each solid-body will be created unique file in same directory with the SW-project: <Name of SW-part-project> <Name of solid-body>.step
    """
    from pyswx.api.swconst.enumerations import SWSaveAsOptionsE, SWSaveAsVersionE, SWBodyTypeE

    root_model = utils.open_document(path).root_model
    assert root_model

    sw_utils = utils.ModelUtils()

    def prepare_save_path_for_bodies():
        save_path_and_body = {}
        model_name = root_model.get_path_name().stem
        save_folder = root_model.get_path_name().parent
        if save_subfolder:
            save_folder = save_folder / pathlib.Path(save_subfolder)
        component = root_model.configuration_manager.active_configuration.get_root_component3(True)
        unique_bodies_sets = sw_utils.get_unique_bodies(component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY))
        for unique_bodies_set in unique_bodies_sets:
            utils.STATUS.log_line(f"detected {len(unique_bodies_set)} unique bodies {[body.name for body in unique_bodies_set]}")
            quantity = len(unique_bodies_set)
            common_name = ' + '.join(set([utils.parse_and_check_body_name(body.name)[0] for body in unique_bodies_set]))
            representative_body = unique_bodies_set[0]
            body_folder_name = sw_utils.detect_folder_for_body(root_model, representative_body) if '+' not in common_name else None
            if body_folder_name:
                step_file_name = pathlib.Path(f"{model_name} {body_folder_name} {common_name} [{quantity}]").with_suffix(".step")
            else:
                step_file_name = pathlib.Path(f"{model_name} {common_name} [{quantity}]").with_suffix(".step")
            step_path = save_folder / step_file_name
            if step_path not in save_path_and_body.keys():
                save_path_and_body[step_path] = representative_body
            else:
                raise Exception(f"step path '{step_path}' for rep-body '{representative_body.name}' is already reserved by body '{save_path_and_body[step_path].name}'")
        return save_path_and_body

    save_paths_and_bodies = prepare_save_path_for_bodies()
    for (step_path, body) in save_paths_and_bodies.items():
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


collection = invoke.Collection()
collection.add_task(step, name="step")
