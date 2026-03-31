from typing import List
from pyswx.api.sldworks.interfaces import IBody2


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


__all__ = [
    'get_unique_bodies',
]
