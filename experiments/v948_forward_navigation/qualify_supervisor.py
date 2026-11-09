"""Complete supervision seam with real saved entry and explicit synthetic callbacks.

No vehicle dynamics or scans are generated. Endpoint poses in callback fixtures
are assigned test data, never reported as measured motion or real action success.
"""
import copy
import gzip
import hashlib
import importlib.abc
import importlib.util
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'runs/v948_forward_navigation/callback_fixtures04'
SAVED = ROOT/'runs/v858_nav2_verified/v945/main_we'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'factory', 'physical', 'vehicle', 'rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0, NoModel())
sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'experiments/v945_rpccr_observation_liveness')]
spec = importlib.util.spec_from_file_location('prepared_supervisor', ROOT/'experiments/v948_forward_navigation/supervise.py')
supervisor = importlib.util.module_from_spec(spec); spec.loader.exec_module(supervisor)
rows = json.loads(gzip.decompress((SAVED/'COMMAND_TUBES.json.gz').read_bytes()))
routes = json.loads((SAVED/'ROUTER_REQUESTS.json').read_text())
known = json.loads((SAVED/'physics/SETUP.json').read_text())['known']
actual = json.loads((SAVED/'RECOVERY_CORRIDORS.json').read_text())[0]
first=dict(packet=actual['entry_packet'],source=actual['entry_source'])


class Future:
    def __init__(self, result, done=True):
        self.value, self.ready = result, done
    def done(self):
        return self.ready
    def result(self):
        assert self.ready
        return self.value


