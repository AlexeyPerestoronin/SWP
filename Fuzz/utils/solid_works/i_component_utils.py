import re
from typing import TypeAlias, List, Optional
from pyswx.api.sldworks.interfaces import IComponent2, IBodyFolder, IBody2
from pyswx.api.swconst.enumerations import SWBodyFolderFeatureTypE

from .i_model_doc_utils import ValidModelName, validate_and_parse_model_name
from . import i_feature_utils

__all__ = [
    'ValidComponentName',
    'validate_and_parse_component_name',
    'get_solid_body_folders_in_component',
    'detect_folder_for_body_in_component',
]


class ValidComponentName:
    AssemblyName: TypeAlias = str
    AssemblyNumbers: TypeAlias = List[int]

    def __init__(self, valid_model_name: ValidModelName, assembly_number: AssemblyNumbers):
        self.__valid_model_name = valid_model_name
        self.__assembly_number = assembly_number

    @property
    def valid_model_name(self) -> ValidModelName:
        return self.__valid_model_name

    @property
    def assembly_number(self) -> AssemblyNumbers:
        return self.__assembly_number


def validate_and_parse_component_name(component: IComponent2) -> ValidComponentName:
    """
    Validate and parse name of the SW-IComponent2.
    """

    try:
        # 'Стол-Письменный-Швейный-Каркас-34'
        component_name = component.name2
        valid_model_name = validate_and_parse_model_name(component.get_model_doc2())
        try:
            assembly_number_extraction = component_name.replace(valid_model_name.model_name, '')
            if valid_model_name.assembly_name:
                assembly_number_extraction = assembly_number_extraction.replace(valid_model_name.assembly_name, '')
            assembly_number_extraction = assembly_number_extraction.replace('-', '', -1)
            assembly_number_extraction = assembly_number_extraction.replace('^', '', -1)
            assembly_numbers = [int(string_number) for string_number in re.findall(r'\d+', assembly_number_extraction)]
        except:
            raise Exception(f"impossible extract assembly number from component '{component_name}'")
        return ValidComponentName(valid_model_name, assembly_numbers)
    except Exception as error:
        raise Exception(f"body name '{component_name}' has unsatisfied condition -> {error}")


def get_solid_body_folders_in_component(component: IComponent2, use_cache: bool = True) -> List[IBodyFolder]:
    """
    Get all folders with solid bodies in the component.
    """
    if not hasattr(get_solid_body_folders_in_component, 'component_folders_cache'):
        setattr(get_solid_body_folders_in_component, 'component_folders_cache', {})
    component_folders_cache = getattr(get_solid_body_folders_in_component, 'component_folders_cache')
    cache_key = component.name2
    cached_folders = component_folders_cache.get(cache_key, None)
    if not cached_folders or use_cache == False:
        cached_folders = i_feature_utils.select_solid_body_folders_in_feature_list(component.first_feature)
    return cached_folders


def detect_folder_for_body_in_component(component: IComponent2, body: IBody2, use_cache: bool = True) -> Optional[str]:
    """
    Detect the containing body folder for a given body in the component.
    """
    folders = get_solid_body_folders_in_component(component, use_cache)
    for folder in folders:
        for body_in_folder in folder.get_bodies():
            if body_in_folder.name == body.name:
                folder_type = folder.type
                folder_name = folder.get_feature().name
                if folder_type == SWBodyFolderFeatureTypE.SW_SOLID_BODY_FOLDER:
                    return None
                elif folder_type == SWBodyFolderFeatureTypE.SW_BODY_SUB_FOLDER:
                    return folder_name
                else:
                    raise Exception(f"body '{body.name}' is found in unexpected folder: folder's type is {folder_type}, name is '{folder_name}'")
    raise Exception(
        f"cannot detect folder for the body '{body.name}' in the component '{component.name2}': list of component's folders is {[folder.get_feature().name for folder in folders]}")
