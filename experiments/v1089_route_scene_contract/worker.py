"""Original navigation, only qualified route scene validation replaces NS SHA."""
import sys,types,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
spec=importlib.util.spec_from_file_location('v1088_exact_prior_worker',R/'experiments/v1088_remaining_routes/worker.py')
prior_worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior_worker)
ORIGINAL=prior_worker.ORIGINAL
OLD="assert setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8'"
NEW="__import__('route_scene_contract').verify_live(v,task)"
def configure():
 import importlib.util
 s=importlib.util.spec_from_file_location('route_scene_contract',C/'contract.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);sys.modules['route_scene_contract']=m
def patched_source():
 s=prior_worker.patched_source();assert s.count(OLD)==1;s=s.replace(OLD,NEW)
 old="assert task['kind']in ['main','repeat']";assert s.count(old)==1;s=s.replace(old,"assert task['kind']in ['main','repeat']")
 # Physical count/controls/predictions untouched. Explicit boot invalidation before factory.
 anchor="w=json.loads((O/'ROUND_WINDOW.json').read_text());"
 assert s.count(anchor)==1;s=s.replace(anchor,anchor+"assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'CROSS_BOOT_AUTHORITY_REJECTED';")
 return s
def load_worker():
 configure();m=types.ModuleType('qualified_route_scene_worker');m.__file__=str(ORIGINAL);exec(compile(patched_source(),str(ORIGINAL),'exec'),m.__dict__);return m
if __name__=='__main__':
 configure();exec(compile(patched_source(),str(ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(ORIGINAL)))
