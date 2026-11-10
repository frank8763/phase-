"""Execute the revised native loop on a deliberately nonphysical counter peer.

No factory, model, physics integrator, policy controller or ROS is imported.
The fixture only tests stop/file/counter/exception control flow.
"""
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
from types import ModuleType, SimpleNamespace as S

C = Path(__file__).parent
R = C.resolve().parents[1]
O = R/'runs/v981_tracking_evidence_closure'
sys.path.insert(0, str(C))
from baseline_red import NoModel
sys.meta_path.insert(0, NoModel())
from closure import dump, request_stop


def exercise(label):
    # Output is explicitly identified as software and is bounded to this repo.
    out = R/'runs/v858_nav2_verified/v981_software'/label
    out.mkdir(parents=True, exist_ok=False)
    relative_socket = Path('runs')/('v981_fixture_'+label)
    sockdir = R/relative_socket
    sockdir.mkdir()
    origin = 6083
    model_calls = []  # List must remain empty, independently of fixture counts.
    class Counter:
        def __init__(self):
            self.count = origin
            self.d = S(time=origin*.01)
            self.component_snapshot = dict(time=self.d.time)
        def body(self):
            return [0., 0., 0., 0., 0.]
        def scan(self):
            return dict(time=self.d.time)
        def native(self):
            if label == 'native_interrupted' and self.count == origin+4:
                raise InterruptedError('FIXTURE_NATIVE_RETURN_INTERRUPTED')
            self.count += 1
            self.d.time = self.count*.01
        def step(self, *args):
            self.native()
        def finish(self):
            receipt = json.loads((out/'NATIVE_ACCOUNTING.json').read_text())
            assert receipt['final'] is False and receipt['own_full_trace_replay_native_exact'] is None
            if label == 'save_failure':
                raise OSError('FIXTURE_SAVE_FAILURE')
            (out/'physics').mkdir(exist_ok=True)
            dump(out/'physics/FIXTURE_TRACE.json', dict(fixture=True, recorded_counter=self.count, models=0))
            return dict(fully_recorded_native=self.count, final_body=self.body(), bad_contacts=0,
                        goal_distance_m=1., final_translation_speed_m_s=0.)
    fake = ModuleType('physical')
    def create(outpath, task):
        return Counter()
    def replay(vehicle, deadline, folder):
        receipt = json.loads((out/'NATIVE_ACCOUNTING.json').read_text())
        assert receipt['status'] == 'TRACE_SAVE_ATTEMPTED_BEFORE_REPLAY'
        if label == 'replay_interrupted':
            dump(folder/'REPLAY_PROGRESS.json', dict(executed_replay_native=3))
            raise InterruptedError('FIXTURE_REPLAY_INTERRUPTED')
        return dict(replay_native=vehicle.count, passed=True, fixture=True)
    fake.create_vehicle, fake.replay = create, replay
    sys.modules['physical'] = fake
    class Startup:
        def __init__(self, run_id):
            self.phase = 'WAITING'
            self.armed_at = None
            self.events = []
        def _journals(self):
            self.receipts, self.execution = [], []
        def receive(self, packet, now, tick, simulation_time):
            if packet['kind'] == 'arm':
                self.phase, self.armed_at = 'RUNNING', now
            elif packet['kind'] == 'stop':
                self.phase = 'STOPPING'
            self.receipts.append(packet)
        def controls(self, now):
            return 0., 0., True
        def step(self, vehicle, now):
            vehicle.step(0., 0., True)
            self.execution.append(dict(counter=vehicle.count))
    spec = importlib.util.spec_from_file_location('v981_actual_loop_'+label, C/'native_loop.py')
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    engine.Startup = Startup
    engine.authorized = lambda *args: time.time()+90
    engine.verify_sources = lambda *args: None
    engine.policy_packet = lambda *args: dict(fixture=True)
    task = dict(output=str(out), socket_dir=str(relative_socket), run_id=label,
                wall_limit_s=.5, brake_s=2., origin_native_tick=origin, origin_sim_time=origin*.01, stage='component')
    errors = []
    def peer():
        try:
            until = time.monotonic()+4
            while not (out/'NATIVE_READY.json').exists():
                assert time.monotonic() < until
                time.sleep(.002)
            if label == 'prearm_stop':
                request_stop(out, label, 'FIXTURE_ROS_FAILURE_BEFORE_ARM')
                return
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
                sock.sendto(json.dumps(dict(kind='arm')).encode(), str(relative_socket/'physics.sock'))
            while not (out/'PARTIAL.json').exists():
                assert time.monotonic() < until
                time.sleep(.002)
            request_stop(out, label, 'FIXTURE_ROS_FAILURE')
        except BaseException as error:
            errors.append(repr(error))
    thread = threading.Thread(target=peer)
    affinity = os.sched_getaffinity(0)
    thread.start()
    try:
        result = engine.run(task, {}, 'FIXTURE_NO_PHYSICAL_AUTHORIZATION')
    finally:
        thread.join(timeout=5)
        os.sched_setaffinity(0, affinity)
        sys.modules.pop('physical')
    assert not errors and not thread.is_alive()
    (R/relative_socket).rmdir()
    receipt = json.loads((out/'NATIVE_ACCOUNTING.json').read_text())
    assert receipt['final'] and not result['passed'] and not receipt['navigation_passed'] and not model_calls
    assert (out/'INGRESS.json.gz').is_file()
    if label == 'native_interrupted':
        assert result['actual_native'] is None and result['new_branch_native'] is None
        assert receipt['count_status'] == 'UNKNOWN_INTERRUPTED_NATIVE_CALL'
        assert receipt['new_branch_native_observed_lower_bound'] == 4
    else:
        assert receipt['new_branch_native_exact'] == result['actual_native']-origin
    if label == 'save_failure':
        assert not result['evidence_save_complete'] and result['replay_native'] is None
    elif label == 'replay_interrupted':
        assert result['replay_native'] is None and result['replay_completed_native_lower_bound'] == 3
    elif label == 'prearm_stop':
        assert result['actual_native'] == origin and result['new_branch_native'] == 0
    else:
        assert result['evidence_save_complete']
    return dict(label=label, passed=True, fixture_counter_total=result['actual_native'],
                fixture_replay_counter=result['replay_native'], native_status=result['status'],
                accounting=receipt, models=0, physical_integrations=0)


def main():
    cases = [exercise(label) for label in ['ros_failure', 'prearm_stop', 'save_failure', 'replay_interrupted', 'native_interrupted']]
    result = dict(passed=all(row['passed'] for row in cases), cases=cases, models=0, actual_native=0,
                  private_native=0, replay_native=0, fixtures_are_counters_not_model_integrations=True,
                  actual_revised_native_loop_exercised=True)
    (O/'NATIVE_LOOP_QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
