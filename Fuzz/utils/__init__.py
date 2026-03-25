import re, difflib, functools

from typing import List, Tuple, Optional

from .logger import SUCCESS, STATUS, INFO, WARNING, ERROR
from .solid_works import ModelUtils, OpenDocument, open_document


def parse_and_check_body_name(body_name: str) -> Tuple[str, Optional[List[str]]]:
    """
    TODO: need provide some comment...
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
    'OpenDocument',
    'open_document',
    # local utils functions
    'parse_and_check_body_name',
    'longest_common_substring',
]
