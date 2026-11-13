"""The actual failed root is a fixture; no physical imports or integrations."""
import sys, json, importlib.abc, copy, tempfile, time
from pathlib import Path
R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs/v1091_certified_exit'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'physical', 'vehicle', 'torch', 'rclpy'}:
            raise AssertionError('NO_MODEL_QUALIFICATION ' + name)
sys.meta_path.insert(0, NoModel())
sys.path.insert(0, str(R / 'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
sys.path.insert(0, str(R / 'experiments/rpccr_execution_core'))
sys.path.insert(0, str(C))
import stop, numpy as np
def main():
    started = time.monotonic()
    x = json.loads((R / 'runs/v1090_recert_failure_diagnosis/ACTUAL_SAVED_INPUT.json').read_text())
    stage = json.loads((R / 'runs/v858_nav2_verified/v1090/main_west_east/ACTIVE_CORRIDOR_STAGES.json').read_text())[0]
    source = stage['source']; packet = x['packet']; setup = x['setup']
    before = json.dumps(packet, sort_keys=True)
    failed, _, _ = stop.corridor.proof(setup, packet, source, np.array(stage['requests'])[4375:])
    assert not failed['passed'] and [k for k,v in failed['checks'].items() if not v] == ['full_raw_geometry']
    proof, states, controls, requests = stop.plan(setup, packet, source)
    assert json.dumps(packet, sort_keys=True) == before
    assert proof['native'] == 2200 and proof['minimum_full_cycle_raw_m'] >= .24353421020226934
    short, _, _ = stop.corridor.proof(setup, packet, source, requests[:-1])
    assert not short['passed'] and not short['checks']['complete2200stop']
    bad = copy.deepcopy(setup)
    bad['known']['known_circles'].append([packet['body'][0], packet['body'][1], .1])
    try:
        stop.plan(bad, packet, source)
        raise RuntimeError('UNSAFE_STOP_WAS_ACCEPTED')
    except AssertionError as e:
        assert str(e) == 'NO_CERTIFIED_ACTUAL_EXIT'
    # Actual installation and control dispatch, but no model is created here.
    from types import SimpleNamespace
    class Fake:
        count = packet['native_tick']
        def __init__(self): self.d = SimpleNamespace(qvel=np.zeros(6)); self.index=0
        def step(self, *r):
            assert np.array_equal(r, np.zeros(3)); self.count += 1; self.index += 1
            self.d.qvel[:2] = states[self.index, 3:5]
        def body(self):
            s = states[self.index]; return [s[0],s[1],s[2],s[3],s[5]]
        def steering_sample(self):
            # Use the original virtual->Ackermann fixture, not stale front cache.
            from recovery_source import forecast_packet
            p = forecast_packet(packet, states[self.index], np.r_[controls[self.index-1],0.], self.index)
            return np.r_[p['steering']['position'],p['steering']['velocity']]
    with tempfile.TemporaryDirectory(dir=O) as tmp:
        f = Fake()
        def reject(): raise AssertionError(stop.REJECTION)
        try:
            stop.after_rejection(reject, f, setup, lambda *a: copy.deepcopy(packet), source, tmp)
            raise RuntimeError('REJECTED_NAVIGATION_RETURNED_SUCCESS')
        except stop.ControlledStop as e:
            assert e.record['completed'] and not e.record['navigation_passed']
            assert f.index == 2200
    f = Fake()
    try:
        stop.after_rejection(lambda: (_ for _ in ()).throw(AssertionError('NATIVE_SAFETY_ANOMALY')), f, setup, lambda *a: packet, source, O)
    except AssertionError as e:
        assert str(e) == 'NATIVE_SAFETY_ANOMALY' and f.index == 0
    result = dict(passed=True, models=0, integrations=0, actual_saved_root=24535,
                  old_rejection_reproduced=True, stop_proof=proof,
                  short_tail_rejected=True, unsafe_stop_rejected=True,
                  packet_and_memory_unmodified=True, production_dispatch_2200=True,
                  rejected_navigation_never_passes=True, physical_anomaly_not_intercepted=True,
                  wall_s=time.monotonic()-started)
    (O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
if __name__ == '__main__': main()
