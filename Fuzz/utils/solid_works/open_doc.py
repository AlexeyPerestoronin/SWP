import pathlib

from pyswx import PySWX
from pyswx.api.sldworks.interfaces import ISldWorks, IModelDoc2
from pyswx.api.swconst.enumerations import SWFileLoadWarningE

from ..logger import STATUS

class OpenDocument:
    """
    Context manager-like class for opening/connecting to SolidWorks document (SLDPRT/SLDASM).

    Supports PySWX 2025, opens silently in lightweight mode.
    Auto-closes if newly opened.
    Provides sw (ISldWorks) and root_model (IModelDoc2) properties.
    Logs open/connect and close/disconnect actions.
    """
    def __init__(self, path: pathlib.Path):
        self.__path = path
        assert self.__path

        if not hasattr(OpenDocument, 'sw2025'):
            setattr(OpenDocument, 'sw2025', PySWX(version=2025).application)
        self.__sw2025 = getattr(OpenDocument, 'sw2025')
        assert self.__sw2025

        open_spec: ISldWorks = self.__sw2025.get_open_doc_spec(file_name=self.__path)
        open_spec.use_light_weight_default = True
        open_spec.light_weight = True
        open_spec.silent = True
        self.__root_model, warning, error = self.__sw2025.open_doc7(specification=open_spec)
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


def open_document(path: pathlib.Path) -> OpenDocument:
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
        open_models[model_key] = OpenDocument(path)
    return open_models[model_key]
