"""Recorded-only heading/command diagnosis; no physical imports or propagation."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[2]
RAW = R / 'runs/v858_nav2_verified/v1296/left_main'
O = R / 'runs/v1296_rpp_turn_brake'


def main():
    result = json.loads((RAW / 'RESULT.json').read_text())
    audit = json.loads((RAW / 'FINAL_INDEPENDENT_AUDIT.json').read_text())
    rows = json.loads((RAW / 'APPLIED_JOURNAL.json').read_text())
    task = json.loads((RAW / 'TASK.json').read_text())
    with np.load(RAW / 'physics/NATIVE_TRACE.npz') as z:
        trace = {k:z[k].copy() for k in z.files}
    q = trace['qpos']; yaw = np.unwrap(np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2)))
    requests = np.array([r['request'] for r in rows],float)
    measured_speed = trace['qvel'][:,0]*np.cos(yaw)+trace['qvel'][:,1]*np.sin(yaw)
    measured_w = trace['qvel'][:,5]
    n = len(rows); nav = next(i for i,r in enumerate(rows) if r['phase']=='COMPLETE_STOP_TAIL')
    chunks = []
    for first,last in [(0,500),(500,1000),(1000,nav),(nav,n)]:
        chunks.append(dict(first_native=first+1,last_native=last,
                           command_v_mean=float(requests[first:last,0].mean()),
                           command_w_mean=float(requests[first:last,1].mean()),
                           actual_v_mean=float(measured_speed[first:last].mean()),
                           actual_w_mean=float(measured_w[first:last].mean()),
                           commanded_yaw_integral=float(requests[first:last,1].sum()*.01),
                           measured_yaw_rate_integral=float(measured_w[first:last].sum()*.01),
                           final_actual_yaw=float(yaw[last-1])))
    ignored = {'component_functional','independent_terminal_heading'}
    evidence = {k:v for k,v in audit['checks'].items() if k not in ignored}
    assert all(evidence.values()) and result['replay']['passed'] and not result['passed']
    assert abs(float(yaw[-1])-.16834137347109554)<1e-10
    assert abs(result['terminal_heading_error_rad']-.13165862652890448)<1e-10
    assert len(rows)==1680 and nav==1480 and n-nav==200
    params=json.loads((R/'experiments/v1296_rpp_turn_brake/params.json').read_text())['controller_server']['ros__parameters']
    ref=np.asarray(task['reference_path']);last=np.asarray(result['physical']['final_body'])
    dx,dy=ref[-1,:2]-last[:2];bearing=math.atan2(float(dy),float(dx))
    proof=dict(recorded_diagnosis_passed=True,component_passed=False,
               navigation_attempts=1,navigation_successes=0,unexecuted=['left_repeat','right_main','right_repeat'],
               safety_replay_and_recording_checks_passed=True,evidence_checks=evidence,
               actual_native=n,own_replay_native=result['own_replay_native'],simulation_time_s=n*.01,
               maximum_control_replay_error=result['replay']['maximum_qpos_qvel_ctrl_mocap_error'],
               component_goal_error_m=result['component_goal_distance_m'],actual_yaw=float(yaw[-1]),
               desired_terminal_yaw=task['component_goal_yaw'],terminal_heading_error=result['terminal_heading_error_rad'],
               maximum_radial_error=result['maximum_arc_radial_error_m'],
               whole_command_yaw_integral=float(requests[:nav,1].sum()*.01),
               terminal_point_bearing=bearing,actual_heading_vs_terminal_bearing=float(math.atan2(math.sin(last[2]-bearing),math.cos(last[2]-bearing))),
               goal_checker_yaw_tolerance=params['goal_checker']['yaw_goal_tolerance'],
               rpp_rotate_to_heading=params['RPP']['use_rotate_to_heading'],lookahead_m=params['RPP']['lookahead_dist'],
               phase_chunks=chunks,
               findings=['Actual RPP action succeeded at positional component goal, independently required terminal tangent heading failed.',
                         'Actual vehicle yaw initially lags requested yaw. Later RPP yaw request decreases almost to zero and becomes slightly negative before positional completion.',
                         'The native goal checker yaw tolerance pi does not enforce this new component terminal heading criterion; planar tracking and braking passed.',
                         'No evidence of a second controller overwriting ctrl: independent allocation and own full replay error0. This does not establish perfect physical response to nominal body commands.'],
               limits=['One exposed component, not general RPP failure or RP-CCR regression.',
                       'No causal intervention or tuned variant was physically executed; lookahead/terminal handling/plant response contributions not separately identified.',
                       'Do not fix by relaxing terminal gate or enabling in-place rotation for this car.'],
               next_design=['Retain common vehicle adapter; examine causal endpoint-aware lookahead/curvature handling using saved observations first.',
                            'Test candidate against the same closed saved input and geometry; preserve original component gates and old failure.',
                            'New physical task needs a separately frozen bounded protocol; no automatic retry.'],
               models=0,new_physical_native=0,analytical_vehicle_native=0)
    (O/'FAILURE_DIAGNOSIS.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(proof,ensure_ascii=False))


if __name__=='__main__':
    main()
