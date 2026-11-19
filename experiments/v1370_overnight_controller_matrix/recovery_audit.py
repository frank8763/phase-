"""Full recorded prefix/component safety, controls, causality and own replay."""
import gzip
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
from component_context import R,C,O,read,sha
from gear_handoff import GearHandoff
from map_gate import inspect_map
from stamped_contract import assess_delivery,validate_delivery,before_step


def accounting(total,origin,inflight):
    if inflight:return dict(actual_total_native=None,historical_prefix_replay_native=None if total<origin else origin,new_component_native=None)
    assert type(total) is int and total>=0
    return dict(actual_total_native=total,historical_prefix_replay_native=min(total,origin),new_component_native=max(0,total-origin))


def audit(task):
    out=Path(task['output']);result=read(out/'RESULT.json');ros=read(out/'ROS_RESULT.json');setup=read(out/'physics/SETUP.json')
    initial=read(out/'INITIAL_PACKET.json');component=read(out/'COMPONENT_INITIAL_PACKET.json');final=read(out/'FINAL_PACKET.json');journal=read(out/'APPLIED_JOURNAL.json')
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k].copy() for k in z.files}
    n=len(trace['time']);origin=15105
    with gzip.open(out/'physics/CONTACTS.json.gz','rt') as stream:contacts=json.load(stream)
    limits=np.asarray(setup['limits']);ctrl=trace['ctrl'][:,setup['actuator_ids']];rate=np.asarray(setup['slew_per_second'])*.01
    prefix=read(out/'PREFIX_RESTORE.json');original=Path(task['prior_raw']);maximum=0.
    with np.load(original/'physics/NATIVE_TRACE.npz') as old:
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            if trace[k].size:maximum=max(maximum,float(np.max(abs(trace[k][:origin]-old[k][:origin]))))
    counts=accounting(n,origin,False)
    checks=dict(full_recorded=n==len(journal)==result['actual_total_native']==result['own_replay_native'],
        exact_prefix=prefix['passed'] and maximum<=1e-8 and prefix['no_root_state_or_clock_rewrite'],
        exact_count_separation=all(result[k]==v for k,v in counts.items()),
        actual_model_original=setup['model_sha256']==read(original/'physics/SETUP.json')['model_sha256'],
        actual_clearance=bool(trace['clearance'].min()>=.15-1e-8),full_self=bool(trace['self_margin'].min()>=-1e-10),
        finite_state=all(np.isfinite(trace[k]).all() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),
        native_clock=bool(abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8),
        legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all() and (ctrl<=limits[:,1]+1e-10).all()),
        legal_slew=bool((abs(np.diff(np.vstack([initial['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()),
        no_bad_contacts=len(contacts)==n+1 and all(c[2] not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'] for row in contacts for c in row),
        full_own_replay=result.get('replay',{}).get('passed') is True and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        complete_tail=n-origin>=200 and all(z['phase']=='COMPLETE_STOP_TAIL' and z['request']==[0.,0.,False] for z in journal[-200:]),
        sources_unchanged=result['source_unchanged'],
        restored_component_origin=np.max(abs(np.asarray(component['body'])-task['origin_body']))<=1e-8 and component['native_tick']==origin)
    gate=GearHandoff();gate_ok=True
    for row in journal:
        v,w,p=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        gate_ok &= row['applied'] and row['request']==[v,w,False] and row['gear_handoff']==p
    checks['gear_reconstruction']=bool(gate_ok)
    commands=read(out/'ROS_COMMANDS.json');by_sequence={z['sequence']:z for z in commands};fresh=True
    for row in journal[origin:]:
        if row.get('expiry_gate') is None:continue
        sent=by_sequence[row['command_sequence']];delivery=validate_delivery(sent,row['delivery']['validated_monotonic'])
        v,w,p=before_step(*row['raw_upstream_request'][:2],delivery,row['expiry_gate']['applied_monotonic'])
        fresh &= delivery==row['delivery'] and p==row['expiry_gate'] and [v,w,False]==row['upstream_request']
    live=[json.loads(line) for line in (out/'ROS_COMMANDS.jsonl').read_text().splitlines()]
    checks['stamped_source_and_expiry']=bool(fresh)
    checks['complete_ros_evidence']=live==commands and ros['closed'] and not ros.get('evidence_write_errors') and ros['controller_server_exited'] and ros['no_physical_modules_loaded']
    checks['reverse_commands_only']=all(abs(z['v'])<.005 or z['v']<0 for z in commands if z['source']=='CONTROLLER')
    checks['actual_controller_plugin']=all(name in ros['actual_loaded_libraries'] for name in (['libphase_executable_rpp.so'] if task['controller_kind']=='rpp' else ['libphase_deadband_mppi.so','libcoherent.so','libmppi_controller.so']))
    sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
    from dynamic_reserve import check as dynamic
    from recovery_guard import check as static
    guards=True
    for event in read(out/'RESERVE_RECORDS.json'):
        a,p=dynamic(event['body'],task['causal_ball'],*event['requested']);b,q=static(setup['known'],event['body'],*event['requested'])
        guards &= a==event['dynamic_allowed'] and p==event['dynamic_proof'] and b==event['static_allowed'] and q==event['static_proof']
        if not a or not b or not event['direction_ok']:
            sent=by_sequence[event['command_sequence']];guards &= sent['v']==sent['w']==0.
    checks['causal_field_guard_reconstructs']=bool(guards and ros.get('public_static_map_receipt',{}).get('source')==sha(C/'COMMON_GRID.json'))
    map_file=out/'INITIAL_ACTUAL_COSTMAP.json'
    map_proof=inspect_map(read(map_file),read(C/'COMMON_GRID.json')) if map_file.exists() else dict(passed=False,reason='MAP_NOT_RECORDED_BEFORE_OLD_FAILURE')
    checks['full_current_window_public_occupancy']=map_proof['passed']
    checks['independent_allocation']=result.get('independent_allocation',{}).get('passed') is True
    distance=float(np.linalg.norm(trace['qpos'][-1,:2]-task['component_goal_xy']))
    progress=-float(np.dot(trace['qpos'][-1,:2]-task['origin_body'][:2],[math.cos(task['origin_body'][2]),math.sin(task['origin_body'][2])]))
    checks.update(component_functional=result['passed'] and ros['passed'],component_goal=distance<=.08,
        reverse_progress=progress>=.6,final_measured_rest=max(abs(z) for z in final['body'][3:])<=.003,
        final_steering_rest=max(abs(z) for z in final['steering']['velocity'])<=.03,
        final_drive_zero=max(abs(z) for z in final['controller_memory']['last_ctrl'][2:])<=1e-10)
    return dict(passed=all(checks.values()),checks=checks,accounting=counts,own_replay_native=n,
        original_prefix_max_error=maximum,actual_component_goal_distance_m=distance,actual_reverse_progress_m=progress,
        minimum_actual_clearance_m=float(trace['clearance'].min()),models=0,new_physical_native=0,
        scope='shared safe recovery component, not full goalnavigation')
