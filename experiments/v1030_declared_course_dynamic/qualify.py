"""New actual entry checks without vehicle models; old native owner unchanged."""
import ast,copy,hashlib,importlib.abc,importlib.util,json,subprocess,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1030_declared_course_dynamic';sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import worker
assert 'v1030_declared_course_dynamic'in str(worker.C)
factory=worker.load('actual_new_course_factory',C/'physical.py');assert callable(factory.create_vehicle)
from certificate import audit
preview=json.loads((R/'runs/v1029_declared_course_source/PREVIEW.json').read_text());assert preview['plan']['passed'];proof=audit(preview['plan'],preview['stopped_packet'],preview['source'],preview['setup'],preview['scene']['goal_xy']);assert proof['passed'],proof
old=R/'experiments/v1024_full_route_execution';assert(C/'owner.py').read_bytes()==(old/'owner.py').read_bytes()
checks=dict(full_new_course_causal_source_reconstruction=proof['passed'],original_actual_full_route_platform_passed=json.loads((R/'runs/v858_nav2_verified/v1024/static_we/FINAL_INDEPENDENT_AUDIT.json').read_text())['passed'],exact_periodic_clipping=json.loads((R/'runs/v1029_declared_course_source/CLIPPING_EQUIVALENCE.json').read_text())['passed'],actual_worker_and_factory_import_zero_models=True,old_native_scheduler_byte_identical=True)
# Exercise the exact production expression and run_phase pause entry. This
# catches the earlier Path+str error before any launch authorization exists.
tree=ast.parse((C/'campaign.py').read_text());expr=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='Popen');tasks=json.loads((C/'TASKS.json').read_text());task=tasks[0];rp=O/'not_authorized.json';args=eval(compile(ast.Expression(expr.args[0]),str(C/'campaign.py'),'eval'),dict(str=str,R=R,C=C,task=task,rp=rp))
assert Path(args[2]).is_file();assert(R/'REVIEW_PENDING').exists();p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr;checks['exact_production_command_and_pre_model_guard']=True
campaign=worker.load('v1030_exact_campaign_policy',C/'campaign.py');select_next=campaign.select_next
assert select_next([],tasks[0])and not select_next([dict(passed=False)],tasks[1])and select_next([dict(passed=True)],tasks[1]);checks['first_failure_stop_success_only_repeat']=True
scene=preview['scene'];anchor=np.asarray(scene['actor_anchor_xy']);known=preview['setup']['known'];clearance=5-float(abs(anchor).max())
for x,y,hx,hy in known['known_rectangles']:
 offset=abs(anchor-[x,y])-[hx,hy];clearance=min(clearance,float(np.linalg.norm(np.maximum(offset,0)))if offset.max()>0 else float(offset.max()))
for x,y,r in known['known_circles']:clearance=min(clearance,float(np.linalg.norm(anchor-[x,y]))-r)
checks['fixed_scene_sweep_known_clearance']=clearance-.35>=.55
checks['public_three_metre_start_exclusion']=np.linalg.norm(anchor-scene['start_xy'])-.35>3.
checks['all_static_geometry_unmodified_by_design']=len(known['known_rectangles'])+len(known['known_circles'])==19
for p in list(C.glob('*.py'))+list((R/'experiments/v1029_declared_course_source').glob('*.py')):ast.parse(p.read_text(),filename=str(p))
# Truth coverage is an OFFLINE evaluator check only. It is not planner input.
from geometry_model import ref
source=preview['source']['periodic'];bounds=ref._old.cycle_upper(source)+1e-6;normals=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)];t=preview['stopped_packet']['sim_time']+np.arange(len(preview['plan']['state_path']))*.01;truth=anchor+np.sin(.32*t+scene['actor_phase_rad'])[:,None]*.25*np.asarray(scene['actor_axis_xy']);checks['offline_entire_predicted_time_actor_coverage']=bool((truth@normals.T<=bounds+1e-8).all())
checks={k:bool(v)for k,v in checks.items()}
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,new_course_only=True,original_dynamic_acceptance_passed=False,minimum_swept_actor_known_clearance_m=clearance-.35,preview_full_input_audit=proof)
(O/'FINAL_SOURCE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='preview_full_input_audit'}));assert result['passed']
