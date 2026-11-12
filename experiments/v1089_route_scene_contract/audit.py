"""Same 25 scientific gates plus route-aware full scene-model byte binding."""
import sys,json,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1086_ns_complete_repeat'))
import audit as original_audit
ORIGINAL=original_audit.ORIGINAL
def patched_source():
 s=original_audit.patched_source();old="setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8'";assert s.count(old)==1
 return s.replace(old,"__import__('route_scene_contract').verify_saved(ph,task)['passed']")
def configure():
 spec=importlib.util.spec_from_file_location('route_scene_contract',C/'contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.modules['route_scene_contract']=m
if __name__=='__main__':
 configure();exec(compile(patched_source(),str(ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(ORIGINAL)))
