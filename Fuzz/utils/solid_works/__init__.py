import pathlib
from typing import Tuple

from pyswx import PySWX
from pyswx.api.sldworks.interfaces import ISldWorks, IModelDoc2, IDocumentSpecification
from pyswx.api.swconst.enumerations import SWFileLoadWarningE, SWDocumentTypesE

from ..logger import STATUS

from .i_model_doc_utils import *
from .i_body_utils import *
from .i_feature_utils import *
from .i_component_utils import *

__all__ = [
    'connect_to_sw2025',
    'open_document',
    # sub modules
    *i_model_doc_utils.__all__,
    *i_body_utils.__all__,
    *i_feature_utils.__all__,
    *i_component_utils.__all__,
]


def connect_to_sw2025() -> ISldWorks:
    if not hasattr(connect_to_sw2025, 'sw2025'):
        setattr(connect_to_sw2025, 'sw2025', PySWX(version=2025).application)
    sw2025 = getattr(connect_to_sw2025, 'sw2025')
    assert sw2025
    return sw2025


class OpenDocument:
    """
    Context manager-like class for opening/connecting to SolidWorks document (SLDPRT/SLDASM).

    Supports PySWX 2025, opens silently in lightweight mode.
    Auto-closes if newly opened.
    Provides sw (ISldWorks) and root_model (IModelDoc2) properties.
    Logs open/connect and close/disconnect actions.
    """

    def __init__(self, path: pathlib.Path, doc_type: Tuple[None, SWDocumentTypesE]):
        self.__path = path
        assert self.__path

        self.__sw2025 = connect_to_sw2025()

        open_specification: IDocumentSpecification = self.__sw2025.get_open_doc_spec(file_name=self.__path)
        if doc_type:
            open_specification.document_type = doc_type
        open_specification.use_light_weight_default = True
        open_specification.light_weight = True
        open_specification.silent = True
        self.__root_model, warning, error = self.__sw2025.open_doc7(specification=open_specification)
        assert not error
        assert self.__root_model

        self.__already_open = bool(warning and warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN)
        STATUS.log_line(f"{'connect to' if self.__already_open else 'open existing'} SW-project {path}")

    def __del__(self):
        if self.__already_open is False:
            self.sw.close_doc(self.__path)
        STATUS.log_line(f"{'disconnect from' if self.__already_open else 'close active'} SW project {self.__path}")

    @property
    def sw(self) -> ISldWorks:
        return self.__sw2025

    @property
    def root_model(self) -> IModelDoc2:
        return self.__root_model


def open_document(path: pathlib.Path, doc_type: Tuple[None, SWDocumentTypesE] = None) -> OpenDocument:
    """
    Cached factory for OpenDocument.

    Uses static cache keyed by path str for singleton behavior.
    """
    assert path

    def get_open_models() -> dict:
        cache_atr_name = 'open_models'
        if not hasattr(open_document, cache_atr_name):
            setattr(open_document, cache_atr_name, {})
        return getattr(open_document, cache_atr_name)

    open_models = get_open_models()
    model_key = str(path)
    if model_key not in open_models:
        open_models[model_key] = OpenDocument(path, doc_type)
    return open_models[model_key]
