# import re
# from typing import List, Tuple
# from pyswx.api.sldworks.interfaces import IModelDoc2, IBody2, IBodyFolder
# from pyswx.api.swconst.enumerations import SWBodyFolderFeatureTypE

from . import i_body_folder_utils

__all__ = [
    'ValidModelName',
    'validate_and_parse_model_name',
    'get_folders_in_model',
    'detect_folder_for_body',
]

class ValidModelName:
    type ModelName = str
    type AssemblyName = Tuple[str, None]

    def __init__(self, model_name: ModelName, assembly_name: AssemblyName):
        self.__model_name = model_name
        self.__assembly_name = assembly_name
    
    @property
    def model_name(self) -> ModelName:
        return self.__model_name
    
    @property
    def assembly_name(self) -> AssemblyName:
        return self.__assembly_name

def validate_and_parse_model_name(model: IModelDoc2) -> ValidModelName:
    """
    Check model name.
    """

    model_name = model.get_path_name().stem
    model_name_pattern = r'(?P<model_name>[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w+)*)(\^(?P<assembly_name>[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w+)*))?'
    match = re.fullmatch(model_name_pattern, model_name)
    if match:
        groups = match.groupdict()
        return ValidModelName(groups['model_name'], groups.get('assembly_name', None))
    raise Exception(f"model name '{model_name}' does not match by regular expression: {model_name_pattern}")


def get_folders_in_model(model: IModelDoc2, use_cache: bool = True) -> List[IBodyFolder]:
    """
    Get all body folders in the model (SolidBodyFolder and SubAtomFolder).

    Args:
        model: IModelDoc2 instance
        use_cache: whether to use or refresh cache (default True)

    Returns:
        List of IBodyFolder.

    Cached by model path.
    """
    if not hasattr(get_folders_in_model, 'model_folders_cache'):
        setattr(get_folders_in_model, 'model_folders_cache', {})
    model_folders_cache = getattr(get_folders_in_model, 'model_folders_cache')
    cache_key = model.get_path_name()
    cached_folders = model_folders_cache.get(cache_key, None)
    if not cached_folders or use_cache == False:
        cached_folders = []
        feature = model.first_feature
        while feature:
            if feature.type_name in ['SolidBodyFolder', 'SubAtomFolder']:
                cached_folders.append(IBodyFolder(feature.get_specific_feature_2()))
            feature = feature.get_next_feature()
        model_folders_cache[cache_key] = cached_folders
    return cached_folders


def detect_folder_for_body(model: IModelDoc2, body: IBody2, use_cache: bool = True) -> str:
    """
    Detect the containing body folder for a given body.

    Args:
        model: The model containing the body
        body: IBody2 instance
        use_cache: Use cached folders/bodies (default True)

    Returns:
        str: Folder name if subfolder, None if solid body folder.

    Raises:
        Exception: Body not found in any folder.
    """
    for folder in get_folders_in_model(model, use_cache):
        for body_in_folder in i_body_folder_utils.get_bodies_in_folder(folder, use_cache):
            if body_in_folder.name == body.name:
                if folder.type == SWBodyFolderFeatureTypE.SW_SOLID_BODY_FOLDER:
                    return None
                if folder.type == SWBodyFolderFeatureTypE.SW_BODY_SUB_FOLDER:
                    return folder.get_feature().name
    raise Exception(f"cannot detect folder for the body {body.name}")
