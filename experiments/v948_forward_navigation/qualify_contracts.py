"""Saved-state direction and exact fault boundary regressions; no model imports."""
import ast
import copy
import gzip
import importlib.abc
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]; CODE=Path(__file__).parent
OUT=ROOT/'runs/v948_forward_navigation'; OUT.mkdir(exist_ok=True)


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco','torch','vehicle','factory','physical','rclpy'}:
            raise AssertionError('FORBIDDEN_MODEL_IMPORT '+name)


sys.meta_path.insert(0,NoModel())
sys.path[:0]=[str(CODE),str(ROOT/'experiments/v945_rpccr_observation_liveness')]
from navigation_policy import ForwardNavigation, require_forward_path
import motion_publisher as publisher

saved=ROOT/'runs/v858_nav2_verified/v945/main_we'
plans=json.loads((saved/'PLANS.json').read_text())
rows=json.loads(gzip.decompress((saved/'COMMAND_TUBES.json.gz').read_bytes()))
row=rows[-1]; packet=row['packet']; source=row['source']
checks={}; failures={}


def rejected(name, call, match):
    try: call()
    except Exception as error:
        failures[name]=str(error)
        return match in str(error)
    return False


checks['actual_v945_reversing_path_is_red']=rejected(
    'old_reference',lambda: require_forward_path(plans[-1]['path']), 'CONTAINS_REVERSE')
flow=ForwardNavigation([4.,-2.])
checks['negative_normal_requests_cancel_replan']=not flow.request(-.05,0.) and flow.replan_requested
checks['zero_request_creates_no_motion']=flow.request(0.,0.) is True
checks['resume_recovers_original_forward_goal']=flow.resume([4.,-2.])==dict(
    action='NAVIGATE_FORWARD_TO_ORIGINAL_GOAL',goal=[4.,-2.],original_goal_success=False) and not flow.replan_requested
checks['recovery_endpoint_not_success_or_new_target']=rejected(
    'changed_goal',lambda:flow.resume([3.,-2.]),'ORIGINAL_GOAL_CHANGED')
checks['implicit_reverse_escape_disabled']=rejected(
    'escape',lambda:flow.reverse_escape(), 'NOT_QUALIFIED')
checks['normal_forward_reference_accepted']=flow.reference([[0.,0.,0.],[.1,0.,0.]])['forward_only']
checks['nonfinite_request_rejected']=rejected('nonfinite',lambda:flow.request(float('nan'),0.),'NONFINITE')

# Exercise the actual publisher method with a saved packet and no ROS constructor.
def fixture(cls):
    obj=cls.__new__(cls); obj.lock=threading.RLock(); obj.running=True
    obj._decision_packet=copy.deepcopy(packet);obj.scan_monotonic=packet['scan_measured_at']
    obj.tracker=SimpleNamespace(latest={'native_tick':source['source_native_tick']},
        when=source['source_scan_sim_time'],support=None,last_hit=source['last_hit_time'])
    obj.periodic=SimpleNamespace(last=None)
    return obj

now=max(packet['sent_at'],packet['scan_measured_at'])+.1
publisher.time=SimpleNamespace(monotonic=lambda:now)
publisher.old.time=SimpleNamespace(monotonic=lambda:now)
new=fixture(publisher.MotionPublisher); old=fixture(publisher.old.MotionPublisher)
checks['fresh_snapshot_identical_to_original']=new.decision_snapshot()==old.decision_snapshot()
now=max(packet['sent_at'],packet['scan_measured_at'])+.201
checks['original_stale_snapshot_red']=rejected('old_stale',old.decision_snapshot,'STALE_COHERENT')
try: new.decision_snapshot()
except publisher.ObservationFault as error:
    detail=error.evidence
    checks['new_stale_is_still_rejected']=str(error)=='STALE_COHERENT_OBSERVATION'
    checks['exact_failed_input_retained']=detail['packet']==packet and detail['checked_at']==now and detail['exact_check_input']
    checks['exact_ages_retained']=detail['body_sent_age_s']==now-packet['sent_at'] and detail['scan_measured_age_s']==now-packet['scan_measured_at']
else: checks['new_stale_is_still_rejected']=False
now=packet['sent_at']-.051
checks['future_timestamp_rejected']=rejected('future',new.decision_snapshot,'FUTURE_COHERENT')
for path in CODE.glob('*.py'):ast.parse(path.read_text(),str(path))
checks['source_parse']=True
cfg=json.loads((CODE/'A_forward.yaml').read_text())
checks['normal_planner_dubin']=cfg['planner_server']['ros__parameters']['GridBased']['motion_model_for_search']=='DUBIN'
checks['rpp_reversing_disabled']=cfg['controller_server']['ros__parameters']['FollowPath']['allow_reversing']is False
checks['selector_exact_qualified_v947']=(CODE/'rpccr_recovery.py').read_bytes()==(ROOT/'experiments/v947_rpccr_forward_commitment/forward_selector.py').read_bytes()
checks['physical_gate_closed']=json.loads((CODE/'READINESS.json').read_text())['physical_ready']is False
result=dict(passed=all(checks.values()),checks=checks,red_reasons=failures,
    models=0,integrations=0,scope='Software direction/fault boundaries only; no new path or physical arrival claim.')
(OUT/'CONTRACT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],checks=len(checks),failed=[k for k,v in checks.items()if not v],red_reasons=failures)))
assert result['passed']
