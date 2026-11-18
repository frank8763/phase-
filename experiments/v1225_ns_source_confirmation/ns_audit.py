"""New NS source audited against the complete real native trajectory."""
from campaign_context import *
import gzip
projection=load('v1225_ns_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
core=load('v1225_ns_core_audit',R/'experiments/v1204_goal_audit_worker/audit_goal.py')
causal=load('v1225_ns_causal_audit',R/'experiments/v1204_goal_audit_worker/native_audit.py')
admission=load('v1225_ns_admission_audit',C/'audit_admission.py')
def verify_goal(x,table,bundle,external,deadline):
 assert x['setup']['case']['id']=='NORTH_SOUTH'
 assert bundle['initial']['method']=='current_state_NS_direct_control_space' and bundle['initial']['prefix_rows']is None
 assert bundle['result']['generations'][0]['method']=='current_state_NS_direct_control_space'
 first=core.verify(x,table,bundle,False,external=external)
 second=admission.verify_bundle(x,table,bundle,deadline)
 return dict(passed=True,core=first,admission=second,analytical_cpp_native=first['analytical_cpp_native']+second['analytical_cpp_native'])
def audit(task,qualification_output=None):
 assert task['case_id']=='NORTH_SOUTH' and qualification_output is None
 out=Path(task['output']);r=read(out/'RESULT.json');assert r['passed']and r['error']is None
 base=load('v1225_ns_all_native',C/'audit_refusal.py').audit(task,output_path=out/'BASE_NATIVE_AUDIT.json')
 setup=read(out/'physics/SETUP.json')
 with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
 states=np.vstack([q.initial(read(out/'CANONICAL_INITIAL_PACKET.json'))['state'],projection(trace['qpos'],trace['qvel'],setup)])
 commands=np.array(read(out/'physics/BODY_COMMANDS.json'))
 with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
 x=read(out/'LIVE_GOAL_INPUT.json');gs=x['packet']['native_tick']
 assert gs==r['recovery_origin_native']and previous.stopped(x['packet'])and abs(q.initial(x['packet'])['state']-states[gs]).max()<=1e-8
 table=causal.table_check(out,'LIVE_GOAL',x,sensors)
 final=read(out/'ACTUAL_FINAL_PACKET.json');applied=read(out/'APPLIED_JOURNAL.json')
 memory=np.asarray([row['last_ctrl']+[row['integral']]for row in applied[gs:]]+[final['controller_memory']['last_ctrl']+[final['controller_memory']['integral']]])
 external=dict(states=states[gs:],controls=trace['ctrl'][gs:,setup['actuator_ids']],memory=memory,requests=commands[gs:][:,[1,2,5]])
 bundle=core.load_bundle(out/'CURRENT_GOAL_ENTRY');goal=verify_goal(x,table,bundle,external,time.monotonic()+150)
 assert r['physical']['actual_travel_after_detection_m']>=1. and np.linalg.norm(states[-1,:2]-task['goal_xy'])+.08<=.45
 result=dict(passed=True,physical_audit_complete=True,actual_replay_verified=True,full_current_causal_domain_rebuilt=True,goal=goal,native_reviewed=len(trace['time']),minimum_native_actual_clearance=float(trace['clearance'].min()),analytical_cpp_native=goal['analytical_cpp_native'],models=0,new_mujoco_native=0,formal_retained_commit=False)
 dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
