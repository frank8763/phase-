"""Exact generic actual prefix auditor; explicit fixed pre-discovery component."""
import ast,copy,gzip,hashlib,sys
from pathlib import Path
from context import SOURCE,R,C,read,load,sha
PARENT=R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py'

def generic_ast(source):
 assert source[str(PARENT.relative_to(R))]==sha(PARENT),'ORIGINAL_AUDITOR_SHA'
 fn=next(n for n in ast.parse(PARENT.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='audit')
 i=next(i for i,n in enumerate(fn.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='segments'for t in n.targets))
 assert "DIRECT_SEGMENTS.json"in ast.unparse(fn.body[i])and i>10
 keep=copy.deepcopy(fn.body[:i])
 assert all(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)for a,b in zip(keep,fn.body[:i]))
 fn.body=keep+ast.parse("return dict(n=n,states=states,trace=trace,commands=commands,journal=journal,maximum_controller_error=maximum,maximum_memory_error=memoryerror,setup=setup,p0=p0,sensors=sensors,contacts=contacts)").body
 return ast.fix_missing_locations(fn),dict(generic_original_statements_preserved=i,original_SHA256=sha(PARENT),generic_AST_SHA256=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest(),removed_only_old_discovery_and_whole_task_scope=True)

def audit(task,result,source):
 dependency=R/'experiments/v1195_eight_gib_timed_refuge';before=sys.path[:];sys.path.insert(0,str(dependency))
 try:
  module=load('v1670_exact_actual_generic_auditor',PARENT)
  fn,seam=generic_ast(source);space=vars(module).copy();exec(compile(ast.Module(body=[fn],type_ignores=[]),str(C/'audit_component.py'),'exec'),space)
  scratch=dict(result,passed=False,error=None,functional_failure=dict(reason='FIXED_SVG_COMPONENT_NOT_ARRIVAL'))
  generic=space['audit'](task,result_override=scratch)
 finally:sys.path[:]=before
 np=module.np;q=module.q;n=generic['n'];assert n==2210
 out=Path(task['output']);ss=generic['states'];trace=generic['trace'];commands=generic['commands'];setup=generic['setup'];p0=generic['p0']
 origin_binding=load('v1685_independent_origin_receipt',C/'origin.py');origin=origin_binding.verify_receipt(read(out/'CURRENT_MEASURED_ORIGIN.json'),p0)
 proof=read(out/'CURRENT_SHADOW_CERTIFICATE.json');assert proof['passed']and proof['origin_packet']==origin and proof['origin_packet_sha256']==origin_binding.digest(origin)
 solver=read(out/'CURRENT_SOLVER_INPUT.json')['origin'];proposal=read(out/'DWA_SELECTED_CURRENT_PROPOSAL.json');assert solver['origin_packet']==origin and solver['origin_packet_sha256']==origin_binding.digest(origin)and proposal['source_packet']==origin
 with np.load(out/'CURRENT_SHADOW.npz')as z:shadow={k:z[k].copy()for k in z.files}
 assert np.array_equal(commands[:,[1,2,5]],shadow['requests'])and np.array_equal(shadow['requests'][-2200:],np.zeros((2200,3)))
 error=ss-shadow['states'];limits=np.array([.04,.035,.015]);maximum=np.array([np.linalg.norm(error[:,:2],axis=1).max(),abs(np.arctan2(np.sin(error[:,2]),np.cos(error[:,2]))).max(),abs(error[:,6]).max()]);assert(maximum<=limits).all()
 receipts=read(out/'CURRENT_ADMISSION_RECEIPTS.json');assert len(receipts)==2 and [row['offset']for row in receipts]==list(range(0,10,5))
 assert receipts[0]['proof']['origin_packet']==origin and receipts[0]['proof']['origin_packet_sha256']==origin_binding.digest(origin)
 for row in receipts:
  one=row['proof'];assert one['passed']and all(one['checks'].values())and one['source_native']==row['offset']and abs(one['source_sim_time']-.01*row['offset'])<=1e-8
  # Bind the admission origin to actual measured full state and reconstructed memory.
  actual=q.initial(one['origin_packet']);assert abs(np.asarray(actual['state'])-ss[row['offset']]).max()<=1e-8
 final=read(out/'ACTUAL_FINAL_PACKET.json');assert module.previous.stopped(final)
 with np.load(out/'FULL_STATE_NPLUS1.npz')as z:
  for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']:
   value=z[key];assert len(value)==n+1
   if value[1:].size:assert np.max(abs(value[1:]-trace[key]))<=1e-8
 physical=result['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['fully_recorded_native']==n
 assert physical['first_actor_detection']is None,'COMPONENT_MUST_STAY_PRE_DISCOVERY'
 static=sys.modules['kernel'].ref._old.Geometry(setup['known'],None).clearances(ss[:,:3])[0];assert static.min()>=.15-1e-8
 distance=float(np.linalg.norm(ss[-1,:2]-np.asarray(task['goal_xy'])))
 answer=dict(passed=True,scope='INDEPENDENT_CURRENT_DWA_CYCLE_COMPONENT_NOT_NAVIGATION',actual_native=n,own_replay_native=result['own_replay_native'],whole_navigation_passed=False,actual_original_goal_reached=distance<=.45,original_goal_distance_m=distance,maximum_actual_tracking=maximum.tolist(),maximum_controller_error=generic['maximum_controller_error'],maximum_memory_error=generic['maximum_memory_error'],all_actual_clearance_m=float(trace['clearance'].min()),all_static_fullfootprint_actual_m=float(static.min()),generic_original_checks_seam=seam,complete_zero_stop_native=2200,current_measured_admissions=2,explicit_allocator_compute_calls=n,internal_Allocator_constructions=None,model_work_total=None,new_physical_native_during_audit=0,qualification_only=False)
 module.dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
