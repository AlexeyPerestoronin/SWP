import re
from typing import TypeAlias, List, Optional
from pyswx.api.sldworks.interfaces import IModelDoc2, IBody2, IBodyFolder
from pyswx.api.swconst.enumerations import SWBodyFolderFeatureTypE

from . import i_body_folder_utils
from . import i_feature_utils

__all__ = [
    'ValidModelName',
    'validate_and_parse_model_name',
    'get_solid_body_folders_in_model',
    'detect_folder_for_body_in_model',
]


class ValidModelName:
    ModelName: TypeAlias = str
    AssemblyNameOpt: TypeAlias = Optional[str]

    def __init__(self, model_name: ModelName, assembly_name: AssemblyNameOpt):
        self.__model_name = model_name
        self.__assembly_name = assembly_name

    @property
    def model_name(self) -> ModelName:
        return self.__model_name

    @property
    def assembly_name(self) -> AssemblyNameOpt:
        return self.__assembly_name


def validate_and_parse_model_name(model: IModelDoc2) -> ValidModelName:
    """
    Validate and parse name of the SW-IModelDoc2.
    """

    model_name = model.get_path_name().stem
    model_name_pattern = r'(?P<model_name>[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w+)*)(\^(?P<assembly_name>[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w+)*))?'
    match = re.fullmatch(model_name_pattern, model_name)
    if match:
        groups = match.groupdict()
        return ValidModelName(groups['model_name'], groups.get('assembly_name', None))
    raise Exception(f"model name '{model_name}' does not match by regular expression: {model_name_pattern}")


def get_solid_body_folders_in_model(model: IModelDoc2, use_cache: bool = True) -> List[IBodyFolder]:
    """
    Get all folders with solid bodies in the model.
    """
    if not hasattr(get_solid_body_folders_in_model, 'model_folders_cache'):
        setattr(get_solid_body_folders_in_model, 'model_folders_cache', {})
    model_folders_cache = getattr(get_solid_body_folders_in_model, 'model_folders_cache')
    cache_key = model.get_path_name()
    cached_folders = model_folders_cache.get(cache_key, None)
    if not cached_folders or use_cache == False:
        cached_folders = i_feature_utils.select_solid_body_folders_in_feature_list(model.first_feature)
    return cached_folders


def detect_folder_for_body_in_model(model: IModelDoc2, body: IBody2, use_cache: bool = True) -> str:
    """
    Detect the containing body folder for a given body in the model.
    """
    folders = get_solid_body_folders_in_model(model, use_cache)
    for folder in folders:
        for body_in_folder in i_body_folder_utils.get_bodies_in_folder(folder, use_cache):
            if body_in_folder.name == body.name:
                folder_type = folder.type
                folder_name = folder.get_feature().name
                if folder_type == SWBodyFolderFeatureTypE.SW_SOLID_BODY_FOLDER:
                    return None
                elif folder_type == SWBodyFolderFeatureTypE.SW_BODY_SUB_FOLDER:
                    return folder_name
                else:
                    raise Exception(f"body '{body.name}' is found in unexpected folder: folder's type is {folder_type}, name is '{folder_name}'")
    raise Exception(f"cannot detect folder for the body '{body.name}': list of model's folders is {[folder.get_feature().name for folder in folders]}")
