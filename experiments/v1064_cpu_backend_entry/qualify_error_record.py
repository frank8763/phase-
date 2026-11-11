"""Real inherited write guard: the fallback stays inside bootstrap OUT."""
import sys,importlib.util,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
from resource_policy import apply
apply()
from entry_record import save
out=R/'runs/v1063_night_entry_continuation_20261111/entry_record_fixture';inner=out/'physics/paired';inner.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('v1063_actual_legacy_guard',R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);guard.OUT=inner;sys.addaudithook(guard.write_guard);record=dict(passed=False,error='INTENTIONAL_STARTUP_FAILURE',model_initializations=None,navigation_native=0,own_replay_native=0,private_mujoco_native=0);save(out,record);assert not(out/'RESULT.json').exists()and json.loads((inner/'ENTRY_FAILURE_RESULT.json').read_text())==record;print(json.dumps(dict(passed=True,models=0,integrations=0,original_write_guard_enforced=True,outer_write_denied_inner_record_kept=True)))
