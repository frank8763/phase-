"""Actual saved-scene red/green loop, production entry imports and rejection gates."""
import sys,json,ast,types,importlib.abc,importlib.util,copy,os,hashlib,shutil
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1089_route_scene_contract'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import worker
w=worker.load_worker();import contract
def mod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
a=mod('qualified_new_audit',C/'audit.py');a.configure();compile(a.patched_source(),str(a.ORIGINAL),'exec')
for p in C.glob('*.py'):compile(p.read_text(),str(p),'exec')
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==55
rows=[]
for task in tasks:
 t,root,cfg,out=w.entry(str(O/(task['task_id']+'.json')));assert t==task and not out.exists();meta=json.loads((O/(t['case_id']+'_T0_METADATA.json')).read_text());assert meta['packet']['body'][:2]==t['start_xy']and abs(meta['packet']['body'][2]-t['start_yaw'])<=1e-8;assert json.loads((O/(t['case_id']+'_STATIC_SOURCE.json')).read_text())['passed'];rows.append(t['task_id'])
f=w.factory(O);owner=w.pipeline.configure(O);assert callable(f.create_vehicle)and callable(f.replay)and callable(owner.navigate);assert Path(__import__('planner').library()._name).is_file()
reference=json.loads((R/'runs/v1088_remaining_routes/main_west_east.json').read_text());ph=R/'runs/v858_nav2_verified/v1088/main_west_east/physics';saved=contract.verify_saved(ph,reference,require_live=False);assert saved['passed']
# The former exact worker gate really rejects this saved, declared scene.
assert json.loads((ph/'SETUP.json').read_text())['model_sha256']!=contract.SPEC['baseline_NS_sha']
cases=O/'rejection_cases';cases.mkdir(exist_ok=True)
def fixture(label):
 root=cases/label;root.mkdir(exist_ok=False)
 for name in ['SETUP.json','MODEL_BUILD_CONTRACT.json','PATCHED_ASSEMBLY.xml']:(root/name).write_bytes((ph/name).read_bytes())
 os.link(ph/'scene_model.mjb',root/'scene_model.mjb');return root
def reject(label,mutate):
 root=fixture(label);mutate(root)
 try:contract.verify_saved(root,reference,require_live=False);return False
 except AssertionError:return True
def json_change(root,name,fn):
 p=root/name;x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x))
negative={}
negative['wrong_model_sha']=reject('wrong_model_sha',lambda p:json_change(p,'SETUP.json',lambda x:x.update(model_sha256='0'*64)))
negative['wrong_actor_anchor']=reject('wrong_actor_anchor',lambda p:json_change(p,'SETUP.json',lambda x:x['actor'].update(anchor_xy=[0.,0.])))
negative['wrong_phase']=reject('wrong_phase',lambda p:json_change(p,'SETUP.json',lambda x:x['actor'].update(phase_rad=0.)))
negative['wrong_vehicle_array']=reject('wrong_vehicle_array',lambda p:json_change(p,'MODEL_BUILD_CONTRACT.json',lambda x:x['preserved_arrays'][0].update(sha256='0'*64)))
negative['wrong_actuator']=reject('wrong_actuator',lambda p:json_change(p,'MODEL_BUILD_CONTRACT.json',lambda x:x['interface']['drivers'][0].update(new_range=[-1,1])))
for label,old,new in [('actor_size','size=".10 .20"','size=".11 .20"'),('mocap','mocap="true"','mocap="false"'),('static_map','name="real_rect_obs_6"','name="changed_static_obstacle"')]:
 text=(ph/'PATCHED_ASSEMBLY.xml').read_text()
 if old not in text:raise AssertionError('MUTATION_ANCHOR_NOT_FOUND '+label)
 def mutate(p,old=old,new=new):
  q=p/'PATCHED_ASSEMBLY.xml';s=q.read_text();assert old in s;q.write_text(s.replace(old,new,1))
 negative[label]=reject(label,mutate)
assert all(negative.values())
# Archive seam includes the actual non-NS MJB and verifies exact reassembly/member SHA.
arc=mod('archive_gate',R/'experiments/v1065_preflight_metadata_continuation/archive.py');record,inventory=arc.package(R,[ph/'scene_model.mjb',ph/'SETUP.json',ph/'MODEL_BUILD_CONTRACT.json',ph/'PATCHED_ASSEMBLY.xml'],O/'archive_qualification','actual-WE-model-positive');assert any(x['path'].endswith('scene_model.mjb')for x in inventory)
# Worker's implementation differs only in scene verification and boot authority.
assert worker.OLD not in worker.patched_source()and worker.NEW in worker.patched_source()
assert 'verify_saved(ph,task)'in a.patched_source()
pool=json.loads((C/'CONFIRMATION_POOL.json').read_text());assert hashlib.sha256((C/'CONFIRMATION_POOL.json').read_bytes()).hexdigest()==hashlib.sha256((R/'experiments/v1062_three_route_night/CONFIRMATION_POOL.json').read_bytes()).hexdigest()
assert len(pool)==24 and len({x['seed']for x in pool})==24
assert all(sum(x['case_id']==case for x in pool)==8 for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST'])
assert sum(x['initial_axis_motion_direction']=='POSITIVE_AXIS'for x in pool)==12
assert [t['slot']for t in tasks[-3:]]==[1,9,17]
for t in tasks[28:]:
 slot=next(p for p in pool if p['slot']==t['slot']);assert t['seed']==slot['seed']and t['phase']==slot['phase']and t['case_id']==slot['case_id']
assert not any((R/'runs/v858_nav2_verified'/v/('confirm_main_%02d'%i)).exists()for v in ['v1062','v1063','v1064','v1065','v1067']for i in range(1,25)),'POOL_PRIOR_USE_REQUIRES_REVIEW'
w.install_history_guard(Path(tasks[0]['output']))
try:(R/'runs/v858_nav2_verified/v1085_entry/main_fresh_ns/physics/NATIVE_TRACE.npz').open('rb');rejected=False
except AssertionError:rejected=True
assert rejected
answer=dict(passed=True,models=0,integrations=0,saved_actual_WE_scene_accepted=saved,old_NS_hash_error_reproduced=True,negative_cases=negative,real_isolated_production_entries=len(rows),all_four_components_worker_t0_audit_archive_compile=True,actual_nonNS_scene_archive_source_sha_verified=True,fixed_original_pool_bytes_retained=True,pool_not_previously_executed=True,confirmation_preflights=24,confirmation_mains=24,fixed_repeats=[1,9,17],history_read_rejected=True,scientific_navigation_changes=0)
(O/'QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
