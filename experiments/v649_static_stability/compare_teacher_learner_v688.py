"""Zero-integration paired behavior comparison and trained-model provenance audit."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v688_dynamic_distance_curriculum';src=repo/'experiments/v688_dynamic_distance_curriculum';sys.path.insert(0,str(src))
from learned_proposer import Proposer
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['teacher6m','learned6m_train_task'];z={};model=Proposer(root/'training_6m/proposer.json');mean=model.mean;std=model.std
for name in names:
 pair=root/name/'paired';cell=pair/'geometry_memory';trace=read(cell/'trace.json');ad=lines(cell/'model_admission.jsonl');samples=lines(cell/'proposal_learning_samples.jsonl');dist=np.r_[6.,[x['goal_distance_m']for x in trace]];groups={}
 for a in ad:
  group='OBSERVATION'if a.get('observation_initialization')else'REVERSE'if a['active_gear']==-1 else'FORWARD'
  groups.setdefault(group,{'steps':0,'net_goal_progress_m':0.});groups[group]['steps']+=1;groups[group]['net_goal_progress_m']+=float(dist[a['step']]-dist[a['step']+1])
 path=np.asarray([[-3.,-2.],*[x['pose'][:2]for x in trace]]);plans=[]
 for file in sorted(cell.glob('planning_*.json')):
  x=read(file);pp=np.asarray(x['path']);plans.append({'step':x['step'],'min_route_y':float(pp[:,1].min()),'max_route_y':float(pp[:,1].max()),'reverse_poses':int(np.sum(pp[:,3]==-1))})
 xx=np.asarray([s['features']for s in samples]);features=np.abs((xx-mean)/std)
 z[name]={'groups':groups,'executed_xy_path_length_m':float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()),'first_learned_selected_step':next((s['step']for s in samples if s['selected_role']=='LEARNED'),None),'learned_selected_steps':sum(s['selected_role']=='LEARNED'for s in samples),'plans':plans,'features_outside_5std':int(np.any(features>5,axis=1).sum()),'maximum_standardized_feature':float(features.max())}
execution=[lines(root/n/'paired/geometry_memory/v648_execution.jsonl')for n in names]
for k in ['ctrl','qpos_full','qvel_full']:z['first_difference_'+k]=next((i for i,(a,b)in enumerate(zip(*execution))if np.max(abs(np.asarray(a[k])-b[k]))>1e-12),None)
a,b=[read(root/n/'paired/geometry_memory/result.json')for n in names]
z['same_normalized_initial_state']=a['normalized_initial_state_hash']==b['normalized_initial_state_hash'];z['same_scene_model_bytes']=sha(root/names[0]/'paired/scene_model.mjb')==sha(root/names[1]/'paired/scene_model.mjb')==sha(repo/'runs/v686_dynamic_open_curriculum/open01/paired/scene_model.mjb')
teacherfile=root/'teacher6m/paired/geometry_memory/proposal_learning_samples.jsonl';samples=lines(teacherfile);xx=np.asarray([s['features']for s in samples]);yy=np.asarray([s['target']for s in samples])/[.52,.52,20.,20.];prediction=np.asarray([model.predict(x)for x in xx])/[.52,.52,20.,20.];report=read(root/'training_6m/TRAINING.json');mse=float(np.mean((prediction-yy)**2))
trainchecks={'weight_hash_matches':report['model_sha256']==model.sha256==b['proposal_model_sha256'],'teacher_data_hash_matches':sha(teacherfile)==report['source_sample_sha256']==model.parameters['teacher_sample_sha256'],'gradient_count_registered':report['gradient_updates']==model.parameters['gradient_updates']==512,'same_sample_count':len(samples)==report['samples']==852,'finite_twelve_dimensional_inputs':xx.shape==(852,12)and np.isfinite(xx).all(),'actual_training_mse_matches':abs(mse-report['final_mse'])<=1e-12,'all_source_freezes_unchanged':all(sha(src/n)==h for n,h in read(root/'curriculum01/SOURCE_FREEZE.json').items())}
z['training_provenance_audit']={'passed':all(trainchecks.values()),'checks':{k:bool(v)for k,v in trainchecks.items()},'recomputed_training_mse':mse,'gradient_replay_updates':0}
z.update(robot_integrations=0,interpretation='Adding learned proposals plus fixed ranking bonus changes the closed-loop route and controls. No unique loss cause, covariate-shift proof, or superiority claim; no feature exceeded5std does not prove joint-distribution coverage.')
(root/'TEACHER_LEARNER_COMPARISON.json').write_text(json.dumps(z,indent=2)+'\n');assert z['training_provenance_audit']['passed']and z['same_normalized_initial_state']and z['same_scene_model_bytes'];print(json.dumps({'training_audit':z['training_provenance_audit'],'same_initial':z['same_normalized_initial_state'],'same_model':z['same_scene_model_bytes'],'first_control_difference':z['first_difference_ctrl'],'integrations':0},indent=2))
