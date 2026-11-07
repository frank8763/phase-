"""Pre-freeze saved interfaces: no model init, no physical/predict/replay."""
import ast,hashlib,importlib.util,json,pathlib,subprocess,sys
from types import SimpleNamespace
import numpy as np
repo=pathlib.Path(__file__).resolve().parents[2];own=repo/'experiments/v809_time_reference_global';sys.path.insert(0,str(own));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from timed_reference import attach
from independent_time_reference import field as independent_field,values,revalidation_queries
from route_commitment import route_check
from planner import search
read=lambda p:json.loads(p.read_text());out=repo/'runs/v809_preparation';out.mkdir(exist_ok=False)
for p in own.glob('*.py'):ast.parse(p.read_text())
prior=repo/'runs/v807_reactive_single_task_continuation/main_slot01/paired';protocol=read(prior/'STATIC_PROTOCOL.json');cell=prior/'geometry_memory';states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};trace=read(cell/'trace.json')
spec=importlib.util.spec_from_file_location('v809_preparation_footprint',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
r=read(cell/'planning_0000.json');world=r['causal_input'];f=build(F,world);f.base_heuristic=F.base._heuristic_grid;attach(f,states[0]);path,stats=search(f,r['pose'],protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
if stats['status']!='GLOBAL_GOAL_PATH':
 preferred,pstats=path,stats;path,stats=search(f,r['pose'],protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
 if path is None:path,stats=preferred,pstats
expected=np.asarray(r['stats']['forward_curve']['original_path']);assert np.array_equal(path,expected),'UNSEEN_INITIAL_SPATIAL_PATH_CHANGED'
rows=list(map(json.loads,(cell/'route_revalidation.jsonl').read_text().splitlines()));cases=[rows[i]for i in np.linspace(0,len(rows)-1,10).astype(int)];errors=[];query_errors=[]
for row in cases:
 step=row['step'];state=states[step];ff=independent_field(protocol,state);ff.pose_values=lambda poses,ff=ff:__import__('exact_footprint').pose_values(ff,poses);attach(ff,state);p=np.asarray(row['reference_path']);current=np.asarray(trace[step-1]['pose'])
 actual=route_check(ff,p,row['index'],current,trace[:step],step,row['last_plan'])
 if state['center']is not None:
  qp,qt=revalidation_queries(p,row['index'],current);query_errors.append(float(max(np.max(abs(qp-actual['time_reference_query_poses'])),np.max(abs(qt-actual['time_reference_query_times_s'])))));minimum=float(values(independent_field(protocol,state),state,qp,qt).min())
 else:minimum=float(ff.pose_values(p[row['index']:min(len(p),row['index']+26),:3]).min())
 errors.append(abs(minimum-actual['current_route_minimum_m']))
assert max(errors)<=1e-10 and max(query_errors,default=0)<=1e-10
# Exercise the EXACT new three-task cardinality audit on old immutable t0 packets.
refs=read(repo/'runs/v802_exact_rejection_global/development01/PREFLIGHTS.json');(out/'PREFLIGHTS.json').write_text(json.dumps(refs,indent=2)+'\n')
r=subprocess.run([sys.executable,'-B',str(own/'audit_field_preflight.py'),str(out)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60);(out/'preflight_adapter.console').write_text(r.stdout);assert r.returncode==0 and read(out/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS'
mods=['motion_tracker.py','serial_predictor.py','geometry_predictor.py','dynamic_scene.py','scene_sensors.py','discovery_brake.py','reserved_recovery.py','joint_admission.py','recovery_supervisor.py','replay_native_audit.py']
old=repo/'experiments/v807_reactive_single_task_continuation';assert all((old/n).read_bytes()==(own/n).read_bytes()for n in mods)
assert (own/'planner.py').read_bytes()==(repo/'experiments/v808_timed_reference_qualification/planner.py').read_bytes()
result=dict(status='PHYSICAL_INTERFACE_SAVED_PREPARATION_PASS',unseen_initial_original_astar_path_exact=True,ten_saved_revalidation_queries_error=max(query_errors,default=0.),maximum_independent_geometry_error=max(errors),three_task_noise_audit_on_immutable_prior_packets='PASS',unchanged_scientific_modules=mods,qualified_planner_exact=True,new_models=0,integrations=0)
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

