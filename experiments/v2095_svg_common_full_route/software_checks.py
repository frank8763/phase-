"""Bounded source preparation using closed inputs and explicit software doubles."""
import ast,copy,fcntl,hashlib,importlib.abc,json,os,subprocess,sys,traceback,types
from pathlib import Path
from context import R,C,O,SOURCE,read,put,sha,load,digest,predecessors_closed
P=R/'runs/v2090_svg_persistent_counter_fixture';A=P/'actual'
def run():
 assert not(SOURCE/'SOURCE_ONCE.json').exists();predecessors_closed()
 out=SOURCE/'software_checks_03';out.mkdir(exist_ok=False)
 result=dict(passed=False,models=0,DLLs=0,constructors=0,solver_queries=0,physical_native=0,replay=0,formal_claims=0)
 try:
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,name,*args):
    if name.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
  sys.meta_path.insert(0,Ban());import numpy as np
  pins={};prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())
  def pinned(p):pins[str(p.relative_to(R))]=sha(p);return read(p)
  frames=[pinned(A/f'SVG_QUERY_{i}_FRAME.json')for i in range(2)]
  receipts=[pinned(A/f'cycle_{i:04d}_origin.json')['receipt']for i in range(2)]
  replies=[pinned(A/f'SVG_QUERY_{i}_RESULT.json')for i in range(2)]
  selected=pinned(A/'SVG_SELECTED_SEGMENT.json');oldtask=pinned(P/'PILOT_TASK.json')
  protocol=load('SVG_new_peer_clock_test',C/'peer_contract.py');third=copy.deepcopy(frames[1]);third['request'].update(native_tick=2205,sim_time=22.05);third['maps']['source_request_sha256']=digest(third['request']);third['maps_sha256']=digest(third['maps'])
  wire=lambda x:json.dumps(x,allow_nan=True).encode()+b'\n'
  protocol.decode(wire(frames[0]),sequence=0,run_id=oldtask['run_id']);protocol.decode(wire(frames[1]),sequence=1,run_id=oldtask['run_id'],previous_native=0);protocol.decode(wire(third),sequence=2,run_id=oldtask['run_id'],previous_native=5)
  negatives=[]
  def reject(label,fn):
   try:fn()
   except (AssertionError,ValueError,KeyError):negatives.append(label)
   else:raise AssertionError('BAD_INPUT_ACCEPTED:'+label)
  reject('stale_native',lambda:protocol.decode(wire(frames[1]),sequence=2,run_id=oldtask['run_id'],previous_native=5))
  reject('count_cap',lambda:protocol.decode(wire(third),sequence=12000,run_id=oldtask['run_id']))
  reject('foreign_run',lambda:protocol.decode(wire(third),sequence=2,run_id='foreign'))
  reject('first_nonzero',lambda:protocol.decode(wire(frames[1]),sequence=0,run_id=oldtask['run_id']))
  reject('old_counter_semantics',lambda:protocol.verify_author_counts([1,2],attempts=2,returns=2,code=0))
  reject('failed_native_return',lambda:protocol.verify_author_counts([2,2],attempts=2,returns=2,code=-1))
  assert protocol.verify_author_counts([3,3],attempts=3,returns=3,code=0)['author_solve_returns']==3
  # Exercise the actual production Client and original OutputBoundary in the
  # actual readonly ROS namespace, replacing ONLY the executable with a named
  # software peer which cannot load a controller or vehicle.
  boundary=load('SVG_original_actual_OutputBoundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');client=load('SVG_production_Client_source_test',C/'native_client.py');actual_load=client.load;actual_read=client.read;saved=[];charges=[]
  def fixture_load(label,path):
   m=actual_load(label,path)
   if label=='SVG_readonly_original_ROS_namespace':
    def command(args):assert args[-1]==str(C/'native_worker.py');return m.command([*args[:-1],str(C/'software_peer.py')])
    return types.SimpleNamespace(environment=m.environment,command=command)
   return m
  def fixture_read(path):
   value=actual_read(path);return dict(value,output=str(out))if Path(path)==O/'PILOT_TASK.json'else value
  def debit(path,n):assert path.is_relative_to(out.resolve());charges.append(n);assert sum(charges)<=1024**2
  def save(n,x):saved.append(n);put(out/n,x)
  client.load=fixture_load;client.read=fixture_read
  with boundary.OutputBoundary(out,debit):
   peer=client.Client(save,frames[0])
   try:answers=[peer.query(),peer.query(frames[1]),peer.query(third)];assert all(x['explicit_software_fixture']for x in answers)and peer.calls==3
   finally:peer.close()
  assert peer.p.returncode==0 and peer.channel.closed
  logs=read(out/'SVG_NATIVE_CONSOLE.json')['lossless'];codec_log=load('SVG_lossless_nonreply_source_test',C/'console_codec.py');raw=list(codec_log.decoded_chunks(out/logs['path']));assert len(raw)==7 and sum(x.startswith(b'SVG_EVENT ')for x in raw)==6 and raw[-1].startswith(b'SVG_CLOSED ')
  assert hashlib.sha256(b''.join(raw)).hexdigest()==logs['raw_SHA256']
  # New actual compact-query auditor, with two closed real current frames and
  # original actually executed commands. This is a readout test, not replay or
  # a new safety audit of the closed component.
  compact=load('SVG_source_compact_codec',C/'compact_record.py');audit=load('SVG_source_compact_audit_seam',C/'audit_component.py');actual_sha=audit.sha;audit.sha=lambda p:sha(P/'SOURCE_FREEZE.json')if p==SOURCE/'SOURCE_FREEZE.json'else actual_sha(p)
  auditout=out/'query_readout';auditout.mkdir();put(auditout/'plan_00_segments.json',[selected]);records=[]
  for i in range(2):
   base=f'cycle_{i:06d}';value=compact.pack(cycle=i,receipt=receipts[i],selected=selected,frame=frames[i],reply=replies[i],source_freeze_sha256=sha(P/'SOURCE_FREEZE.json'));records.append(value)
   put(auditout/(base+'_query.json'),value);put(auditout/(base+'_origin.json'),dict(origin_native=5*i,receipt=receipts[i]));put(auditout/(base+'_selection.json'),dict(plan_index=0,segment_index=0,selected_segment_sha256=digest(selected)))
   put(auditout/(base+'_proposal.json'),pinned(A/f'SVG_QUERY_{i}_PROPOSAL.json'));put(auditout/(base+'_executed.json'),dict(kind='SVG_control_cycle'))
  put(auditout/'SVG_NATIVE_CLOSED.json',pinned(A/'SVG_NATIVE_CLOSED.json'));commands=np.asarray(pinned(A/'physics/BODY_COMMANDS.json'),float)
  assert audit.audit_queries(np,auditout,oldtask,prior,commands,False)['query_records']==2
  bad=copy.deepcopy(records[0]);bad['reply']['raw']['run_id']='foreign';put(auditout/'cycle_000000_query.json',bad)
  reject('foreign_saved_reply_in_actual_auditor',lambda:audit.audit_queries(np,auditout,oldtask,prior,commands,False));put(auditout/'cycle_000000_query.json',records[0])
  for name,change in [('source_freeze',lambda x:x.update(source_freeze_sha256='0'*64)),('segment_SHA',lambda x:x.update(selected_segment_sha256='0'*64)),('transport_SHA',lambda x:x['reply']['transport_ack'].update(sha256='0'*64)),('authority',lambda x:x.update(actual_execution_permitted=True))]:
   value=copy.deepcopy(records[0]);change(value);b=compact.Rebuilder(prior,source_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),run_id=oldtask['run_id'])
   try:reject(name,lambda:b.check(np,value,selected=selected,goal_xy=oldtask['goal_xy']))
   finally:b.close()
  # Twelve task identities are locked before any outcomes, all original fields.
  locked=pinned(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');plan=read(SOURCE/'PLAN_LOCKED.json')
  for row,original in zip(plan['tasks'],locked['tasks']):
   path=R/row['root']/'PILOT_TASK.json';t=read(path);assert sha(path)==row['task_sha256']
   for k,v in original['task'].items():
    if k not in {'task_id','output','method','run_id','run_root'}:assert t[k]==v,(k,row)
   assert t['common_task_id']==original['task']['task_id']and t['method']=='SVG-MPPI'and not t['component_not_navigation']and t['stop_native']==2200
  # Original full response/numerical calls are exact; the extended navigator
  # retains both complete predictions and per-five actual tracking gates.
  assert (C/'response.py').read_bytes()==(R/'experiments/v2090_svg_persistent_counter_fixture/response.py').read_bytes()
  def calls(path,name):return[ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(path.read_text()))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr==name]
  for name in ['phase_svg_create','phase_svg_set_maps','phase_svg_solve','phase_svg_destroy']:assert calls(C/'native_worker.py',name)==calls(R/'experiments/v2090_svg_persistent_counter_fixture/native_worker.py',name)
  for name in ['CONFIG.json','NATIVE_DEPENDENCIES.json']:assert sha(SOURCE/name)==sha(P/name)
  # Escrow simulation charges both online and recipe reconstruction against the
  # existing25M subset cap; no new numerical work is performed.
  escrow=load('SVG_original_rebuild_escrow',R/'experiments/v1907_dwa_reconstruction_contract/escrow.py').WorkEscrow(25000000);online=0
  for i in range(500):online+=4415;escrow.before_online(online,0);escrow.reserve(str(i),4415,online)
  for i in range(500):escrow.begin(str(i),online);escrow.before_rebuild(online,4415);online+=4415;escrow.finish(online)
  assert online==4415000 and not escrow.holds
  reject('shared_workcap',lambda:escrow.before_online(online,25000000))
  from reserved_census import admission
  reserve=admission()
  for name in ['pilot_entry.py','run_phase.py']:
   p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/name)],env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'NOT_ADMITTED'in p.stderr
  ros=load('SVG_real_readonly_pre_admission_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);idx=cmd.index('--bind');cmd[idx]='--ro-bind';p=subprocess.run(['taskset','-c','7',*cmd],env=ros.environment(),capture_output=True,timeout=15);assert p.returncode!=0 and b'PILOT_ADMISSION.json'in p.stderr
  for folder in [C,R/'experiments/v2096_svg_first_formal_dispatch']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     pins[str(p.relative_to(R))]=sha(p)
  result.update(passed=True,negative_cases=negatives,actual_client_three_frame_readonly_namespace=True,clock_ticks=[0,5,2205],all_nonreply_log_bytes_retained=True,compact_query_audit_on_two_closed_actual_records=True,not_a_new_old_component_safety_audit=True,original_native_calls_and_parameters_exact=True,original_response_all_gates_byte_exact=True,locked_tasks=12,workcap_online_and_rebuild_shared=True,reservation=reserve,source_pins=pins,software_fixture_bytes_charged=sum(charges))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result['closed']=True;put(out/'RESULT.json',result);put(SOURCE/'SOFTWARE_CHECK_PROOF.json',result)
 print(json.dumps({k:result.get(k)for k in ['passed','first_error','models','formal_claims']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(run())
