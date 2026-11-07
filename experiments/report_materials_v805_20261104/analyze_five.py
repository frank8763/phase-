"""Closed five-run comparison, raw sensor differences and limits; no model."""
import json,gzip,hashlib,signal
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v805_static_five_continuation';read=lambda p:json.loads(p.read_text());lines=lambda p:list(map(json.loads,p.read_text().splitlines()));s=read(root/'FINAL_INDEPENDENT_AUDIT.json');assert s['completed'];out=repo/'runs/v805_five_static_analysis';assert not out.exists();out.mkdir();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIVE_ANALYSIS_180S')));signal.alarm(180)
rows=[];base_execution=None;base_packets=None;basemodel=None
for i,row in enumerate(s['rows']):
 pair=(repo/'runs/v804_no_dynamic_static_contact'/row['name']/'paired')if i==0 else root/row['name']/'paired';cell=pair/'geometry_memory';ex=lines(cell/'v648_execution.jsonl');p=read(pair/'STATIC_PROTOCOL.json')
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=list(map(json.loads,f))
 dec=lines(cell/'control_decisions.jsonl');nominal=[x for x in dec if x['stage']=='NOMINAL'and x.get('candidate_role')=='ORDINARY'];ap=[x for x in dec if x['stage']=='BACKUP_APPEND'and x.get('candidate_role')=='ORDINARY'];tails=[t for x in ap for t in x['detail'].get('candidates',[])];counted=sum(len(x['candidates'])for x in nominal)*240+8*len(ap)+320*len(tails)
 if i==0:base_execution=ex;base_packets=packets;basemodel=hashlib.sha256((pair/'scene_model.mjb').read_bytes()).hexdigest()
 equal=len(ex)==len(base_execution);errors={k:float(np.max(abs(np.asarray([x[k]for x in ex])-np.asarray([x[k]for x in base_execution]))))if equal else None for k in ['qpos_full','qvel_full','ctrl']}
 sensor_errors={k:float(np.max(abs(np.asarray([x[k]for x in packets])-np.asarray([x[k]for x in base_packets]))))if len(packets)==len(base_packets)else None for k in ['lidar','depth']}
 old=lines(repo/'runs/v802_exact_rejection_global/main_slot01/paired/geometry_memory/v648_execution.jsonl');first_difference=None;common_error=0.
 for a,b in zip(old,ex):
  e=max(float(np.max(abs(np.asarray(a[k])-b[k])))for k in ['qpos_full','qvel_full','ctrl'])
  if e>1e-8:first_difference=a['step'];break
  common_error=max(common_error,e)
 rows.append(dict(name=row['name'],seed=row['seed'],strict_static_success=row['strict_static_success'],metrics=row['metrics'],vehicle_trace_equals_first=equal and all(v==0 for v in errors.values()),vehicle_trace_errors=errors,raw_sensor_max_difference_from_first=sensor_errors,model_equals_first=hashlib.sha256((pair/'scene_model.mjb').read_bytes()).hexdigest()==basemodel,first_control_state_difference_from_dynamic_V802=first_difference,common_dynamic_prefix_error=common_error,nominal_predictions=sum(len(x['candidates'])for x in nominal),append_calls=len(ap),tail_predictions=len(tails),counted_private_native=counted,private_account_matches=counted==row['metrics']['private_native'],static_arrival_wall_less_than_old_dynamic_780s_cap=row['metrics']['wall_s']<780,minimum_admitted_static_tail_m=min(float(z['minimum_causal_clearance'])for z in [np.load(x)for x in sorted((cell/'ordinary_certificates').glob('*.npz'))])))
assert all(x['private_account_matches']and x['model_equals_first']for x in rows)
res=dict(status='CLOSED_FIVE_STATIC_COMPARISON',successes=s['successes'],planned=5,rows=rows,same_map_and_route=True,all_vehicle_traces_exactly_equal=all(x['vehicle_trace_equals_first']for x in rows),scope='five noise-seed repetitions of one deterministic known-static route; not independent map generalization or evidence that all dynamic failure causes are uniquely isolated',changed_factors_from_dynamic=['physical actor absent','unknown dynamic causal risk domain disabled','per-run wall cap1200s rather than780s'],unchanged_factors=['19 known static obstacles','physical vehicle dynamics and actuator constraints','global A* initial route','nominal candidate bank and scoring weights','native static full prefix-plus-tail safety requirements'],causal_limit='Successful static following localizes the unresolved dynamic pipeline; it does not separate conservative unknown-motion prior, finite candidate choice and computation as unique causes.',new_models=0,new_integrations=0)
(out/'RESULT.json').write_text(json.dumps(res,indent=2)+'\n');signal.alarm(0);print(json.dumps(res))
