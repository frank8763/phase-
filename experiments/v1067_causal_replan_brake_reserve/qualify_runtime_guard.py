"""Use the exact legacy filesystem hook after setup, without creating a model."""
import importlib.abc,sys,json
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from planner import library;from brake_reserve import Reserve;from entry_record import save;from initial_contract import check_setup
raw=R/'runs/v858_nav2_verified/v1067/qualification_io_guard';out=raw/'entry';(out/'physics/paired').mkdir(parents=True,exist_ok=False);x=json.loads((R/'runs/v1066_actual_route_diagnosis/EW_SAVED_ACTUAL_INPUT.json').read_text());lib=library();old=json.loads((R/'runs/v1065_preflight_metadata_continuation_20261111/PREFLIGHTS.json').read_text());cases=[]
for reference in old.values():
 case=reference['task']['case_id'];meta=json.loads((O/(case+'_T0_METADATA.json')).read_text());assert check_setup(reference['setup'],meta);cases.append(case)
assert len(cases)==3
B=load('v1067_actual_frozen_write_guard',R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py');B.OUT=R/'runs/v858_nav2_verified';sys.addaudithook(B.write_guard)
assert library()._name==lib._name;Reserve(x['setup']);assert json.loads((O/'EAST_WEST_STATIC_SOURCE.json').read_text())['passed'];outside_denied=False
try:(O/'FORBIDDEN_GUARD_WRITE').write_text('no')
except PermissionError:outside_denied=True
assert outside_denied
B.OUT=out/'physics/paired';save(out,dict(passed=False,error='EXPECTED_ZERO_MODEL_ENTRY_FAILURE',model_initializations=None,navigation_native=0,own_replay_native=0,private_mujoco_native=0));assert not(out/'RESULT.json').exists()and(out/'physics/paired/ENTRY_FAILURE_RESULT.json').exists();B.OUT=R/'runs/v858_nav2_verified';dump(raw/'RESULT.json',dict(passed=True,precompiled_analytical_library_read_only_under_real_guard=True,legacy_expander_cache_available_without_writes=True,public_metadata_read_after_hook=True,outside_write_rejected=True,entry_failure_fallback_saved_without_models=True,three_saved_actual_setup_contracts=cases,models=0,integrations=0));print(json.dumps(dict(passed=True,models=0)),flush=True)