def run_case(name, label=None):
    folder = OUT/(label or name)
    folder.mkdir(exist_ok=False)
    state = SimpleNamespace(index=-1, now=rows[0]['proof']['issued_at'], phase='history', stopped_reads=0,
                            row=None, sent_path=None, outputs=0, calls=0, canceled=0, follow_ticks=0)
    normal_result = Future(SimpleNamespace(status=5), done=False)
    follow_result = Future(SimpleNamespace(status=4), done=False)

    def snapshot():
        if state.phase=='history':
            row = rows[max(state.index, 0)]
            return copy.deepcopy(row['packet']), copy.deepcopy(row['source'])
        if state.phase=='stopped':
            state.stopped_reads+=1
        p, s = copy.deepcopy(first['packet']), copy.deepcopy(first['source'])
        p['body_measured_at']=state.now; p['sent_at']=state.now
        s['decision_at']=state.now
        if state.phase=='following':
            if name=='live_100ms': p['body_measured_at']=state.now-.1
            if name=='stale_201ms': p['body_measured_at']=state.now-.201
            if name=='stale_scan': s['source_age_s']=.201
        if state.phase=='endpoint':
            p['body']=[*state.sent_path[-1], 0., 0.]
        elif name=='pose_drift' and state.stopped_reads>=3:
            p['body'][0]+=.02
        p['steering']=dict(native_tick=p['native_tick'],measured_at=state.now,position=[0.,0.],velocity=[0.,0.])
        if name=='turned_steering':p['steering']['position']=[-.36,-.52]
        if name=='missing_steering':del p['steering']
        if name=='stale_steering':p['steering']['measured_at']=state.now-.1
        return p,s

    class NormalHandle:
        accepted=True
        def get_result_async(self):
            return normal_result
        def cancel_goal_async(self):
            state.canceled+=1
            if name=='cancel_timeout':
                return Future(None, done=False)
            state.phase='stopped'
            normal_result.ready=True
            return Future(SimpleNamespace(return_code=0))

    class Action:
        def send_goal_async(self, goal):
            state.calls+=1
            if state.calls==1:
                return Future(NormalHandle())
            # Synthetic original-goal completion stops this fixture, not evidence of navigation.
            normal_result.value=SimpleNamespace(status=4); normal_result.ready=True
            return Future(NormalHandle())

    from navigation_policy import ForwardNavigation
    node = SimpleNamespace(forward=ForwardNavigation([4.,-2.]),
        guard_failure=None,
        planner_proxy=SimpleNamespace(known=known, rows=routes),
        tube_decisions=[], motion=SimpleNamespace(out=folder, decision_snapshot=snapshot),
        action=Action(), get_clock=lambda:SimpleNamespace(now=lambda:SimpleNamespace(to_msg=lambda:None)))

    class Binding:
        def __init__(self, node):
            self.client=SimpleNamespace(server_is_ready=lambda:True)
        def send(self, event):
            assert state.phase=='stopped' and state.canceled==1
            state.sent_path=copy.deepcopy(event['path']); state.outputs+=1
            state.phase='following'
            return Future(SimpleNamespace(accepted=name!='follow_rejected', get_result_async=lambda:follow_result))

    def spin(node, timeout_sec):
        if state.phase=='history':
            state.index+=1
            assert state.index<len(rows), 'ACTUAL_HISTORY_DID_NOT_TRIGGER'
            state.now=rows[state.index]['proof']['issued_at']
            node.tube_decisions=rows[:state.index+1]
            if name=='negative_replan' and state.index==10:node.forward.request(-.05,0.)
        elif state.phase=='following':
            state.follow_ticks+=1
            if state.follow_ticks>=3:
                state.phase='endpoint'; follow_result.ready=True
        if name=='turned_steering' and state.phase!='history':state.now+=.005
        if name in ['command_guard_fault','expired_permission'] and state.phase=='stopped':
            node.guard_failure='SYNTHETIC_EXPIRED_PERMISSION' if name=='expired_permission' else 'SYNTHETIC_COMMAND_SAFETY_FAULT'
        time.sleep(.0001)

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    def wait(node, predicate, until, message):
        if name=='cancel_timeout' and message=='NORMAL_CANCEL_TIMEOUT':
            raise TimeoutError(message)
        for _ in range(10000):
            if predicate():
                return
            spin(node, .005)
        raise TimeoutError(message)

    goal=SimpleNamespace(pose=SimpleNamespace(header=SimpleNamespace(stamp=None),
        pose=SimpleNamespace(position=SimpleNamespace(x=4., y=-2.))))
    supervisor.time=SimpleNamespace(monotonic=lambda:state.now, time=lambda:0.)
    supervisor.FollowPathBinding=Binding
    error=None
    try:
        answer, events=supervisor.supervise(node, goal, state.now+180., 1000., spin, wait, require, lambda:None)
    except (AssertionError, TimeoutError, ValueError) as exception:
        error=str(exception)
        events=[]
    saved=json.loads((folder/'RECOVERY_CORRIDORS.json').read_text())
    return dict(scenario=name, error=error, normal_goals=state.calls,
                normal_cancels=state.canceled, follow_submissions=state.outputs,
                trigger_tick=saved[0]['trigger']['trigger']['body_native_tick'] if saved else None,
                synthetic_segment_callbacks=saved, fault=json.loads((folder/'RECOVERY_FAULT.json').read_text()) if (folder/'RECOVERY_FAULT.json').exists() else None,
                models=0, integrations=0, actual_motion_observed=False)


