from typing import List
from pyswx.api.sldworks.interfaces import IFeature, IBodyFolder

__all__ = [
    'select_solid_body_folders_in_feature_list',
]


def select_solid_body_folders_in_feature_list(first_feature: IFeature) -> List[IBodyFolder]:
    """
    Get all body folders in the model (SolidBodyFolder and SubAtomFolder).
    """
    result = []
    feature = first_feature
    while feature:
        if feature.type_name in ['SolidBodyFolder', 'SubAtomFolder']:
            result.append(IBodyFolder(feature.get_specific_feature_2()))
        feature = feature.get_next_feature()
    return result
