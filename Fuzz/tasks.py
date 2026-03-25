import invoke

namespace = invoke.Collection()

import export

namespace.add_collection(export.collection, name="export")

import check

namespace.add_collection(check.collection, name="check")
