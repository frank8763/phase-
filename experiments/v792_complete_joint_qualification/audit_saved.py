"""Independent saved-array admission/account audit. No MuJoCo initialization."""
import gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v791_coherent_global_reference';sys.path.insert(0,str(source))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V792_SAVED_INITIALIZATION_OR_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
import mujoco.rollout
mujoco.rollout.rollout=forbidden
from exact_footprint import pose_values
from motion_tracker import install_time_gate
from self_geometry import containment_margin
from motion_evaluator import check_forecast
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v792_complete_joint_saved_audit';root.mkdir(exist_ok=False);raw=repo/'runs/v792_complete_joint_qualification';pair=repo/'runs/v791_coherent_global_reference/main_slot01/paired';cell=pair/'geometry_memory';begun=time.time();deadline=min(begun+300,read(repo/'RPCCR_GLOBAL_METHOD_REVIEW_AUTHORIZATION_20261104.json')['absolute_deadline_unix']);window=dict(started_unix=begun,absolute_deadline_unix=deadline,limit_s=deadline-begun,round_closed=False,new_initializations=0,new_integrations=0)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V792_SAVED_300S_ABSOLUTE_STOP')));signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-time.time()));os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});dump('ROUND_WINDOW.json',window)
records=[];status='RUNNING'
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def sequence(target,last,n,brake):
 command=np.asarray(last).copy();result=[]
 for t in range(0,n,8):
  active=np.asarray(target).copy()
  if t>=brake:active[2:]=0.
  command=np.clip(np.clip(active,limits[:,0],limits[:,1]),command-rate,command+rate);result.extend([command.copy()for _ in range(min(8,n-t))])
 return np.asarray(result)
def eq(a,b):
 if isinstance(a,dict):assert isinstance(b,dict)and set(a)==set(b);return max([eq(a[k],b[k])for k in a]or[0.])
 if isinstance(a,list):assert isinstance(b,list)and len(a)==len(b);return max([eq(x,y)for x,y in zip(a,b)]or[0.])
 if type(a)in(int,float)and type(b)in(int,float):return abs(a-b)
 assert a==b;return 0.
