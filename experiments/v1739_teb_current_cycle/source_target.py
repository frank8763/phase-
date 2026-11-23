"""One new frame/pipe/command interface qualification, zero numerical models."""
import ast,copy,ctypes,fcntl,importlib.abc,math,os,runpy,sys,time,traceback
from context import C,O,R,read,put,sha,load,digest
def main():
 start=time.monotonic();assert os.sched_getaffinity(0)=={2}
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1739_original_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','kernel','factory','vehicle','bindings','rclpy'}:raise AssertionError('SOURCE_NO_MODEL:'+name)
 sys.meta_path.insert(0,Ban())
 def no_dll(*a,**k):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=no_dll
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 binding=read(O/'INPUT_BINDING.json');source=binding['files_SHA256'];result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,analytical_native=0,explicit_DLL_loads=0,metadata_FFI_calls=0,optimizer_calls=0)
 try:
  assert all(sha(R/n)==h for n,h in source.items())and all(sha(n)==h for n,h in binding['external_SHA256'].items())
  for p in C.glob('*.py'):ast.parse(p.read_text())
  prior=R/'experiments/v1690_dwa_origin_source_checks'
  reused=[]
  for n in ['capture.py','resources.py','work.py','history_binding.py','transforms.py','runtime_binding.py','error_stop.py','origin.py','obstacles.py']:
   assert sha(C/n)==sha(prior/n);reused.append(n)
  assert ast.dump(ast.parse((C/'quota.py').read_text()),include_attributes=False).replace('native query child has read-only mounts and pipe-only output','no ROS children')==ast.dump(ast.parse((prior/'quota.py').read_text()),include_attributes=False)
  assert sha(C/'api.py')==sha(R/'experiments/v1737_teb_exact_native_aliases/api.py')
  old=(prior/'driver.py').read_text();expected=old.replace("def tail():return error_tail.complete(v,result['error_stop_progress'])","def tail():\n       shared=load('v1694_unchanged_shared_closure',R/'experiments/v1694_shared_observation_closure/contract.py')\n       return shared.complete_closure(v,result['error_stop_progress'],error_tail.complete)")
  assert(C/'driver.py').read_text()==expected,'ORIGINAL_DRIVER_OTHER_STATEMENTS_CHANGED'
  # The whole numerical shadow/retained-stop/feedback body is reused exactly.
  old=(prior/'component.py').read_text();now=(C/'component.py').read_text();a=old.index(' requests=[body_request.copy()');b=old.index(' result=dict(passed=True',a)
  oldtail=old[a:b].replace('DWA','TEB').replace('SVG','TEB');assert now[now.index(' requests=[body_request.copy()'):now.index(' result=dict(passed=True')]==oldtail
  assert(C/'audit_component.py').read_text()==(prior/'audit_component.py').read_text().replace('DWA','TEB').replace('SVG','TEB')
  cfg=read(O/'TEB_CONFIG.json');ref=read(O/'REFERENCE_CONFIG.json');assert cfg['forward']==cfg['backward']==ref['max_speed']==.08 and cfg['omega']==ref['max_yaw_rate']==.16
  assert cfg['acceleration']==ref['max_accel']and cfg['angular_acceleration']==ref['max_delta_yaw_rate']and cfg['maximum_curvature']==ref['maximum_curvature']
  assert cfg['body_half_length']*2==ref['robot_length']and cfg['body_half_width']*2==ref['robot_width']and abs(cfg['min_turning_radius']*cfg['maximum_curvature']-1)<1e-15
  task=read(O/'PILOT_TASK.json');oldtask=read(R/'runs/v1690_dwa_origin_source_checks/PILOT_TASK.json');changed={'task_id','scope','output','run_root','run_id'}
  assert {k:v for k,v in task.items()if k not in changed}=={k:v for k,v in oldtask.items()if k not in changed}
  assert sha(O/'LIMITS_DRAFT.json')==sha(R/'runs/v1690_dwa_origin_source_checks/LIMITS_DRAFT.json')
  frames=load('v1739_new_production_frames',C/'frames.py');velocity=load('v1739_new_production_command',C/'velocity.py')
  # New reference-frame seam only; these are software scalars, no vehicle model.
  errors=[]
  for angle in [-math.pi,-1.,0.,.3,1.,math.pi]:
   body=[1.2,-.8,angle];rear=frames.rear(body);back=frames.centre(rear);errors.extend(abs(x-y)for x,y in zip(body,back))
   for x,y in cfg['footprint']:
    world=[rear[0]+x*math.cos(angle)-y*math.sin(angle),rear[1]+x*math.sin(angle)+y*math.cos(angle)]
    original=[body[0]+(x-.3)*math.cos(angle)-y*math.sin(angle),body[1]+(x-.3)*math.sin(angle)+y*math.cos(angle)];errors.extend(abs(a-b)for a,b in zip(world,original))
  assert max(errors)<1e-12
  p=dict(body=[1.,2.,.4,.03,.1],body_lateral=.02,native_tick=0,sim_time=0.,body_measured_at=11.,sent_at=11.,steering=dict(native_tick=0,position=[0.,0.],velocity=[0.,0.],measured_at=11.),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.))
  origin=dict(packet=p,acquisition_before_monotonic=10.,acquisition_after_monotonic=12.)
  scan=dict(native_tick=0,time=0.,xy=[1.,2.],yaw=.4,ranges=[3.]*32)
  receipt=frames.observation_receipt(origin,scan);before=digest(receipt);wire=frames.encode(receipt,[4.,-2.,0.],[[0.,0.]],cfg)
  assert digest(receipt)==before and abs(wire['query']['vy']+.01)<1e-15 and wire['query']['vx']==.03 and wire['query']['omega']==.1
  assert wire['obstacles']==[dict(x=0.,y=0.,vx=0.,vy=0.,dynamic=0)]and wire['query']['goal_x']==3.7
  velocities=[((.2,0.,.01),(.08,0.,.01)),((-.2,0.,-.3),(-.08,0.,-.16)),((0.,.1,0.),(0.,0.,0.)),((.02,0.,.01),(.02,0.,.01))]
  for raw,wanted in velocities:assert velocity.saturate(*raw,cfg)==wanted
  raw=dict(status=0,vx=.2,vy=0.,omega=.01);mapped=frames.command(raw,cfg);assert mapped['body_request']==[.08,.01,False]and mapped['raw_twist']==[.2,0.,.01]
  negatives=[]
  def reject(name,fn):
   try:fn()
   except (AssertionError,KeyError,FileNotFoundError):negatives.append(name)
   else:raise AssertionError('NEW_SOURCE_NEGATIVE_ACCEPTED:'+name)
  bad=copy.deepcopy(receipt);bad['packet_sha256']='bad';reject('query_receipt_SHA',lambda:frames.encode(bad,[4.,-2.,0.],[[0.,0.]],cfg))
  bad=copy.deepcopy(receipt);bad['scan']['truth']=[123.];reject('scan_truth_field',lambda:frames.encode(bad,[4.,-2.,0.],[[0.,0.]],cfg))
  reject('goal_nonfinite',lambda:frames.encode(receipt,[float('nan'),0.,0.],[[0.,0.]],cfg))
  reject('obstacle_nonfinite',lambda:frames.encode(receipt,[4.,-2.,0.],[[float('inf'),0.]],cfg))
  for label,v,w in [('no_inplace',0.,.1),('deadband',.001,0.),('curvature',.08,.16)]:reject(label,lambda v=v,w=w:frames.command(dict(status=0,vx=v,vy=0.,omega=w),cfg))
  reject('original_optimizer_refusal',lambda:frames.command(dict(status=1,vx=0.,vy=0.,omega=0.),cfg))
  reject('trajectory_time',lambda:frames.trajectory(dict(trajectory=[[0.,0.,0.,1.,0.,0.,0.],[1.,0.,0.,0.,0.,0.,0.]]),cfg))
  reject('actual_entry_before_admission',lambda:runpy.run_path(str(C/'pilot_entry.py'),run_name='__main__'))
  def native_entry():
   before=sys.argv[:];sys.argv=[str(C/'native_query.py'),'--query-once']
   try:runpy.run_path(str(C/'native_query.py'),run_name='__main__')
   finally:sys.argv[:]=before
  reject('native_entry_before_admission',native_entry)
  ns=load('v1739_pure_native_argv',C/'native_namespace.py');argv=ns.command([ns.PYTHON,'-I','-B','-S',str(C/'native_query.py'),'--query-once'],O/'source_argv_only')
  assert '--bind'not in argv and sum(1 for i,x in enumerate(argv)if x=='--ro-bind'and i+2<len(argv)and argv[i+2]in {r['target']for r in read(O/'EXACT_NATIVE_ALIASES.json')['aliases']})==3
  text=(C/'client.py').read_text();assert 'stdin=readonly_input'in text and 'stdin=subprocess.PIPE'not in text and '256*1024'in text
  assert all(sha(R/n)==h for n,h in source.items());put(O/'SOURCE_FREEZE.json',dict(files=source,external_SHA256=binding['external_SHA256'],models_authorized=False))
  result.update(passed=True,source_members=len(source),negative_cases=negatives,reused_unchanged_modules=reused,frame_software_max_error=max(errors),readonly_native_pipe_contract=True,original_numeric_driver_and_audit_reused=True,old_numerical_suites_repeated=False,actual_client_runtime_qualified=False)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
