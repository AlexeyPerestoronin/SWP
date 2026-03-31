import re, difflib, functools

from typing import List, Tuple, Optional
from pyswx.api.sldworks.interfaces import IModelDoc2, IBody2, IBodyFolder

from .logger import SUCCESS, STATUS, INFO, WARNING, ERROR
from .solid_works import ModelUtils, connect_to_sw2025, OpenDocument, open_document


def validate_and_parse_body_name(body_name: str) -> Tuple[str, Optional[List[str]]]:
    """
    Parse SolidWorks body name into main name and optional suffixes.

    Main name: word chars, optionally hyphen-separated word parts.
    Suffixes: space-separated R/L/U/D/F/B or numbers.

    Returns:
        Tuple[str, Optional[List[str]]]: (main_name, suffixes)

    Raises:
        Exception: Invalid name or suffixes.
    """

    def check_main_name(main_name: str) -> str:
        main_name_pattern = r'\w+(-\w)*'
        if not bool(re.match(main_name_pattern, main_name)):
            raise Exception(f"main-name does not match by regular expression: {main_name_pattern}")
        return main_name

    def check_name_suffixes(body_suffixes: List[str]) -> str:
        available_suffixes = [r'R', r'L', r'U', r'D', r'F', r'B', r'\d+']
        for body_suffix in body_suffixes:
            if any([bool(re.match(available_suffix, body_suffix)) for available_suffix in available_suffixes]):
                return body_suffix
            raise Exception(f"unexpected body suffix: {body_suffix}")

    try:
        if ' ' in body_name:
            parts = body_name.split(' ')
            return (check_main_name(parts[0]), [suffix for suffix in check_name_suffixes(parts[1:])])
        else:
            return (check_main_name(body_name), None)
    except Exception as error:
        raise Exception(f"body name '{body_name}' has unsatisfied condition -> {error}")


def validate_project_naming(model: IModelDoc2):
    """
    Check project name via its model
    """

    model_name = model.get_path_name().stem
    model_name_pattern = r'[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w)*'
    if not bool(re.match(model_name_pattern, model_name)):
        raise Exception(f"model name '{model_name}' does not match by regular expression: {model_name_pattern}")
    return True


def validate_bodies_naming(bodies: List[IBody2]):
    """
    Validate names of all bodies in list.
    """
    for body in bodies:
        body_name = body.name
        assert validate_and_parse_body_name(body_name)
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


__all__ = [
    # .logger
    'SUCCESS',
    'STATUS',
    'INFO',
    'WARNING',
    'ERROR',
    # .solid_works
    'ModelUtils',
    'connect_to_sw2025',
    'OpenDocument',
    'open_document',
    # local utils functions
    'validate_and_parse_body_name',
    'validate_project_naming',
    'validate_bodies_naming',
    'validate_folders_naming',
    'longest_common_substring',
]
