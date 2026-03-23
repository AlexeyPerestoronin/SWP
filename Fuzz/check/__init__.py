import invoke, re

from pyswx import PySWX
from pyswx.api.swconst.enumerations import SWBodyTypeE
from pyswx.api.swconst.enumerations import SWFileLoadWarningE
from pyswx.api.swconst.enumerations import SWRebuildOnActivationOptionsE

from utils import *


@invoke.task(help={
    "path": "path to SW-project models in which should be checked",
})
def model_naming(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    sw = PySWX(version=2025).application
    assert sw

    part_open_spec = sw.get_open_doc_spec(file_name=path)
    part_open_spec.use_light_weight_default = True
    part_open_spec.light_weight = True
    part_open_spec.silent = True

    model, warning, error = sw.open_doc7(specification=part_open_spec)
    assert not error
    assert model

    model_name = model.get_path_name().stem

    model_name_pattern = r'[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w)*'
    if not bool(re.match(model_name_pattern, model_name)):
        raise Exception(f"model name '{model_name}' does not match regular expression: {model_name_pattern}")

    SUCCESS.log_line("model name is right")

    if not (warning or warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN):
        sw.close_doc(model.get_path_name())


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def body_naming(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    sw = PySWX(version=2025).application
    assert sw

    part_open_spec = sw.get_open_doc_spec(file_name=path)
    part_open_spec.use_light_weight_default = True
    part_open_spec.light_weight = True
    part_open_spec.silent = True

    model, warning, error = sw.open_doc7(specification=part_open_spec)
    assert not error
    assert model

    model, error = sw.activate_doc_3(name=model.get_path_name(), use_user_preferences=False, option=SWRebuildOnActivationOptionsE.SW_REBUILD_ACTIVE_DOC)
    assert model
    assert not error

    component = model.configuration_manager.active_configuration.get_root_component3(True)
    bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)

    for body in bodies:
        body_name = body.name
        parse_and_check_body_name(body_name)

    SUCCESS.log_line("all bodies' names is right!")

    if not (warning or warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN):
        sw.close_doc(model.get_path_name())


collection = invoke.Collection()
collection.add_task(model_naming, name="model-naming")
collection.add_task(body_naming, name="body-naming")
