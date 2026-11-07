"""Shared actual audit callsite; optional explicitly labeled zero-model dry-run."""
import argparse,importlib.abc,json,os,runpy,sys,types
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--saved-only',action='store_true');ap.add_argument('--omit-legacy-path',action='store_true');ap.add_argument('worker');ap.add_argument('script');ap.add_argument('arguments',nargs=argparse.REMAINDER);a=ap.parse_args()
repo=Path(__file__).resolve().parents[2];own=repo/'experiments'/a.worker
assert own.is_dir() and a.script.endswith('.py') and '/' not in a.script
if not a.omit_legacy_path:
 for directory in [repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1']:
  sys.path.insert(0,str(directory))
sys.path.insert(0,str(own));os.environ['PHASE_REPO']=str(repo)
if a.saved_only:
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name=='mujoco' or name.startswith('mujoco.'):
    raise RuntimeError('QUALIFICATION_FORBIDS_MODEL_CONSTRUCTION_AND_INTEGRATION')
 sys.meta_path.insert(0,NoModels())
 if a.script=='audit_run.py':
  # Import/callsite dry-run ONLY. This is not an independent MJB metadata audit.
  import numpy as np
  pair=Path(a.arguments[0]);contract=json.loads((pair/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json').read_text())
  module=types.ModuleType('mujoco')
  def saved_metadata_only(path):
   assert Path(path)==pair/'scene_model.mjb'
   ranges=np.zeros((max(contract['ids'])+1,2));ranges[contract['ids']]=contract['limits']
   return types.SimpleNamespace(actuator_ctrlrange=ranges)
  module.MjModel=types.SimpleNamespace(from_binary_path=saved_metadata_only)
  sys.modules['mujoco']=module
elif a.script!='replay_native_audit.py':
 # Canonical auditor may read the actual MJB metadata, but no auditor can step.
 import mujoco
 def denied(*args,**kwargs):raise RuntimeError('AUDITOR_INTEGRATION_FORBIDDEN')
 mujoco.mj_step=mujoco.mj_step1=mujoco.mj_step2=denied
sys.argv=[str(own/a.script),*a.arguments];runpy.run_path(sys.argv[0],run_name='__main__')
