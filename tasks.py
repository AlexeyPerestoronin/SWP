import invoke
import pathlib

from pyswx import PySWX
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWFileLoadWarningE
from pyswx.api.swconst.enumerations import SWRebuildOnActivationOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsVersionE

SolidWorks = PySWX(version=2025).application


@invoke.task(help={"path": "path to SW-body which bodies should be saved as *.step"})
def step_export(ctx, path: str = None):
    """
    Mass exporting of SW-solid-bodies in step-files
    """
    path = pathlib.Path(path)
    assert path.exists()

    part_open_spec = SolidWorks.get_open_doc_spec(file_name=path)
    part_open_spec.document_type = SWDocumentTypesE.SW_DOC_PART
    part_open_spec.use_light_weight_default = True
    part_open_spec.light_weight = True
    part_open_spec.silent = True

    part_model, warning, error = SolidWorks.open_doc7(specification=part_open_spec)
    assert not error
    assert not warning or warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN
    assert part_model

    part_model, error = SolidWorks.activate_doc_3(name=part_model.get_path_name(), use_user_preferences=False, option=SWRebuildOnActivationOptionsE.SW_REBUILD_ACTIVE_DOC)
    assert part_model
    assert not error

    step_path = part_model.get_path_name().with_suffix(".step")
    print(f"step_path = {step_path}")
    part_model.extension.save_as_3(name=step_path,
                                   version=SWSaveAsVersionE.SW_SAVE_AS_CURRENT_VERSION,
                                   options=SWSaveAsOptionsE.SW_SAVE_AS_OPTIONS_SILENT,
                                   export_data=None,
                                   advanced_save_as_options=None)

    SolidWorks.close_doc(part_model.get_path_name())


namespace = invoke.Collection()
namespace.add_task(step_export, name="step-export")
