import invoke

from pyswx import PySWX
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWFileLoadWarningE
from pyswx.api.swconst.enumerations import SWRebuildOnActivationOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsOptionsE
from pyswx.api.swconst.enumerations import SWSaveAsVersionE
from pyswx.api.swconst.enumerations import SWBodyTypeE

SolidWorksPySWX = PySWX(version=2025).application


def com_test(com_object):
    import inspect

    print("COM object type:", type(com_object))
    print("Dir GetBodies2:", [m for m in dir(com_object) if 'GetBodies2' in m])

    # Попробуем разные варианты вызова
    print("\n=== Тест 1: self.com_object.GetBodies2(body_type_int) ===")
    try:
        body_type = int(SWBodyTypeE.SW_SOLID_BODY)
        result = com_object.GetBodies2(body_type)
        print("Успех! Result:", result)
    except Exception as e:
        print("Ошибка:", e)

    print("\n=== Тест 2: self.com_object.GetBodies2(body_type_int, 1) ===")
    try:
        result = com_object.GetBodies2(body_type, 1)
        print("Успех! Result:", result)
    except Exception as e:
        print("Ошибка:", e)

    print("\n=== Тест 3: self.com_object.GetBodies2(body_type_int, 1, None) ===")
    try:
        result = com_object.GetBodies2(body_type, 1, None)
        print("Успех! Result:", result)
    except Exception as e:
        print("Ошибка:", e)

    print("\n=== Тест 4: dir(root_comp) ===")
    print(dir(com_object))

    print("\n=== Type info GetBodies2 ===")
    if hasattr(com_object, 'GetBodies2'):
        method = com_object.GetBodies2
        print("Method type:", type(method))
        print("Inspect signature:", inspect.signature(method) if hasattr(method, '__signature__') else 'No signature')


@invoke.task(
    help={
        "path": "path to SW-part-project which bodies should be saved as *.step",
        "execute": "if True unique solid-body will be saved in corresponded step-file, otherwise only log (be default: False)",
    })
def step_export(ctx, path: str = None, only_unique: bool = True, execute: bool = False):
    """
    Mass exporting of SW-solid-bodies in unique step-files.
    Note: for each solid-body will be created unique file in same directory with the SW-project: <Name of SW-part-project> <Name of solid-body>.step
    """
    assert SolidWorksPySWX

    part_open_spec = SolidWorksPySWX.get_open_doc_spec(file_name=path)
    part_open_spec.document_type = SWDocumentTypesE.SW_DOC_PART
    part_open_spec.use_light_weight_default = True
    part_open_spec.light_weight = True
    part_open_spec.silent = True

    part_model, warning, error = SolidWorksPySWX.open_doc7(specification=part_open_spec)
    assert not error
    assert not warning or warning == SWFileLoadWarningE.SW_FILELOADWARNING_ALREADY_OPEN
    assert part_model

    part_model, error = SolidWorksPySWX.activate_doc_3(name=part_model.get_path_name(), use_user_preferences=False, option=SWRebuildOnActivationOptionsE.SW_REBUILD_ACTIVE_DOC)
    assert part_model
    assert not error

    root_component = part_model.configuration_manager.active_configuration.get_root_component3(True)
    bodies = root_component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)
    if only_unique:
        unique_bodies = []
        remain_bodies = []
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
        bodies = unique_bodies

    for body in bodies:
        step_path = part_model.get_path_name()
        step_path = step_path.with_name(f"{step_path.stem} {body.name}").with_suffix(".step")
        print(f"step path for unique solid-body = {step_path}")
        if execute:
            part_model.clear_selection2(True)
            assert body.select_2(False)
            part_model.extension.save_as_3(name=step_path,
                                           version=SWSaveAsVersionE.SW_SAVE_AS_CURRENT_VERSION,
                                           options=SWSaveAsOptionsE.SW_SAVE_AS_OPTIONS_SILENT,
                                           export_data=None,
                                           advanced_save_as_options=None)

    SolidWorksPySWX.close_doc(part_model.get_path_name())


namespace = invoke.Collection()
namespace.add_task(step_export, name="step-export")
