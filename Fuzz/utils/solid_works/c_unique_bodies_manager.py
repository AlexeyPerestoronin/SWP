from typing import List, Tuple, Set, TypeAlias
from pyswx.api.sldworks.interfaces import IAssemblyDoc, IModelDoc2, IComponent2, IBody2
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWBodyTypeE

from . import i_body_utils

__all__ = [
    'UniqueBodiesManager',
]


class UniqueBodiesManager:
    """
    TODO: need to provide short comment
    """
    SameBodies: TypeAlias = List[Tuple[IBody2, IComponent2]]
    UniqueBodies: TypeAlias = List[SameBodies]

    def __init__(self):
        self.__unique_bodies: UniqueBodiesManager.UniqueBodies = []

    def add_from_assembly(self, assembly: IAssemblyDoc):
        """
        TODO: need to provide short comment
        """
        components = assembly.get_components(True)
        while len(components) > 0:
            component = components.pop(0)
            print(f"component name is '{component.name2}'")
            component_type = component.get_type()
            if component_type == SWDocumentTypesE.SW_DOC_PART:
                self.add_from_component(component)
            elif component_type == SWDocumentTypesE.SW_DOC_ASSEMBLY:
                for sub_component in component.get_children():
                    components.append(sub_component)
            else:
                raise Exception(f"unexpected type of mode: f{component_type}")

    def add_from_model(self, model: IModelDoc2):
        """
        TODO: need to provide short comment
        """
        component = model.configuration_manager.active_configuration.get_root_component3(False)
        self.add_from_component(component)

    def add_from_component(self, component: IComponent2):
        """
        TODO: need to provide short comment
        """
        bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)
        equal_bodies_groups = i_body_utils.get_equal_bodies_groups(bodies)
        for equal_bodies_group in equal_bodies_groups:
            same_bodies_from_equal_group: UniqueBodiesManager.SameBodies = [(body, component) for body in equal_bodies_group]
            equal_group_reference_body = equal_bodies_group[0]
            added = False
            for same_bodies in self.__unique_bodies:
                reference_body_in_same_group = same_bodies[0][0]
                if i_body_utils.is_two_body_equal(reference_body_in_same_group, equal_group_reference_body):
                    same_bodies.extend(same_bodies_from_equal_group)
                    added = True
                    break
            if not added:
                self.__unique_bodies.append(same_bodies_from_equal_group)

    @property
    def unique_bodies(self) -> UniqueBodies:
        """
        TODO: need to provide short comment
        """
        return self.__unique_bodies
