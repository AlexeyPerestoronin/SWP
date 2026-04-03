import re
from typing import TypeAlias, List, Tuple
from pyswx.api.sldworks.interfaces import IBody2

__all__ = [
    'get_unique_bodies',
    'ValidBodyName',
    'validate_and_parse_body_name',
    'validate_and_parse_bodies_names',
]


def get_unique_bodies(bodies: List[IBody2], show_log: bool = True) -> List[List[IBody2]]:
    """
    Groups a list of SolidWorks solid bodies (IBody2) into unique sets based on geometric coincidence.

    Args:
        bodies (List[IBody2]): list of SW bodies for selection of unique
        show_log (bool): if True - the working log will be printed in the consol

    Returns:
        List[List[IBody2]]: List of lists of same bodies
    """
    unique_bodies = []
    while len(bodies) != 0:
        remain_bodies = []
        body1 = bodies[0]
        unique_bodies.append([body1])
        for body2 in bodies[1:]:
            (result, _) = body1.get_coincidence_transform_2(body2)
            if result:
                unique_bodies[-1].append(body2)
            else:
                remain_bodies.append(body2)
        bodies = remain_bodies
    return unique_bodies


class ValidBodyName:
    MainName: TypeAlias = str
    SuffixesOpt: TypeAlias = Tuple[List[str], None]

    def __init__(self, main_name: MainName, suffixes: SuffixesOpt):
        self.__main_name = main_name
        self.__suffixes = suffixes

    @property
    def main_name(self) -> MainName:
        return self.__main_name

    @property
    def suffixes(self) -> SuffixesOpt:
        return self.__suffixes


def validate_and_parse_body_name(body: IBody2) -> ValidBodyName:
    """
    Validate and parse name of the SW-IBody2.
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
        body_name = body.name
        if ' ' in body_name:
            parts = body_name.split(' ')
            return ValidBodyName(check_main_name(parts[0]), [suffix for suffix in check_name_suffixes(parts[1:])])
        else:
            return ValidBodyName(check_main_name(body_name), None)
    except Exception as error:
        raise Exception(f"body name '{body_name}' has unsatisfied condition -> {error}")


def validate_and_parse_bodies_names(bodies: List[IBody2]) -> List[ValidBodyName]:
    """
    Validate names of all bodies in list.
    """
    return [validate_and_parse_body_name(body) for body in bodies]
