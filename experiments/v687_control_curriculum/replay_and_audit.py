"""Independent complete native replay and command audit of the no-actor task."""
import os,sys,json,math,gzip,hashlib,argparse,signal
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
src=Path(__file__).resolve().parent;repo=src.parents[1];core=repo/'experiments/v680_dynamic_later_stop_reserve'
sys.path.insert(1,str(core));sys.path.insert(2,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from contact_contract import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--window',required=True);a=p.parse_args();root=Path(a.paired);window=Path(a.window);cell=root/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('C0_AUDIT_45S')));signal.alarm(45)
r=read(cell/'result.json');protocol=read(root/'STATIC_PROTOCOL.json');course=read(root/'C0_PROTOCOL.json');execution=lines(cell/'v648_execution.jsonl');ad=lines(cell/'model_admission.jsonl');decisions=lines(cell/'control_decisions.jsonl');contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');nom={x['step']:x for x in decisions if x['stage']=='NOMINAL'}
m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=protocol['start_qvel'];mujoco.mj_forward(m,d)
catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml');geometry=SelfGeometry(m,mujoco);bounds=np.asarray(protocol['footprint_bounds']);ids=contract['ids'];rate=np.asarray(contract['rate']);limits=np.asarray(contract['limits'])
minimum=margin=float('inf');steps=contacts=unknown=0;errq=errv=0.;native=[];status='FAILED';error=None
try:
 for row in execution:
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1
   b=geometry.actual(m,d);q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
   field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=[],circles=[],sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
   minimum=min(minimum,float(pose_values(field,[[q[0],q[1],yaw]])[0]));margin=min(margin,float(containment_margin(b,bounds)))
   for c in d.contact:
    kind=catalog.classify(c,steps,row['step'],float(d.time))['contact_type'];contacts+=kind in ['robot_obstacle_contact','robot_obstacle_penetration'];unknown+=kind=='unknown_contact'
  errq=max(errq,float(np.max(abs(d.qpos-row['qpos_full']))));errv=max(errv,float(np.max(abs(d.qvel-row['qvel_full']))));assert max(errq,errv)<=1e-8
 with gzip.open(cell/'native.jsonl.gz','rt')as stream:native=[json.loads(s)for s in stream]
 commands=np.asarray([x['ctrl']for x in execution]);diff=np.diff(np.vstack((np.zeros(4),commands[:,ids])),axis=0);selection_errors=[];raw_errors=[]
 certificates={}
 for file in(cell/'recovery_contracts').glob('*.gz'):
  with gzip.open(file,'rt')as f:c=json.load(f)
  certificates[c['created_step']]=c
 for x in ad:
  step=x['step']
  if x['status']=='MODEL_SAFE_COMMAND':
   candidates=sorted([c for c in nom[step]['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True);seen=set();unique=[]
   for c in candidates:
    k=tuple(c['first_command'])
    if k not in seen:seen.add(k);unique.append(c)
   rank=x['joint_admission_distinct_command_rank'];chosen=unique[rank];expected=np.asarray(chosen['first_command'])
   tests=[t for t in decisions if t['step']==step and t['stage']=='BACKUP_APPEND']
   if not(rank<3 and len(tests)==rank+1 and tests[-1]['detail']['status']=='APPENDABLE_BACKUP_FOUND' and chosen['minimum_clearance_m']>=.155 and chosen['self_domain_margin_m']>=.002 and chosen['terminal_speed_m_s']<=.025):selection_errors.append(step)
  else:
   assert x['status']=='RETAINED_REVERSE_BRAKE_CONTRACT';c=certificates[x['retained_from_step']];expected=np.asarray(c['controls'][x['contract_native_cursor']])
  if np.max(abs(commands[step,ids]-expected))>1e-12:raw_errors.append(step)
 h=hashlib.sha256();nr=ob=un=0
 with gzip.open(cell/'contacts.jsonl.gz','rb')as f:
  for raw in f:
   h.update(raw);c=json.loads(raw);nr+=1;ob+=c['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration'];un+=c['contact_type']=='unknown_contact'
 freeze=read(window/'SOURCE_FREEZE.json');reference=np.asarray(course['reference']);trace=read(cell/'trace.json');tracking=[float(np.min(np.linalg.norm(reference[:,:2]-t['pose'][:2],axis=1)))for t in trace]
 old=mujoco.MjModel.from_binary_path(str(repo/'runs/v686_dynamic_open_curriculum/open01/paired/scene_model.mjb'))
 vehicle_checks={k:bool(np.array_equal(getattr(m,k),getattr(old,k)))for k in ['jnt_range','jnt_limited','dof_damping','dof_armature','actuator_ctrlrange','actuator_gainprm','actuator_biasprm','actuator_forcerange']}
 for key in ['body_mass','body_inertia','body_ipos','body_iquat']:
  vehicle_checks[key]=bool(np.array_equal(getattr(m,key),getattr(old,key)[:m.nbody]))
 disabled=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,n)for n in course['removed_static_geometries']]
 checks={'complete_counts':len(execution)==len(ad)==r['public_steps']and steps==len(native)==r['physics_steps']==8*len(execution),'all_full_state_matches':max(errq,errv)<=1e-8,'native_clearance':minimum>=.15 and abs(minimum-r['minimum_native_clearance_m'])<=1e-8,'complete_self_geometry':margin>=0 and abs(margin-r['minimum_actual_self_domain_margin_m'])<=1e-8,'zero_contacts':contacts==unknown==ob==un==0,'contact_digest':h.hexdigest()==r['contacts']['contact_log_content_sha256']and nr==r['contacts']['all_contact_records'],'source_frozen':all(sha(repo/k)==v for k,v in freeze.items()),'model_hash':sha(root/'scene_model.mjb')==protocol['full_model_sha256'],'no_actor':m.nmocap==0 and course['actor_count']==0 and len(disabled)==21 and np.all(m.geom_contype[disabled]==0)and np.all(m.geom_conaffinity[disabled]==0),'unchanged_vehicle':all(vehicle_checks.values()),'all_controls_legal_and_slew':np.all(commands[:,ids]>=limits[:,0]-1e-12)and np.all(commands[:,ids]<=limits[:,1]+1e-12)and np.all(abs(diff)<=rate+1e-12),'actual_native_controls':all(np.max(abs(np.asarray(x['actual_ctrl'])-x['expected_ctrl']))<=1e-12 for x in native),'raw_admitted_commands':not raw_errors,'ordinary_selection':not selection_errors,'all_predicted_first_full_states':len(read(cell/'prediction_state_matches.json'))==len(execution)and all(x['maximum_full_state_and_ctrl_error']<=1e-8 for x in read(cell/'prediction_state_matches.json')),'no_external_root_mutation':r['root_mutations_outside_mjstep']==0 and r['static_obstacle_pose_unchanged'],'strict_goal':r['strict_safe_arrival']==bool(r['outcome']=='GOAL'and r['goal_distance_m']<=.45)}
 status='ALL_C0_AUDITS_PASS'if all(checks.values())else'FAIL'
except BaseException as e:error={'type':type(e).__name__,'message':str(e)};checks={}
finally:
 signal.alarm(0)
 out={'status':status,'checks':{k:bool(v)for k,v in checks.items()},'error':error,'replay_native_steps':steps,'maximum_qpos_error':errq,'maximum_qvel_error':errv,'minimum_native_clearance_m':minimum if steps else None,'minimum_self_margin_m':margin if steps else None,'median_nearest_route_distance_m':float(np.median(tracking))if 'tracking'in globals()else None,'maximum_nearest_route_distance_m':max(tracking)if 'tracking'in globals()else None,'strict_arrival':r['strict_safe_arrival'],'scope':'C0 fixed-route ability test, no actor or dynamic navigation claim'}
 (root/'C0_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if status!='ALL_C0_AUDITS_PASS':sys.exit(1)
