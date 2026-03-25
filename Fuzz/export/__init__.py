import invoke

import utils


@invoke.task(
    help={
        "path": "path to SW-part-project which bodies should be saved as *.step",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step(ctx, path: str = None, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    Note: for each solid-body will be created unique file in same directory with the SW-project: <Name of SW-part-project> <Name of solid-body>.step
    """
    from pyswx.api.swconst.enumerations import SWSaveAsOptionsE
    from pyswx.api.swconst.enumerations import SWSaveAsVersionE
    from pyswx.api.swconst.enumerations import SWBodyTypeE

    root_model = utils.open_document(path).root_model
    assert root_model

    sw_utils = utils.ModelUtils()

    component = root_model.configuration_manager.active_configuration.get_root_component3(True)
    unique_bodies = sw_utils.get_unique_bodies(component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY))

    step_paths = []
    for (name, quantity, body) in unique_bodies:
        model_path = root_model.get_path_name()
        body_folder_name = sw_utils.detect_folder_for_body(root_model, body)
        if body_folder_name:
            step_path = model_path.with_name(f"{model_path.stem} {body_folder_name} {name} [{quantity}]").with_suffix(".step")
        else:
            step_path = model_path.with_name(f"{model_path.stem} {name} [{quantity}]").with_suffix(".step")

        if step_path in step_paths:
            raise utils.ERROR.log_line(f"cannot create step file '{step_path}' because it already reserved!")

        step_paths.append(step_path)

        if execute:
            try:
                root_model.clear_selection2(True)
                assert body.select_2(False)
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
