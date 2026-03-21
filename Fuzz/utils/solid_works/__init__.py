from typing import List
from typing import Tuple
from typing import Dict

from pyswx.api.sldworks.interfaces import IModelDoc2
from pyswx.api.sldworks.interfaces import IComponent2
from pyswx.api.sldworks.interfaces import IBody2
from pyswx.api.sldworks.interfaces import IBodyFolder

from pyswx.api.swconst.enumerations import SWBodyFolderFeatureTypE

import utils


class SWUtils:

    def __init__(self):
        self.model_folders_cache: Dict[str, List[IBodyFolder]] = {}

    def get_unique_bodies(self, bodies: List[IBody2], show_log: bool = True) -> List[Tuple[str, int, IBody2]]:
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

    def get_body_folders(self, model: IModelDoc2, use_cache: bool = True):
        """
        TODO: need provide verbose comment
        """
        cache_key = model.get_path_name()
        cached_sw_folders = self.model_folders_cache.get(cache_key, None)
        if not cached_sw_folders or use_cache == False:
            cached_sw_folders = []
            feature = model.first_feature
            while feature:
                if feature.type_name in ['SolidBodyFolder', 'SubAtomFolder']:
                    cached_sw_folders.append(IBodyFolder(feature.get_specific_feature_2()))
                feature = feature.get_next_feature()
            self.model_folders_cache[cache_key] = cached_sw_folders
        return cached_sw_folders

    def detect_folder_for_body(self, model: IModelDoc2, body: IBody2, use_cache: bool = True) -> str:
        """
        TODO: need provide verbose comment
        """
        for folder in self.get_body_folders(model, use_cache):
            for body_in_folder in folder.get_bodies():
                if body_in_folder.name == body.name:
                    if folder.type == SWBodyFolderFeatureTypE.SW_SOLID_BODY_FOLDER:
                        return None
                    if folder.type == SWBodyFolderFeatureTypE.SW_BODY_SUB_FOLDER:
                        return folder.get_feature().name

        raise Exception(f"cannot detect folder for the body {body.name}")