def main():
    OUT.mkdir(exist_ok=True)
    sources=[Path(__file__), ROOT/'experiments/v948_forward_navigation/supervise.py',
             ROOT/'experiments/v945_rpccr_observation_liveness/watchdog.py']
    (OUT/'SUPERVISOR_SOURCE_FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, models=0, integrations=0),indent=2)+'\n')
    global supervisor
    candidate=supervisor
    baseline_spec=importlib.util.spec_from_file_location('baseline_v945_supervisor',ROOT/'experiments/v945_rpccr_observation_liveness/supervise.py')
    baseline=importlib.util.module_from_spec(baseline_spec);baseline_spec.loader.exec_module(baseline)
    supervisor=baseline
    original=run_case('positive','original_same_fixture')
    supervisor=candidate
    cases=[run_case(name) for name in ['positive', 'cancel_timeout', 'pose_drift', 'follow_rejected', 'command_guard_fault','live_100ms','stale_201ms','stale_scan','expired_permission']]
    good=cases[0]
    checks=dict(same_saved_history_entry_as_frozen_supervisor=all(c['trigger_tick']==original['trigger_tick']for c in cases),
                positive_cancels_before_exactly_one_follow=good['error'] is None and good['normal_cancels']==1 and good['follow_submissions']==1,
                positive_resumes_original_goal=good['normal_goals']==2 and len(good['synthetic_segment_callbacks'])==1 and good['synthetic_segment_callbacks'][0]['renewal']['goal']==[4.,-2.],
                cancel_timeout_does_not_follow=cases[1]['error']=='NORMAL_CANCEL_TIMEOUT' and cases[1]['follow_submissions']==0,
                drift_does_not_follow=cases[2]['error']=='POSE_DRIFT_REQUIRES_REPLAN' and cases[2]['follow_submissions']==0,
                rpp_rejection_stops=cases[3]['error']=='RECOVERY_FOLLOW_REJECTED' and cases[3]['normal_goals']==1,
                command_safety_fault_stops_before_follow=cases[4]['error'] is not None and 'COMMAND_CONTRACT_FAILURE' in cases[4]['error'] and cases[4]['follow_submissions']==0)
    checks['100ms_live_full_supervisor_completes_synthetic_segment']=cases[5]['error'] is None and cases[5]['normal_goals']==2
    checks['201ms_stops_with_exact_fault_packet']=cases[6]['error']=='STALE_BODY_LIVENESS' and cases[6]['fault']['input']['stage']=='monitor' and cases[6]['fault']['input']['exact_check_input'] is True and cases[6]['fault']['input']['body_age_s']>.2
    checks['stale_scan_stops']=cases[7]['error']=='STALE_SCAN'
    checks['expired_original_permission_stops']=cases[8]['error'] is not None and 'COMMAND_CONTRACT_FAILURE' in cases[8]['error']
    checks['partial_transaction_events_survive_failure']=all(c['synthetic_segment_callbacks'][0].get('transaction_events') for c in cases if c['error'] is not None)
    checks['every_failure_is_durable']=all(c['fault'] is not None and c['synthetic_segment_callbacks'][0]['fault']==c['fault'] for c in cases if c['error'] is not None)
    negative=run_case('negative_replan')
    checks['negative_normal_request_cancels_before_forward_resume']=negative['error']is None and negative['normal_goals']==2 and negative['normal_cancels']==1 and negative['follow_submissions']==0
    encoder_cases=[run_case(name)for name in ['turned_steering','missing_steering','stale_steering']]
    checks['turned_steering_cannot_install_recovery']=encoder_cases[0]['error']=='RECOVERY_STOP_TIMEOUT'and encoder_cases[0]['follow_submissions']==0
    checks['missing_steering_cannot_install_recovery']=encoder_cases[1]['error']=='MEASURED_STEERING_REQUIRED'and encoder_cases[1]['follow_submissions']==0
    checks['stale_steering_cannot_install_recovery']=encoder_cases[2]['error']=='STALE_STEERING_ENCODERS'and encoder_cases[2]['follow_submissions']==0
    result=dict(encoder_cases=encoder_cases,passed=all(checks.values()),checks=checks,cases=cases,baseline=original,negative_replan=negative,models=0,integrations=0,fixture_cadence_note='Saved command issue timestamps drive this fixture, not exact original asynchronous poll times; compare frozen supervisor under the same fixture.',
                scope='Complete production-supervisor callback fixture; synthetic endpoint and success callbacks are not physical motion or actual goal arrival.')
    (OUT.parent/'SUPERVISOR_QUALIFICATION04.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,errors=[c['error']for c in cases]),indent=2))
    assert result['passed']


if __name__=='__main__':
    main()
