import invoke
import pathlib

from pyswx import PySWX
from pyswx.api.swconst.enumerations import SWDocumentTypesE
from pyswx.api.swconst.enumerations import SWRebuildOnActivationOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsVersionE


@invoke.task(
    help = {
        "path": "path to SW-body which bodies should be saved as *.step"
    }
)
def step_export(ctx, path: str = None):
    """
    Mass exporting of SW-solid-bodies in step-files
    """
    path = pathlib.Path(path)
    assert path.exists()

    swx = PySWX(version=2025).application
    part_open_spec = swx.get_open_doc_spec(file_name=path)
    part_open_spec.document_type = SWDocumentTypesE.SW_DOC_PART
    part_open_spec.use_light_weight_default = True
    part_open_spec.light_weight = True
    part_open_spec.silent = True


namespace = invoke.Collection()
namespace.add_task(step_export, name="step-export")