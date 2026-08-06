import sys
import invoke
import pathlib

current_dir = str(pathlib.Path(__file__).resolve().parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

collection = invoke.Collection()

import engineering_wall_ls

collection.add_collection(engineering_wall_ls.collection, name="engineering-wall-ls")
