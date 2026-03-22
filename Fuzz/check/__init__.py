import invoke

from utils import ERROR, SUCCESS


@invoke.task(help={
    "path": "path to SW-project which should be checked",
})
def model_name(ctx, path: str = None):
    """
    TODO: need to provide some comment...
    """
    from pyswx import PySWX
    from pyswx.api.swconst.enumerations import SWFileLoadWarningE

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

    if model_name.startswith('-') or model_name.endswith('-'):
        raise ERROR.log_line(f"model name '{model_name}' could not have '-' in begging or end")

    for part in model_name.split('-'):
        if not part.istitle():
            raise ERROR.log_line(f"model name '{model_name}' has part '{part}' without title rune")

    SUCCESS.log_line(f"model name '{model_name}' is right")

    if not (warning or warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN):
        sw.close_doc(model.get_path_name())


collection = invoke.Collection()
collection.add_task(model_name, name="model-name")
