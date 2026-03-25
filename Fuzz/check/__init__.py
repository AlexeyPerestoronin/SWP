import invoke, re

from pyswx.api.swconst.enumerations import SWBodyTypeE

import utils


@invoke.task(help={
    "path": "path to SW-project models in which should be checked",
})
def project_naming(ctx, path: str = None):
    """
    Check project name via its filename for a SW project.
    """

    root_model = utils.open_document(path).root_model

    model_name = root_model.get_path_name().stem
    model_name_pattern = r'[A-ZА-ЯЁ]\w+(-[A-ZА-ЯЁ]\w)*'
    if not bool(re.match(model_name_pattern, model_name)):
        raise Exception(f"model name '{model_name}' does not match by regular expression: {model_name_pattern}")

    utils.SUCCESS.log_line("model name is right")


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def body_naming(ctx, path: str = None):
    """
    Validate names of all solid bodies in a SW project.
    """

    root_model = utils.open_document(path).root_model
    component = root_model.configuration_manager.active_configuration.get_root_component3(True)
    bodies = component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY)

    for body in bodies:
        body_name = body.name
        assert utils.parse_and_check_body_name(body_name)

    utils.SUCCESS.log_line("all bodies' names is right!")


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def folder_naming(ctx, path: str = None):
    """
    Check body folder names in a SW project.
    """

    utils.open_document(path)
    folder_name_pattern = r'\w+(-\w+)*'
    for folder in utils.ModelUtils().get_folders_in_model(utils.open_document(path).root_model):
        folder_name = folder.get_feature().name
        if not bool(re.match(folder_name_pattern, folder_name)):
            raise Exception(f"folder name '{folder_name}' does not match by regular expression: {folder_name_pattern}")

    utils.SUCCESS.log_line("all folders' names is right!")


@invoke.task(help={
    "path": "path to SW-project which should be complexity checked",
})
def all(ctx, path: str = None):
    """
    Run all naming checks for a SW project
    """

    project_naming(ctx, path)
    body_naming(ctx, path)
    folder_naming(ctx, path)


collection = invoke.Collection()
collection.add_task(project_naming, name="project-naming")
collection.add_task(body_naming, name="body-naming")
collection.add_task(folder_naming, name="folder-naming")
collection.add_task(all, name="all")
