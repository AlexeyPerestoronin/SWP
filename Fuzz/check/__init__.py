import invoke, re, pathlib
from typing import Tuple

from pyswx import PySWX
from pyswx.api.sldworks.interfaces import ISldWorks, IModelDoc2

from pyswx.api.swconst.enumerations import SWBodyTypeE
from pyswx.api.swconst.enumerations import SWFileLoadWarningE
from pyswx.api.swconst.enumerations import SWRebuildOnActivationOptionsE

from utils import *


class OpenModel:
    """
    TODO: provide some comment...
    """

    def __init__(self, path: pathlib.Path):
        self.__path = path
        assert self.__path

        if not hasattr(OpenModel, 'sw2025'):
            setattr(OpenModel, 'sw2025', PySWX(version=2025).application)
        self.__sw2025 = getattr(OpenModel, 'sw2025')
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


def open_model(path: pathlib.Path) -> OpenModel:
    """
    TODO: provide some comment...
    """
    assert path

    def get_open_models() -> dict:
        cache_atr_name = 'open_models'
        if not hasattr(open_model, cache_atr_name):
            setattr(open_model, cache_atr_name, {})
        return getattr(open_model, cache_atr_name)

    open_models = get_open_models()
    model_key = str(path)
    if model_key not in open_models:
        open_models[model_key] = OpenModel(path)
    return open_models[model_key]


@invoke.task(help={
    "path": "path to SW-project models in which should be checked",
})
def model_naming(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    sw = PySWX(version=2025).application
    assert sw
    root_model = open_model(path).root_model

    model_name = root_model.get_path_name().stem
    model_name_pattern = r'[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w)*'
    if not bool(re.match(model_name_pattern, model_name)):
        raise Exception(f"model name '{model_name}' does not match by regular expression: {model_name_pattern}")

    SUCCESS.log_line("model name is right")


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def body_naming(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    root_model = open_model(path).root_model
    component = root_model.configuration_manager.active_configuration.get_root_component3(True)
    bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)

    for body in bodies:
        body_name = body.name
        assert parse_and_check_body_name(body_name)

    SUCCESS.log_line("all bodies' names is right!")


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def folder_naming(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    open_model(path)
    folder_name_pattern = r'\w+(-\w+)*'
    for folder in SWUtils().get_folders_in_model(open_model(path).root_model):
        folder_name = folder.get_feature().name
        if not bool(re.match(folder_name_pattern, folder_name)):
            raise Exception(f"folder name '{folder_name}' does not match by regular expression: {folder_name_pattern}")

    SUCCESS.log_line("all folders' names is right!")


@invoke.task(help={
    "path": "path to SW-project which should be complexity checked",
})
def all(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    model_naming(ctx, path)
    body_naming(ctx, path)
    folder_naming(ctx, path)


collection = invoke.Collection()
collection.add_task(model_naming, name="model-naming")
collection.add_task(body_naming, name="body-naming")
collection.add_task(folder_naming, name="folder-naming")
collection.add_task(all, name="all")
