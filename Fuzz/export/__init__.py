import invoke

from pyswx import PySWX
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWFileLoadWarningE
from pyswx.api.swconst.enumerations import SWRebuildOnActivationOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsVersionE
from pyswx.api.swconst.enumerations import SWBodyTypeE

import utils.solid_works


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
    sw = PySWX(version=2025).application
    assert sw

    part_open_spec = sw.get_open_doc_spec(file_name=path)
    part_open_spec.document_type = SWDocumentTypesE.SW_DOC_PART
    part_open_spec.use_light_weight_default = True
    part_open_spec.light_weight = True
    part_open_spec.silent = True

    model, warning, error = sw.open_doc7(specification=part_open_spec)
    assert not error
    assert model

    model, error = sw.activate_doc_3(name=model.get_path_name(), use_user_preferences=False, option=SWRebuildOnActivationOptionsE.SW_REBUILD_ACTIVE_DOC)
    assert model
    assert not error

    sw_utils = utils.solid_works.SWUtils()

    component = model.configuration_manager.active_configuration.get_root_component3(True)
    unique_bodies = sw_utils.get_unique_bodies(component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY))

    for (name, quantity, body) in unique_bodies:
        model_path = model.get_path_name()
        body_folder_name = sw_utils.detect_folder_for_body(model, body)
        if body_folder_name:
            model_path = model_path.with_name(f"{model_path.stem} {body_folder_name} {name} [{quantity}]").with_suffix(".step")
        else:
            model_path = model_path.with_name(f"{model_path.stem} {name} [{quantity}]").with_suffix(".step")

        if execute:
            try:
                model.clear_selection2(True)
                assert body.select_2(False)
                model.extension.save_as_3(name=model_path,
                                          version=SWSaveAsVersionE.SW_SAVE_AS_CURRENT_VERSION,
                                          options=SWSaveAsOptionsE.SW_SAVE_AS_OPTIONS_SILENT,
                                          export_data=None,
                                          advanced_save_as_options=None)
                utils.SUCCESS.log_line(f"step file created: {model_path}")
            except error:
                utils.ERROR.log_line(f"cannot create step file '{model_path}': {error}")
        else:
            utils.INFO.log_line(f"defined path for unique solid-body: {model_path}")

    if not (warning or warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN):
        sw.close_doc(model.get_path_name())


collection = invoke.Collection()
collection.add_task(step, name="step")
