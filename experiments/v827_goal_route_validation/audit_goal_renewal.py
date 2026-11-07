"""Independent saved-data trigger, causal reference and pre-divergence audit."""
import argparse,gzip,importlib.util,json,math,os,sys
from pathlib import Path
import numpy as np
from exact_footprint import build
repo=Path(__file__).resolve().parents[2];ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);ap.add_argument('--anchor-original-ns',action='store_true');a=ap.parse_args();pair=a.pair;cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
rows=lines(cell/'goal_reference_renewal.jsonl')if(cell/'goal_reference_renewal.jsonl').exists()else[]
triggers=[r for r in rows if r['should_replan']]
if a.anchor_original_ns:assert rows and triggers and triggers[0]['step']==282,'FIRST_RENEWAL_NOT_ORIGINAL282'
protocol=read(pair/'STATIC_PROTOCOL.json');states={r['step']:r for r in lines(cell/'motion_estimate.jsonl')};executions=lines(cell/'v648_execution.jsonl');plans={int(p.stem.split('_')[-1]):read(p)for p in cell.glob('planning_*.json')}
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
checks=[]
for row in rows:
 step=row['step'];state=states[step];q=np.asarray(executions[step-1]['qpos_full']);pose=np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
 old=plans[row['last_plan']];assert old['stats']['status']=='SAFE_PROGRESS_PREFIX'
 world=dict(old['causal_route_input']);world['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']];world['circles']=protocol['known_circles'];world['start']=pose.tolist();field=build(F,world)
 field.free=field.clearance>=.15-field.config.resolution/math.sqrt(2);guide=F.base._heuristic_grid(field,np.asarray(protocol['goal_xy']));idx=field.indices([pose[:2]])[0];inside=bool(guide is not None and(idx>=0).all()and(idx<guide.shape).all());finite=bool(inside and np.isfinite(guide[tuple(idx)]))
 assert state['observed_this_frame']and state['center']is not None and step-row['last_plan']>=12 and row['goal_guide_finite']==finite and row['should_replan']==finite
 assert row['authorizes_control']is False and row['complete_328_gate_unchanged']is True and row['hidden_world_geometry_used']is False
 if finite:assert step in plans,'TRIGGER_WITHOUT_ACTUAL_REPLAN'
 checks.append(dict(step=step,passed=True,triggered=finite,new_plan_status=plans[step]['stats']['status']if finite else None))
native_error=None;native=0;errors={}
if a.anchor_original_ns:
 oldcell=repo/'runs/v821_norm_route_development/main_slot02/paired/geometry_memory';original=lines(oldcell/'v648_execution.jsonl');errors={k:float(np.max(abs(np.asarray([x[k]for x in executions[:282]])-np.asarray([x[k]for x in original[:282]]))))for k in['qpos_full','qvel_full','ctrl','mocap_pos']};assert all(v<=1e-8 for v in errors.values())
 native_error=0.;native=0
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(oldcell/'dynamic_native.jsonl.gz','rt')as bb:
  for i,(x,y)in enumerate(zip(aa,bb)):
   if i>=2256:break
   x=json.loads(x);y=json.loads(y);error=max(np.max(abs(np.asarray(x[k])-y[k]))for k in['qpos_full','qvel_full','actual_ctrl','mocap_pos']);native_error=max(native_error,float(error));native+=1
 assert native==2256 and native_error<=1e-8
out=dict(status='GOAL_REFERENCE_RENEWAL_INDEPENDENT_PASS',records=checks,first_trigger_step=(triggers[0]['step']if triggers else None),first_updated_plan_status=(plans[triggers[0]['step']]['stats']['status']if triggers else None),original_ns_anchor_checked=a.anchor_original_ns,pre_trigger_public_states=(282 if a.anchor_original_ns else 0),pre_trigger_public_max_errors=errors,pre_trigger_native_states=native,pre_trigger_native_max_error=native_error,new_integrations=0,reference_does_not_authorize_control=True)
(pair/'GOAL_REFERENCE_RENEWAL_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
