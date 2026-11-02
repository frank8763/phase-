"""Independently reconstruct recorded proposal-route trigger geometry and progress."""
import argparse,os,json,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
from exact_footprint import pose_values
from motion_tracker import install_time_gate
from planner import wrap
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired);cell=root/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
protocol=read(root/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds']);trace=read(cell/'trace.json');execution=lines(cell/'v648_execution.jsonl');states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};rows=lines(cell/'route_revalidation.jsonl');errors=[];failures=[];references=[]
plans=[read(p)for p in sorted(cell.glob('planning_*.json'))]
for r in rows:
 step=r['step'];index=r['index'];path=np.asarray(r['reference_path']);state=states[step]
 field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));field.pose_values=MethodType(pose_values,field);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
 minimum=float(np.min(field.pose_values(path[index:min(len(path),index+26),:3])));error=abs(minimum-r['current_route_minimum_m']);errors.append(error)
 current=np.asarray(trace[step-1]['pose']);net=False;arc=None
 if step-r['last_plan']>=30 and step>=30:
  previous=np.asarray(trace[step-30]['pose']);old_index=trace[step-30]['path_index'];net=bool(np.linalg.norm(current[:2]-previous[:2])<.04 and abs(wrap(current[2]-previous[2]))<.06)
  lo=max(0,min(old_index,index));hi=min(len(path)-1,max(old_index,index));arc=float(np.linalg.norm(np.diff(path[lo:hi+1,:2],axis=0),axis=1).sum())
 good=error<=1e-10 and r['current_route_invalid']==bool(minimum<.155-1e-6) and r['old_net_motion_stagnant']==net and r['stagnated_without_route_progress']==bool(net and(arc is None or arc<.08)) and((arc is None and r['route_arc_progress_last30_m']is None)or(arc is not None and abs(arc-r['route_arc_progress_last30_m'])<=1e-10))and r['authorizes_control']is False and r['future_native_gate_unchanged']is True
 if not good:failures.append(step)
 # Reference must equal a previously computed causal planner output. The
 # unchanged supervisor may also return a path; that is already certified by
 # the independent full handover audit and is explicitly counted separately.
 source=any(np.array_equal(path,np.asarray(p['path']))for p in plans if p['step']<step and p['path']is not None)
 references.append({'step':step,'matches_prior_causal_planning_path':source})
checks={'has_revalidation_rows':bool(rows),'all_current_geometry_and_progress_recomputed':not failures,'no_control_authorization_from_proposal':all(r['authorizes_control']is False for r in rows),'full_future_control_gates_present':all(x.get('prediction_horizon_steps')==240 and x.get('braking_tail_after_physics_steps')==80 and x.get('terminal_speed_threshold_m_s')==.025 for x in lines(cell/'model_admission.jsonl')if x['status']=='MODEL_SAFE_COMMAND'and not x.get('certified_backup_handover'))}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':checks,'rows':len(rows),'maximum_geometry_reconstruction_error':max(errors,default=0.),'failed_steps':failures,'rows_with_supervisor_or_other_reference':sum(not x['matches_prior_causal_planning_path']for x in references),'verification_integrations':0,'scope':'route proposal bookkeeping, never replaces native future/control audits'}
(root/'ROUTE_COMMITMENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'
