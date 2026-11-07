"""Independent zero-integration observation contract and command-bank audit."""
import argparse,gzip,json,math
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
from exact_footprint import pose_values
from motion_tracker import install_time_gate
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();pair=Path(a.paired);cell=pair/'geometry_memory';read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
protocol=read(pair/'STATIC_PROTOCOL.json');execution=lines(cell/'v648_execution.jsonl');admissions=lines(cell/'model_admission.jsonl');beliefs={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};decisions=lines(cell/'control_decisions.jsonl');command=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(command['limits']);rate=np.asarray(command['rate']);checks={}
with gzip.open(cell/'observation_scan_certificate.json.gz','rt')as stream:c=json.load(stream)
created=c['created_step'];before=execution[created-1];state=beliefs[created];q=np.asarray(c['qpos']);v=np.asarray(c['qvel']);ctrl=np.asarray(c['controls']);bounds=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));field.pose_values=MethodType(pose_values,field);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);minimum=float(field.trajectory_values(c['poses'],.01).min());last=np.asarray(c['prefix_command']);expected=[last.copy()for _ in range(8)]
for tick in range(0,320,8):
 target=np.asarray(c['target']).copy()
 if tick>=160:target[2:]=0.
 last=np.clip(np.clip(target,limits[:,0],limits[:,1]),last-rate,last+rate);expected.extend([last.copy()for _ in range(8)])
rows=[x for x in admissions if x['status']=='OBSERVATION_SCAN_CONTRACT'];errors=[]
for x in rows:
 i=x['contract_native_cursor'];r=execution[x['step']];errors.append(max(float(np.max(abs(r['qpos_full']-q[i+7]))),float(np.max(abs(r['qvel_full']-v[i+7]))),float(np.max(abs(np.asarray(r['ctrl'])[command['ids']]-ctrl[i])))))
done=read(cell/'OBSERVATION_SCAN_COMPLETION.json')if (cell/'OBSERVATION_SCAN_COMPLETION.json').exists()else None
checks.update(registered_fixed_scan=created==32 and c['target']==[0.,0.,8.,-8.]and c['first_held_command_ticks']==8 and c['brake_after_native_ticks']==168,no_saved_input_actions=np.max(abs(np.asarray(c['initial_qpos'])-before['qpos_full']))<=1e-8 and np.max(abs(np.asarray(c['initial_qvel'])-before['qvel_full']))<=1e-8 and np.max(abs(np.asarray(c['prefix_command'])-np.asarray(before['ctrl'])[command['ids']]))<=1e-12,exact_canonical_controls=np.max(abs(ctrl-expected))<=1e-12,complete328=len(q)==len(v)==len(ctrl)==328,causal_state_exact=c['forecast_state']=={k:v for k,v in state.items()if k!='step'} and state['center']is None,full_native_geometry=minimum>=.155 and abs(minimum-c['minimum_causal_predicted_clearance_m'])<=1e-8,self_domain=c['minimum_predicted_self_domain_margin_m']>=.002,terminal_complete_stop=np.linalg.norm(v[-1,:2])<=.025 and np.linalg.norm(v[-1,3:6])<=.025,actual_state_and_controls=max(errors,default=1.)<=1e-8,completed_once=done is not None and done['finished_step']==72 and len(rows)==41)
finish=72 if done else 10**9;bank=[]
for d in decisions:
 if d['stage']!='NOMINAL':continue
 candidates=d.get('candidates',[]);diff=[x for x in candidates if x['proposal_role']=='DIFFERENTIAL'];step=d['step']
 if not candidates:continue
 if step<=finish:bank.append(not diff);continue
 feature=np.asarray(candidates[0]['features']);speed=feature[-1];wheel_ref=float(np.clip((speed+1.3*(speed-feature[4]))/.12,-12.,12.));mean=.45*wheel_ref;half=min(2.,abs(mean))
 fronts=sorted({tuple(c['target_command'][:2])for c in candidates if c['proposal_role']=='ANALYTIC'});three=[fronts[0],min(fronts,key=lambda x:abs(x[0])+abs(x[1])),fronts[-1]];expected_bank=[[*front,mean-sign*half,mean+sign*half]for front in three for sign in [-1.,1.]]
 local=len(diff)==6 and all(np.max(abs(np.asarray(row['target_command'])-expected))<=1e-12 for row,expected in zip(diff,expected_bank)) and all(x['target_command'][2]*x['target_command'][3]>=-1e-12 for x in diff)
 bank.append(local)
checks['six_differential_bank_only_after_scan']=bool(bank)and all(bank)
repo=Path(__file__).resolve().parents[2];old=lines(repo/'runs/v721_recursive_unseen_navigation/main01/paired/geometry_memory/v648_execution.jsonl')
baseline_first32_full_state_ctrl=len(execution)>=32 and max(float(np.max(abs(np.asarray([x[k]for x in execution[:32]])-np.asarray([x[k]for x in old[:32]]))))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])<=1e-8
checks['new_first32_full_native_replay']=len(execution)>=32 and read(pair/'NATIVE_REPLAY_AUDIT.json')['maximum_full_native_state_ctrl_error']<=1e-8
out=dict(original_first32_equivalent=baseline_first32_full_state_ctrl,status='EARLY_SCAN_CONTRACT_AND_BANK_PASS'if all(checks.values())else'FAIL',checks={k:bool(v)for k,v in checks.items()},scan_actual_public_steps=len(rows),minimum_recomputed_scan_clearance_m=minimum,maximum_scan_state_error=max(errors,default=None),new_integrations=0,scope='One fixed early observation intervention plus six legal differential proposals; not a general scanning policy or complete navigation result.')
(pair/'EARLY_SCAN_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['status']!='FAIL'
