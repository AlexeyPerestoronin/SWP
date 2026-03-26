import invoke

import utils


@invoke.task(help={
    "unsaved": "close unsaved document too (default: False)",
})
def close_all(ctx, unsaved: bool = False):
    """
    Close all opened SW projects
    """
    utils.connect_to_sw2025().close_all_documents(include_unsaved=unsaved)


namespace = invoke.Collection()
namespace.add_task(close_all, name='close-all')

import export

namespace.add_collection(export.collection, name="export")

import check

namespace.add_collection(check.collection, name="check")
