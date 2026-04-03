import invoke
from pyswx.api.swconst.enumerations import SWDocumentTypesE, SWBodyTypeE

import utils


@invoke.task(help={
    "path": "path to SW-project models in which should be checked",
})
def project_naming(ctx, path: str = None):
    """
    Check project name via its filename for a SW project.
    """
    assert utils.validate_project_naming(utils.open_document(path).root_model)
    utils.SUCCESS.log_line("model name is right")


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def bodies_naming(ctx, path: str = None):
    """
    Validate names of all solid bodies in a SW project.
    """

    root_model = utils.open_document(path).root_model
    component = root_model.configuration_manager.active_configuration.get_root_component3(True)
    assert utils.validate_bodies_naming(component.get_bodies2(SWBodyTypeE.SW_SOLID_BODY))
    utils.SUCCESS.log_line("all bodies' names is right!")


@invoke.task(help={
    "path": "path to SW-project bodies in which should be checked",
})
def folders_naming(ctx, path: str = None):
    """
    Check body folder names in a SW project.
    """

    root_model = utils.open_document(path, SWDocumentTypesE.SW_DOC_PART).root_model
    assert utils.validate_folders_naming(utils.get_folders_in_model(root_model))
    utils.SUCCESS.log_line("all folders' names is right!")


@invoke.task(help={
    "path": "path to SW-project which should be complexity checked",
})
def all(ctx, path: str = None):
    """
    Run all naming checks for a SW project
    """
    project_naming(ctx, path)
    bodies_naming(ctx, path)
    folders_naming(ctx, path)


collection = invoke.Collection()
collection.add_task(project_naming, name="project-naming")
collection.add_task(bodies_naming, name="body-naming")
collection.add_task(folders_naming, name="folder-naming")
collection.add_task(all, name="all")
