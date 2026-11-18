"""New NS source audited against the complete real native trajectory."""
from campaign_context import *
import gzip
projection=load('v1265_ns_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
core=load('v1265_ns_core_audit',R/'experiments/v1204_goal_audit_worker/audit_goal.py')
causal=load('v1265_ns_causal_audit',R/'experiments/v1204_goal_audit_worker/native_audit.py')
admission=load('v1265_ns_admission_audit',C/'ns_admission_audit.py')
terminal_audit=load('v1265_terminal_independent',R/'experiments/v1227_terminal_contract_capture/audit_terminal.py')
def load_ns_bundle(path):
 b=core.load_bundle(path);b['terminal_record']=read(path/'TERMINAL_PREVIEW.json')
 with np.load(path/'TERMINAL_PREVIEW.npz')as z:b['terminal_arrays']={k:z[k].copy()for k in z.files}
 return b

def verify_goal(x,table,bundle,external,deadline):
 assert x['setup']['case']['id']=='NORTH_SOUTH'
 assert bundle['initial']['method']=='current_state_NS_retained_balanced_seeded_fallback'
 if bundle['initial']['prefix_rows']is not None:assert bundle['initial']['entry_recovery_contract']=='certified_entry_recovery_then22mm_goal' and 'handoff'in bundle
 assert bundle['result']['generations'][0]['method']=='current_state_NS_retained_balanced_seeded_fallback'
 proposal=None
 if bundle['initial'].get('proposal_method'):
  proposal=load('v1265_independent_proposal',R/'experiments/v1241_fine_route_reconnection/audit_proposal.py').verify(bundle['initial'])
 first=core.verify(x,table,bundle,False,external=external)
 second=admission.verify_bundle(x,table,bundle,deadline)
 record=bundle['terminal_record'];offset=record['offset'];t=bundle['trace']
 target_reference=bundle['onward_ref']['states']if 'handoff'in bundle else bundle['initial_ref']['states']
 expected_offset=(bundle['initial']['prefix_native']if 'handoff'in bundle else 0)+len(target_reference)-1
 assert offset==expected_offset
 origin=dict(record['origin'],state=t['states'][offset],last_ctrl=t['memory'][offset,:4],integral=t['memory'][offset,4])
 engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);initial=dict(q.initial(x['packet']),steering_load_episode=False)
 sh,_,mm=engine.simulate(initial,[q.accelerator.row(float(v),float(w))for v,w,_ in t['requests'][:offset]])
 so=dict(record['shadow_origin'],state=sh[-1],last_ctrl=mm[-1,:4],integral=mm[-1,4])
 terminal=terminal_audit.verify(x,table,origin,so,offset,target_reference[-1,:3],record,bundle['terminal_arrays'])
 return dict(passed=True,core=first,admission=second,terminal=terminal,proposal=proposal,analytical_cpp_native=first['analytical_cpp_native']+second['analytical_cpp_native']+engine.native+terminal['analytical_cpp_native'])
def audit(task,qualification_output=None):
 assert task['case_id']=='NORTH_SOUTH' and qualification_output is None
 out=Path(task['output']);r=read(out/'RESULT.json');assert r['passed']and r['error']is None
 base=load('v1265_ns_all_native',C/'audit_refusal.py').audit(task,output_path=out/'BASE_NATIVE_AUDIT.json')
 setup=read(out/'physics/SETUP.json')
 with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
 if task['slot']==13:
  prefix=read(R/'runs/v858_nav2_verified/v1243/main_slot13/LIVE_GOAL_INPUT.json')['packet']['native_tick']
  with np.load(R/'runs/v858_nav2_verified/v1243/main_slot13/physics/NATIVE_TRACE.npz')as old_trace:
   for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
    assert trace[key][:prefix].shape==old_trace[key][:prefix].shape and (not trace[key][:prefix].size or abs(trace[key][:prefix]-old_trace[key][:prefix]).max()<=1e-8),'ORIGINAL_PRE_SOURCE_PREFIX_CHANGED'
 states=np.vstack([q.initial(read(out/'CANONICAL_INITIAL_PACKET.json'))['state'],projection(trace['qpos'],trace['qvel'],setup)])
 commands=np.array(read(out/'physics/BODY_COMMANDS.json'))
 with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
 x=read(out/'LIVE_GOAL_INPUT.json');gs=x['packet']['native_tick']
 assert gs==r['recovery_origin_native']and previous.stopped(x['packet'])and abs(q.initial(x['packet'])['state']-states[gs]).max()<=1e-8
 table=causal.table_check(out,'LIVE_GOAL',x,sensors)
 final=read(out/'ACTUAL_FINAL_PACKET.json');applied=read(out/'APPLIED_JOURNAL.json')
 memory=np.asarray([row['last_ctrl']+[row['integral']]for row in applied[gs:]]+[final['controller_memory']['last_ctrl']+[final['controller_memory']['integral']]])
 external=dict(states=states[gs:],controls=trace['ctrl'][gs:,setup['actuator_ids']],memory=memory,requests=commands[gs:][:,[1,2,5]])
 bundle=load_ns_bundle(out/'CURRENT_GOAL_ENTRY');goal=verify_goal(x,table,bundle,external,time.monotonic()+150)
 assert r['physical']['actual_travel_after_detection_m']>=1. and np.linalg.norm(states[-1,:2]-task['goal_xy'])+.08<=.45
 result=dict(passed=True,physical_audit_complete=True,actual_replay_verified=True,full_current_causal_domain_rebuilt=True,goal=goal,native_reviewed=len(trace['time']),minimum_native_actual_clearance=float(trace['clearance'].min()),analytical_cpp_native=goal['analytical_cpp_native'],models=0,new_mujoco_native=0,formal_retained_commit=False)
 dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
