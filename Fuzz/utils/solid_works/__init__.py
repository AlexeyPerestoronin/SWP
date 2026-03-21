from typing import List
from typing import Tuple

from pyswx.api.sldworks.interfaces import IModelDoc2
from pyswx.api.sldworks.interfaces import IComponent2
from pyswx.api.sldworks.interfaces import IBody2
from pyswx.api.sldworks.interfaces.i_body_folder import IBodyFolder

import utils


def get_unique_bodies(bodies: List[IBody2], show_log: bool = True) -> List[Tuple[str, int, IBody2]]:
    """
    Groups a list of SolidWorks solid bodies (IBody2) into unique sets based on geometric coincidence.

    Args:
        bodies (List[IBody2]): list of SW bodies for selection of unique
        show_log (bool): if True - the working log will be printed in the consol

    Returns:
        List[Tuple[str, int, IBody2]]: List of tuples (common_name, quantity, representative_body) for each unique group.
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

    def prepare_result(same_bodies: List[IBody2]):
        names = [body.name for body in same_bodies]
        common_name = utils.longest_common_substring(names).strip()
        if show_log:
            utils.INFO.log_line(f"next {len(names)} bodies {names} are same and their common name is '{common_name}'")
        return (common_name, len(same_bodies), same_bodies[0])

    return [prepare_result(same_bodies) for same_bodies in unique_bodies]


def detect_folder_for_body(model: IModelDoc2, body: IBody2) -> str:
    feature = model.first_feature
    while feature:
        folder = None
        if feature.type_name == 'SolidBodyFolder':
            for folder_in_body in IBodyFolder(feature.get_specific_feature_2()).get_bodies():
                if folder_in_body.name == body.name:
                    return None
        if feature.type_name == 'SubAtomFolder':
            for folder_in_body in IBodyFolder(feature.get_specific_feature_2()).get_bodies():
                if folder_in_body.name == body.name:
                    return feature.name
        feature = feature.get_next_feature()
    raise Exception(f"cannot detect folder for the body {body.name}")