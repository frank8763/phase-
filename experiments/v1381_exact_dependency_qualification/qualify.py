"""Actual import-path regression, red on original production callable identity."""
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('NO_PHYSICAL_DIAGNOSIS '+name)
sys.meta_path.insert(0,NoPhysical())
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    frozen=json.loads((O/'SOURCE_FREEZE.json').read_text())['files'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    base=R/'experiments/v1380_timed_handoff_component';sys.path.insert(0,str(base))
    module=load('phase_v1381_original_native_readonly',base/'native.py');expected=base/'prefix_restore.py'
    actual=Path(module.restore.__code__.co_filename).resolve()
    assert actual==R/'experiments/v1372_coherent_sampling_fault/prefix_restore.py','ORIGINAL_FAILURE_NOT_REPRODUCED'
    try:assert actual==expected,'PRODUCTION_RESTORE_WRONG_SOURCE'
    except AssertionError as error:original_rejection=str(error)
    else:raise AssertionError('ORIGINAL_BAD_BINDING_ACCEPTED')
    fixed=load('phase_v1381_exact_prefix_restore',expected);module.restore=fixed.restore
    expected_functions={'restore':('prefix_restore.py',module.restore),'Capture':('controller.py',module.Capture.select),'Geometry':('geometry_contract.py',module.Geometry.actual),'membership':('geometry_contract.py',module.membership),'certify':('reserve.py',module.certify),'wire_packet':('frames.py',module.wire_packet),'SampleCache':('frames.py',module.SampleCache.__init__),'GearHandoff':('gear_handoff.py',module.GearHandoff.select),'before_step':('stamped_contract.py',module.before_step)}
    identities={}
    for name,(path,fn) in expected_functions.items():
        source=Path(fn.__code__.co_filename).resolve();assert source==base/path,(name,str(source));identities[name]=str(source.relative_to(R))
    assert module.restore is fixed.restore and Path(module.restore.__code__.co_filename).resolve()==expected
    assert 'mujoco' not in sys.modules and 'vehicle' not in sys.modules
    result=dict(passed=True,original_red_case=original_rejection,original_loaded_restore=str(actual.relative_to(R)),expected_restore=str(expected.relative_to(R)),private_memory_binding_passed=True,production_function_sources=identities,
        actual_physical_entry_patched=False,old_frozen_sources_edited=False,new_physical_authority=False,physics_restart=False,
        models=0,analytical_native=0,physical_native=0,replay_native=0,
        next_requirement='Any future separately-authorized component must pin these private source identities in its production loader and assert them before first model initialization; do not restart V1380.')
    assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    p=O/'QUALIFICATION.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');assert json.loads(p.read_text())==result;print(json.dumps(result))
if __name__=='__main__':main()
