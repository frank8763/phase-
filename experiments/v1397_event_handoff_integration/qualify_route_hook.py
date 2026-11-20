"""Once-only zero-model integration checkpoint; no production admission."""
import ast
import copy
import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'runs' / HERE.name


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'vehicle', 'torch', 'coupled_model', 'factory', 'physical', 'rclpy'}:
            raise AssertionError('ZERO_MODEL_HOOK_QUALIFICATION:' + name)


sys.meta_path.insert(0, NoModel())
from native_event_frame import acquire
from route_event import CertificateRequired, digest, make_request, validate_envelope
from response_reference import ResponseReference
import route_context


def main():
    assert sorted(os.sched_getaffinity(0)) == [5]
    result_path = OUT / 'ROUTE_HOOK_QUALIFICATION.json'
    assert not result_path.exists(), 'QUALIFICATION_ALREADY_CLOSED'
    os.nice(max(0, 19-os.getpriority(os.PRIO_PROCESS, 0)))
    assert hashlib.sha256((HERE/'event_contract.py').read_bytes()).hexdigest() == '24249fb2450b21141f6bdfa802aba55422f953b306e88c11e4f58d278da0368a'
    class Vector(list):
        def tolist(self): return list(self)
    class Vehicle:
        count = 1000
        d = SimpleNamespace(time=10., qpos=Vector([0.,0.,0.]), qvel=Vector([0.,0.,0.]), ctrl=Vector([0.,0.,0.,0.]), mocap_pos=Vector([]), mocap_quat=Vector([]))
        adapter = SimpleNamespace(last=Vector([0.,0.,0.,0.]), integral=0., parked_target=None, _steering_motion_active=False)
        calls = 0
        def body(self): return [0.,0.,0.,0.,0.]
        def steering_sample(self): return Vector([0.,0.,0.,0.])
        def scan(self):
            self.calls += 1
            return dict(native_tick=self.count, time=self.d.time, xy=[0.,0.], yaw=0., ranges=[3.]*32)
    from route_event import frames
    vehicle = Vehicle(); clock = lambda: 100.
    gear = SimpleNamespace(gear=1, brake_start=None, last_tick=999)
    before = copy.deepcopy(vars(vehicle.d))
    envelope = acquire(vehicle, frames.SampleCache(clock=clock), gear, run_id='hook-fixture', sequence=0, now=clock)
    assert vehicle.calls == 1 and vars(vehicle.d) == before and vehicle.count == 1000
    segment = dict(gear=1, poses=[[-.3,0.,0.],[.7,0.,0.]])
    geometry = dict(start_distance_m=0., start_heading_rad=0., minimum_clearance_m=.23)
    forecast = dict(native_tick=900, periodic_source_tick=850, sim_time=9., center=[2.,1.], radius_m=.6,
                    invariant_for_all_future_under_declared_class=True)
    def request(value=envelope, proof=geometry, prediction=forecast):
        return make_request(value, segment, proof, prediction, run_id='hook-fixture', event_index=0, brake_start=700, now=100.)
    valid = request()
    negative = []
    def reject(name, call):
        try: call()
        except (AssertionError, ValueError, RuntimeError): negative.append(name)
        else: raise AssertionError('NEGATIVE_ACCEPTED:' + name)
    for name, mutate in [
        ('relabeled_scan', lambda e: e['wire'].__setitem__('sampled_at', 100.1)),
        ('old_frame', lambda e: (e['wire'].__setitem__('sampled_at',99.7),e['wire']['sensor_frame'].__setitem__('sampled_at',99.7))),
        ('changed_feedback_body', lambda e: e['feedback']['body'].__setitem__(0,.1)),
        ('wrong_gear_clock', lambda e: e['feedback']['gear_memory'].__setitem__('last_tick',998)),
        ('nonfinite_memory', lambda e: e['feedback'].__setitem__('integral',float('nan'))),
        ('modeled_frame', lambda e: e.__setitem__('kind','MODELED_BODY_CAUSAL_MAP_NOT_SENSOR')),
        ('foreign_run', lambda e: e['wire'].__setitem__('run_id','other')),
    ]:
        changed = copy.deepcopy(envelope); mutate(changed); reject(name, lambda: request(value=changed))
    changed = dict(forecast, periodic_source_tick=1001)
    reject('future_coefficient', lambda: request(prediction=changed))
    reject('missing_forecast', lambda: request(prediction=None))
    reject('wrong_segment_start', lambda: request(proof=dict(geometry,start_distance_m=.1)))
    reject('replayed_observation', lambda: validate_envelope(envelope,run_id='hook-fixture',now=100.,previous_sequence=0))
    steering = copy.deepcopy(envelope); steering['feedback']['encoders'][2] = .031
    assert request(value=steering)['decision']['next_required_gate'] == 'COMPLETE_MEASURED_STOP_AND_STEERING_REST'
    # Execute the exact production cusp AST block, including its serializer.
    tree = ast.parse((HERE/'route_ros.py').read_text())
    block = next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test) == "brake_action == 'segment' and segment_queue")
    hook_rows = []
    for minimum in [.23,.21]:
        proof = dict(geometry,minimum_clearance_m=minimum)
        persisted = []; paths = []
        scope = dict(brake_action='segment',segment_queue=[copy.deepcopy(segment)],tracker=SimpleNamespace(occupied_ball=lambda _:([2.,1.],.6),forecasts=[forecast]),sim_time=10.,
                     validate_segment=lambda *args:(minimum>=.22,proof),center_body=[0.,0.,0.,0.,0.],known={},task=dict(run_id='hook-fixture',planner_guard_m=.22),
                     segment_records=[],native_tick=1000,brake_start=700,dump=lambda p,v:persisted.append((p,copy.deepcopy(v))),out=OUT,
                     measured_envelope=copy.deepcopy(envelope),handoff_requests=[],make_request=make_request,
                     require_certificate=__import__('route_event').require_certificate,time=SimpleNamespace(monotonic=lambda:100.),send_path=lambda p:paths.append(p))
        try: exec(compile(ast.Module(body=[block],type_ignores=[]),str(HERE/'route_ros.py'),'exec'),scope)
        except CertificateRequired as exc:
            assert len(scope['handoff_requests']) == 1 and scope['segment_queue'] == [segment] and not paths
            assert persisted[-1][0].name == 'CURRENT_CUSP_REQUESTS.json'
            hook_rows.append(dict(geometry_passed=minimum>=.22,next_required_gate=exc.request['decision']['next_required_gate'],request_preserved=True,queue_retained=True,paths_sent=0))
        else: raise AssertionError('PRODUCTION_CUSP_BYPASSED_CERTIFICATE')
    states = [[.001*i,0.,0.,0.,0.,0.,0.,0.] for i in range(261)]
    monitor = ResponseReference(valid,states)
    assert monitor.assess([.001,0.,0.,0.,0.],1001)['reference_index'] == 1
    reject('reference_replayed_native',lambda:monitor.assess([.001,0.,0.,0.,0.],1001))
    reject('response_outside_2cm',lambda:monitor.assess([.002,.021,0.,0.,0.],1002))
    reject('response_outside_0p1rad',lambda:monitor.assess([.002,0.,.101,0.,0.],1002))
    reject('response_after_fixed_reference',lambda:monitor.assess([0.,0.,0.,0.,0.],1261))
    changed = copy.deepcopy(valid); changed['event_index'] = 1
    reject('reference_bound_to_changed_event',lambda:ResponseReference(changed,states))
    # Origin translation does not alter relative matching or require a saved tick.
    shifted = copy.deepcopy(valid); shifted['actual']['wire']['native_tick'] += 12345
    shifted.pop('request_sha256'); shifted['request_sha256'] = digest(shifted)
    monitor2 = ResponseReference(shifted,states)
    assert monitor2.assess([.001,0.,0.,0.,0.],13346)['reference_index'] == 1
    original = json.loads((ROOT/'experiments/v1370_overnight_controller_matrix/TASKS.json').read_text())
    task = next(t for t in original if t['task_id']=='rpp_default_horizon_m1_s01_main')
    reject('production_launch_without_complete_backend',lambda:route_context.task_check(task))
    result = dict(passed=True,scope='production cusp-hook AST and read-only acquisition/reference software qualification only',
                  synthetic_fixture=True,not_new_measured_sensor_or_physics=True,read_only_acquisition=True,
                  original_frozen_event_unchanged=True,production_cusp_blocks=hook_rows,negative_cases=negative,
                  tick_translation_invariant=True,complete_route_qualified=False,physical_admission=False,
                  models=0,analytical_native=0,physical_native=0,replay_native=0)
    route_context.dump(result_path,result)
    files = [HERE/name for name in ('route_event.py','native_event_frame.py','response_reference.py','route_context.py','route_ros.py','qualify_route_hook.py')]
    files += [ROOT/'experiments/v1396_rpp_rpc_retirement/frames.py',ROOT/'experiments/v1288_baseline_interface/contract.py',HERE/'event_contract.py']
    route_context.dump(OUT/'ROUTE_HOOK_SOURCE_FREEZE.json',dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},qualification=str(result_path.relative_to(ROOT)),physical_admission=False,models=0))
    print(json.dumps(result))


if __name__ == '__main__': main()
