import sys
import invoke
import pathlib

current_dir = str(pathlib.Path(__file__).resolve().parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

collection = invoke.Collection()

import extension_rack

collection.add_collection(extension_rack.collection, name="extension-rack")

import bracket_for_vdm

collection.add_collection(bracket_for_vdm.collection, name="bracket-for-vdm")