try:
 assert(repo/'REVIEW_PENDING').exists();freeze=read(repo/'experiments/v792_complete_joint_qualification/INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 result=read(raw/'RESULT.json');completion=read(raw/'COMPLETION.json');assert result['status']==completion['status']=='FIXED_JOINT_INPUT_QUALIFICATION_COMPLETE'and completion['round_closed']
 plan=read(repo/'experiments/v792_complete_joint_qualification/COMMAND_CLASSES.json');protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);ids=contract['ids'];bounds=np.asarray(protocol['footprint_bounds'])
 static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()];oldrows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];replay=np.load(raw/'ORIGINAL_1984_NATIVE_REPLAY.npz');assert len(replay['qpos'])==1984
 for i,row in enumerate(oldrows[:248]):
  t=8*i+7;assert np.max(abs(replay['qpos'][t]-row['qpos_full']))<=1e-8 and np.max(abs(replay['qvel'][t]-row['qvel_full']))<=1e-8 and np.max(abs(replay['mocap'][t]-row['mocap_pos']))<=1e-8
  assert np.array_equal(replay['ctrl'][8*i:8*i+8],np.repeat([row['ctrl']],8,axis=0))
 assert replay['safety'][:,0].min()>=.15 and replay['safety'][:,1].min()>=0
 private=validation=tailcount=0;commands=0;missed={}
 for entry in plan['checkpoints']:
  step=entry['step'];state={k:v for k,v in beliefs[step].items()if k!='step'};field=SimpleNamespace(**static);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);coverage=check_forecast(config,state);assert coverage['passed']and eq(coverage,read(raw/('COVERAGE_%03d.json'%step)))<=1e-12
  old=next(x for x in decisions if x['step']==step and x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY');unique=[];seen=set()
  for candidate in sorted([x for x in old['candidates']if x['reason']is None],key=lambda x:x['score'],reverse=True):
   key=tuple(candidate['first_command'])
   if key not in seen:seen.add(key);unique.append(candidate)
  assert unique==entry['commands']and len(unique)=={248:13}[step]
  missed[str(step)]=0;last=replay['ctrl'][8*step-1,ids]
  for rank,candidate in enumerate(unique):
   commands+=1;r=next(x for x in result['records']if x['step']==step and x['rank']==rank);label=r['label'];assert label=='S%03d_R%02d'%(step,rank)and r['ordinary_candidate']==candidate
   ordinary=np.load(raw/(label+'_ORDINARY.npz'));command=np.asarray(candidate['first_command']);controls=sequence(candidate['target_command'],last,240,80);assert np.array_equal(controls,ordinary['controls'])and np.array_equal(command,controls[0]);assert np.max(abs(poses(ordinary['qpos'])-ordinary['poses']))<=1e-12
   minimum=float(field.trajectory_values(ordinary['poses'],.01).min());margin=float(containment_margin(ordinary['self_bounds'],bounds).min());speed=float(np.linalg.norm(ordinary['qvel'][-1,:2]));assert minimum>=.155 and margin>=.002 and speed<=.025
   assert max(abs(minimum-candidate['minimum_clearance_m']),abs(margin-candidate['self_domain_margin_m']),abs(speed-candidate['terminal_speed_m_s']))<=1e-8
   initialq=replay['qpos'][8*step-1];progress=float(np.linalg.norm(initialq[:2]-protocol['goal_xy'])-np.linalg.norm(ordinary['qpos'][-1,:2]-protocol['goal_xy']));assert abs(progress-r['ordinary_goal_progress_m'])<=1e-10 and r['return_goal_progress_gate_passed']==(progress>=.02)
   prefix=np.load(raw/(label+'_PREFIX.npz'));assert len(prefix['qpos'])==8 and np.array_equal(prefix['controls'],np.repeat([command],8,axis=0));prefix_margin=float(containment_margin(prefix['self_bounds'],bounds).min());assert abs(prefix_margin-r['detail']['prefix_self_domain_margin_m'])<=1e-10
   choices=[(None,0.)]+[(s,w)for s in[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for w in[-12.,-8.,-4.]]+[(s,4.)for s in[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]];best=None;safecount=0
   for i,(tail,tfile)in enumerate(zip(r['detail']['candidates'],r['tail_files'])):
    tailcount+=1;assert i==tfile['index'];data=np.load(raw/(label+'_TAIL_%02d.npz'%i));s,w=choices[i];kind='BRAKE_ONLY'if s is None else'FORWARD_BRAKE'if w>0 else'REVERSE_BRAKE';brake=240 if w>0 else 160
    if s is None:target=np.r_[command[:2],0.,0.]
    elif s==0:target=np.array([0.,0.,w,w])
    else:
     radius=.60/math.tan(abs(s));inner=math.atan2(.60,radius-.27);outer=math.atan2(.60,radius+.27);target=np.array([inner,outer,w,w]if s>0 else[-outer,-inner,w,w])
    assert np.array_equal(target,np.asarray(tail['target_command']))and np.array_equal(target,tfile['target_command'])and tail['kind']==kind and tail['library']==('ORIGINAL'if i<16 else'FORWARD_EXTENSION')and tail['brake_after_native_ticks']==tfile['brake_after']==brake
    assert np.array_equal(data['controls'],sequence(target,command,320,brake))and np.max(abs(poses(data['qpos'])-data['poses']))<=1e-12
    trajectory=np.vstack([poses(prefix['qpos']),data['poses']]);values=field.trajectory_values(trajectory,.01);minimum=float(values.min());margin=min(prefix_margin,float(containment_margin(data['self_bounds'],bounds).min()));speed=float(np.linalg.norm(data['qvel'][-1,:2]));yaw=poses(prefix['qpos'])[-1,2];signed=float((data['qpos'][-1,:2]-prefix['qpos'][-1,:2])@np.array([np.cos(yaw),np.sin(yaw)]))
    reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'INSUFFICIENT_REVERSE'if kind=='REVERSE_BRAKE'and signed>-.02 else'INSUFFICIENT_FORWARD'if kind=='FORWARD_BRAKE'and signed<.02 else None
    from unseen_prior import clearance as unknown_clearance
    static_min=float(pose_values(SimpleNamespace(**static),trajectory).min());unknown_min=float(unknown_clearance(field,trajectory,state,np.arange(1,329)*.01).min());assert max(abs(static_min-tfile['static_minimum_m']),abs(unknown_min-tfile['unknown_future_minimum_m']),abs(min(static_min,unknown_min)-minimum))<=1e-8
    assert reason==tail['reason']and tail['minimum_clearance_native_tick']==int(np.argmin(values))+1
    assert max(abs(minimum-tail['minimum_clearance_m']),abs(margin-tail['self_domain_margin_m']),abs(speed-tail['terminal_speed_m_s']),abs(signed-tail['signed_displacement_m']))<=1e-8
    if reason is None:
     safecount+=1;score=minimum+.1*(signed if kind=='FORWARD_BRAKE'else-signed)-.02*abs(s or 0.)
     if best is None or score>best[0]:best=(score,i)
     if i==0:assert len(r['detail']['candidates'])==1
   assert len(r['detail']['candidates'])==len(r['tail_files'])and((best is None and len(r['tail_files'])==21)or best is not None)
   private+=240+8+len(r['tail_files'])*320;assert r['private_steps']==240+8+len(r['tail_files'])*320
   if rank<3:
    oldappend=next(x['detail']for x in decisions if x['step']==step and x['stage']=='BACKUP_APPEND'and x['candidate_role']=='ORDINARY'and x['distinct_command_rank']==rank);assert eq(oldappend,r['detail'])<=1e-8 and r['append_summary']is None
   assert(r['append_summary']is None)==(best is None)and r['qualified_complete_return']==(best is not None and progress>=.02)
   if best is not None:
    idx=best[1];tail=np.load(raw/(label+'_TAIL_%02d.npz'%idx));actual=np.load(raw/(label+'_ACTUAL.npz'));assert r['validation_steps']==328 and r['selected_target']==r['tail_files'][idx]['target_command'];assert np.max(abs(actual['qpos']-np.vstack([prefix['qpos'],tail['qpos']])))<=1e-8 and np.max(abs(actual['qvel']-np.vstack([prefix['qvel'],tail['qvel']])))<=1e-8 and np.array_equal(actual['controls'],np.vstack([prefix['controls'],tail['controls']]))
    assert actual['safety'][:,0].min()>=.15 and actual['safety'][:,1].min()>=0;validation+=328;missed[str(step)]+=int(rank>=3 and progress>=.02)
   else:assert r['validation_steps']==0
   records.append(dict(step=step,rank=rank,tails=len(r['tail_files']),admissible=best is not None,goal_progress_gate=progress>=.02,qualified_complete_return=r['qualified_complete_return']));dump('PROGRESS.json',records)
 contactlines=0;bad=0
 with gzip.open(raw/'ACTUAL_CONTACTS.jsonl.gz','rt')as f:
  for line in f:
   packet=json.loads(line);contactlines+=1;bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in packet['contacts'])
 assert commands==13 and private==result['private_integrations']<=90584 and validation==result['scene_validation_integrations']<=4264 and contactlines==1984+validation and bad==0 and missed==result['missed_qualified_returns']
 assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 status='ALL_FIXED_JOINT_RETURN_EVIDENCE_VERIFIED';dump('RESULT.json',dict(status=status,commands=commands,tail_predictions=tailcount,records=records,original_replay_steps=1984,private_integrations=private,scene_validation_integrations=validation,missed_qualified_returns=missed,new_initializations=0,new_integrations=0,scope='Finite one saved state and original tail library only; not global impossibility or navigation success.'))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-begun);dump('ROUND_WINDOW.json',window)
