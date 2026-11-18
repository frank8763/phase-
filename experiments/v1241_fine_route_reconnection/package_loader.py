"""Absolute-path private package binding; zero top-level module replacements."""
from pathlib import Path
import hashlib,importlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
NAME='phase_v1241_ns_goal'
def get_goal_entry():
 files=json.loads((C/'PACKAGE_FREEZE.json').read_text())['files']
 assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in files.items()),'PACKAGE_SOURCE_CHANGED'
 if NAME not in sys.modules:
  spec=importlib.util.spec_from_file_location(NAME,C/'goal_package/__init__.py',submodule_search_locations=[str(C/'goal_package')])
  module=importlib.util.module_from_spec(spec);sys.modules[NAME]=module;spec.loader.exec_module(module)
 else:assert Path(sys.modules[NAME].__file__).resolve()==C/'goal_package/__init__.py','PRIVATE_PACKAGE_COLLISION'
 return importlib.import_module(NAME+'.goal_entry')
