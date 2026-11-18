"""Actual configured EW owner under generic-module cache poisoning; no models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_CACHE_CHECK '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import types
def main(order):
    assert order in ['prebind_then_legacy','legacy_then_prebind']
    assert read(O/'APPROVAL.json')['models_authorized']is False
    if order=='prebind_then_legacy':bound=load('phase_v1261_prebound_live',C/'ew_live.py')
    science();saved={}
    for name in ['ew_live','ew_handoff','goal_entry','current_goal_source','candidate_search','connection','admission','audit_chain']:
        wrong=types.ModuleType(name);wrong.__file__='synthetic_wrong_'+name;sys.modules[name]=wrong;saved[name]=wrong
    now=time.time();mono=time.monotonic();window=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    owner=configure_owner(O,now+1000,window)
    actual=sys.modules['phase_v1261_live_owner']
    assert Path(actual.__file__).resolve()==C/'ew_live.py'and actual.component.__name__=='phase_v1261_immutable_ew_component'
    assert Path(actual.component.__file__).resolve()==R/'experiments/v1255_ew_component_entry/ew_handoff.py'
    assert callable(owner.execute)and callable(owner.navigate)and all(sys.modules[n]is m for n,m in saved.items())
    print(json.dumps(dict(passed=True,order=order,actual_live_owner_bound=True,generic_modules_untouched=True,models=0,physical_native=0)))
if __name__=='__main__':main(sys.argv[1])
