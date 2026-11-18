"""One frozen known-course dispatcher, three fresh routes, no old raw replay."""
from pathlib import Path
import sys,os,time,json,hashlib,math,importlib.util
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1195_eight_gib_timed_refuge'
sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
import chain_tools as old
import chain as bridge
q=old.q;np=q.np;load=old.load;read=old.read;dump=old.dump;sha=old.sha;GUARD=old.GUARD;previous=old.previous;packet=old.packet;pin=old.pin;RESOURCE=old.RESOURCE
def remaining(w=None):return old.remaining(w or read(O/'ROUND_WINDOW.json'))
def source_ok():return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def task_contract(t):
    spec=read(R/'experiments/v1089_route_scene_contract/SCENE_CONTRACT.json')['routes'][t['case_id']]['case']
    assert t['dynamic']is True and t['scope']=='frozen_eight_gib_timed_refuge_relay'and t['historical_prefix_native']==0 and t['native_limit']==60000
    assert t['start_xy']==spec['start_xy']and t['goal_xy']==spec['goal_xy']and t['start_yaw']==spec['yaw']
    if t['group']=='routes':
        ids={'WEST_EAST':(10010001,.6573753567727383),'NORTH_SOUTH':(10010002,3.673083947600074),'EAST_WEST':(10010003,.9511239917756753)}
        assert (t['seed'],t['phase'])==ids[t['case_id']] and t['slot']==0 and t['role']in['main','repeat']
        expected='routes_'+t['role']+'_'+t['case_id']
    else:
        original=next(x for x in read(C/'ORIGINAL_TASK_LIST.json')if x['slot']==t['slot'])
        assert(t['seed'],t['phase'],t['case_id'])==(original['seed'],original['phase'],original['case_id'])
        assert (t['group']=='recovery'and t['slot']in[1,2]and t['role']in['main','repeat'])or(t['group']=='preflight'and t['role']=='t0')or(t['group']=='confirmation'and t['role']in['main','repeat'])
        assert t['group']!='confirmation' or t['role']!='repeat' or t['slot']in[1,9,17]
        expected=t['group']+'_'+t['role']+'_slot'+str(t['slot']).zfill(2)
    assert t['task_id']==expected and t['run_root']==str(O)and Path(t['output'])==R/'runs/v858_nav2_verified/v1195'/expected
    return True
def configure_owner(output,end):
    owner=old.configure_owner(output,end)
    import budget
    budget.O=O;budget.RAW=R/'runs/v858_nav2_verified/v1195';budget.LIMIT=8*1024**3
    sys.path.insert(0,str(C))
    import night_dispatch
    owner.execute=lambda *args:night_dispatch.execute(*args,output=Path(output))
    return owner
def factory():
    f=load('v1195_registered_course_factory',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');f.O=O
    f.create=f.create_vehicle
    # Use the current exact replay with this round's deadline, not a closed old window.
    f.replay=load('v1195_deadline_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay
    return f
def finite_plan(case):
    if case=='NORTH_SOUTH':
        p=read(R/'runs/v1182_ns_timing_alignment/SELECTED_PLAN.json');return p['input'],p['rows']
    assert case=='EAST_WEST'
    task=next(t for t in read(R/'experiments/v1181_remaining_route_transfer/TASKS.json')if t['id']==case)
    return read(R/task['input']),task['rows']

def shared_used():
    auth=read(R/'runs/v1192_eight_gib_relay/AUTHORIZATION.json')
    return sum(p.stat().st_size for n in auth['storage_roots']for root in[R/n]if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def output_of(task):
    mapping=read(O/'RESUME_MAP.json')
    old=next((r for r in mapping['stages']if r['stage']==task['task_id']),None)
    return old['original_output']if old else task['output']
def resume_check(mapping):
    if not mapping['stages']:return True
    assert read(O/'CANDIDATE.json')['id']=='A','CROSS_CANDIDATE_RESULT_REUSE_FORBIDDEN'
    for row in mapping['stages']:
        assert row['reused_completed_task']and row['functional_passed']and row['safety_evidence_passed']and row['result']['passed']and row['audit']['passed']
        p=Path(row['original_output']);assert p.is_relative_to(R/'runs/v858_nav2_verified/v1191')or p==R/'runs/v858_nav2_verified/v1189/recovery_main_slot01'
        assert read(p/'RESULT.json')==row['result']
    return True
