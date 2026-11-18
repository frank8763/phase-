"""One frozen known-course dispatcher, three fresh routes, no old raw replay."""
from pathlib import Path
import sys,os,time,json,hashlib,math,importlib.util
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1184_three_route_entry'
sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
import chain_tools as old
import chain as bridge
q=old.q;np=q.np;load=old.load;read=old.read;dump=old.dump;sha=old.sha;GUARD=old.GUARD;previous=old.previous;packet=old.packet;pin=old.pin;RESOURCE=old.RESOURCE
def remaining(w=None):return old.remaining(w or read(O/'ROUND_WINDOW.json'))
def source_ok():return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def task_contract(t):
    spec=read(R/'experiments/v1089_route_scene_contract/SCENE_CONTRACT.json')['routes'][t['case_id']]['case']
    ids={'WEST_EAST':(10010001,.6573753567727383),'NORTH_SOUTH':(10010002,3.673083947600074),'EAST_WEST':(10010003,.9511239917756753)}
    assert (t['seed'],t['phase'])==ids[t['case_id']] and t['dynamic']is True
    assert t['start_xy']==spec['start_xy'] and t['goal_xy']==spec['goal_xy'] and t['start_yaw']==spec['yaw']
    assert t['scope']=='three_known_course_fresh_feedback_development' and t['historical_prefix_native']==0 and t['native_limit']==60000
    assert t['role']in ['main','repeat'] and t['task_id']==t['role']+'_'+t['case_id']
    assert t['run_root']==str(O) and Path(t['output'])==R/'runs/v858_nav2_verified/v1184'/t['task_id']
    return True
def configure_owner(output,end):
    owner=old.configure_owner(output,end)
    import budget
    budget.O=O;budget.RAW=R/'runs/v858_nav2_verified/v1184';budget.LIMIT=2*1024**3
    sys.path.insert(0,str(C))
    import route_policy
    owner.execute=lambda *args:route_policy.execute(*args,output=Path(output))
    return owner
def factory():
    f=load('v1184_registered_course_factory',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');f.O=O
    f.create=f.create_vehicle
    # Use the current exact replay with this round's deadline, not a closed old window.
    f.replay=load('v1184_deadline_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay
    return f
def finite_plan(case):
    if case=='NORTH_SOUTH':
        p=read(R/'runs/v1182_ns_timing_alignment/SELECTED_PLAN.json');return p['input'],p['rows']
    assert case=='EAST_WEST'
    task=next(t for t in read(R/'experiments/v1181_remaining_route_transfer/TASKS.json')if t['id']==case)
    return read(R/task['input']),task['rows']
