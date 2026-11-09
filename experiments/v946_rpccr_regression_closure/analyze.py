"""Closed full-native V945 reference tracking and independent audit diagnosis."""
import copy
import importlib.abc
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v946_rpccr_regression_closure'
RAW=ROOT/'runs/v858_nav2_verified/v945/main_we'
CODE=ROOT/'experiments/v945_rpccr_observation_liveness'
REC=ROOT/'records/nav2_v945_20261109'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','vehicle','physical','factory','rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(CODE))
from corridor_audit import body_rows,tracking


def read(name):return json.loads((RAW/name).read_text())


def main():
    assert json.loads((ROOT/'runs/v945_rpccr_observation_liveness/COMPLETION.json').read_text())['closed']
    native=read('RESULT.json');ros=read('ROS_RESULT.json');fault=read('RECOVERY_FAULT.json')
    with np.load(RAW/'physics/NATIVE_TRACE.npz')as z:
        body=body_rows(z)
    rows=read('RECOVERY_CORRIDORS.json');reports=[]
    for row in rows:
        start=row['install_packet']['native_tick'];end=row.get('end_packet',{}).get('native_tick',len(body))
        result=tracking(row['proposal']['path'],body[start-1:end])
        path=np.asarray(row['proposal']['path'])
        straight=bool(np.ptp(path[:,2])<1e-12)
        first=None
        if straight:
            yaw=body[start-1:end,2]-path[0,2]
            delta=abs(np.arctan2(np.sin(yaw),np.cos(yaw)))
            bad=np.flatnonzero(delta+.758770385*.00025>.035)
            if len(bad):
                i=int(bad[0]);first=dict(native_tick=start+i,seconds_from_install=i*.01,
                                       actual_body=body[start+i-1].tolist(),reference_yaw=float(path[0,2]),
                                       heading_error_rad=float(delta[i]),required_max_rad=.035)
        reports.append(dict(trigger_tick=row['entry_packet']['native_tick'],install_tick=start,
                            action_endpoint_tick=end,action_completed=row['passed'],
                            measured_goal_progress_m=row.get('renewal',{}).get('measured_segment_progress_m'),
                            tracking=result,reference_is_straight=straight,first_heading_violation=first))
    # Original audit short-circuited on corridor tracking; evaluate the remaining
    # independent evidence gates separately without changing its failed result.
    independent={}
    for name,function in [('motion_audit','audit'),('tube_audit','audit_tubes'),
                          ('ingress_audit','audit_ingress'),('recovery_audit','audit')]:
        sys.path.insert(0,str(CODE))
        module=__import__(name)
        try:
            result=getattr(module,function)(RAW)
            independent[name]=result
        except Exception as error:
            independent[name]=dict(passed=False,error=repr(error))
    latest=ros['last_observation']
    result=dict(status='NOT_PASSED',models=0,integrations=0,actual_native=native['actual_native'],
                own_replay_native=native['replay_native'],private_native=native['private_native'],
                goal_distance_m=native['goal_distance_m'],minimum_clearance_m=read('INDEPENDENT_AUDIT.json')['minimum_clearance_m'],
                bad_contacts=read('INDEPENDENT_AUDIT.json')['bad_contacts'],
                state_replay_error=read('INDEPENDENT_AUDIT.json')['maximum_state_error'],
                postdiscovery_actual_travel_m=read('INDEPENDENT_AUDIT.json')['independently_recomputed_postdiscovery_travel_m'],
                recovered_action_segments=len([x for x in reports if x['action_completed']]),
                independently_qualified_complete_segments=sum(x['tracking']['passed']and x['action_completed']for x in reports),
                segments=reports,independent_remaining_evidence=independent,
                runtime_error=ros['error'],fault_stage=fault['input']['stage'],
                exact_failed_snapshot_saved=fault['input']['exact_check_input'],
                catch_time_since_last_received_body_s=fault['observed_at']-latest['body_measured_at'],
                catch_time_since_last_received_scan_s=fault['observed_at']-latest['scan_measured_at'],
                snapshot_context_note='Snapshot producer raised before returning a new packet; saved input is explicitly the previous successful snapshot. Catch-time ages are not the unrecorded internal comparison instant.',
                current_nominal_lookahead_m=json.loads((CODE/'A_motion.yaml').read_text())['controller_server']['ros__parameters']['FollowPath']['lookahead_dist'],
                maximum_native_wall_lag_s=native['maximum_wall_lag_s'],
                old_v943_50ms_monitor_abort_reappeared=False,
                complete_arrival_or_dynamic_acceptance=False,
                next_design='First reproduce complete saved straight-reference heading error and actual ROS callback scheduling under fixed input; qualify compatible corridor tracking and isolate observation I/O from heavy callbacks. No larger freshness bound or new physical retry in this closed batch.')
    (OUT/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    (REC/'POSTMORTEM.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='independent_remaining_evidence'},indent=2))
    print('remaining gates',{k:v['passed']for k,v in independent.items()},flush=True)


if __name__=='__main__':main()
