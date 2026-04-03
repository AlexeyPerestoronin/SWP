import re, difflib, functools
from typing import List, Tuple, Optional
from pyswx.api.sldworks.interfaces import IModelDoc2, IBody2, IBodyFolder

from .logger import *
from .solid_works import *

__all__ = [
    # local utils functions
    'validate_project_naming',
    'validate_folders_naming',
    'longest_common_substring',
    # sub modules
    *solid_works.__all__,
    *logger.__all__,
]


def validate_project_naming(model: IModelDoc2):
    """
    Check project name via its model
    """

    model_name = model.get_path_name().stem
    model_name_pattern = r'[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w+)*'
    if not bool(re.fullmatch(model_name_pattern, model_name)):
        raise Exception(f"model name '{model_name}' does not match by regular expression: {model_name_pattern}")
    return True


def validate_folders_naming(folders: List[IBodyFolder]):
    """
    Check names of all folders in list.
    """

    folder_name_pattern = r'\w+(-\w+)*'
    for folder in folders:
        folder_name = folder.get_feature().name
        if not bool(re.match(folder_name_pattern, folder_name)):
            raise Exception(f"folder name '{folder_name}' does not match by regular expression: {folder_name_pattern}")
    return True


def longest_common_substring(strings: List[str]) -> str:
    """
    Returns longest common substring for all strings in the list using difflib.
    """
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]

    def lcs_pair(a: str, b: str) -> str:
        matcher = difflib.SequenceMatcher(None, a, b)
        match = matcher.find_longest_match(0, len(a), 0, len(b))
        return a[match.a:match.a + match.size]

    return functools.reduce(lcs_pair, strings)
