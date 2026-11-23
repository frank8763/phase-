"""Saved metadata only: separate benchmark tables and a complete method registry."""
import csv,hashlib,json,time
from pathlib import Path

R=Path(__file__).resolve().parents[2]
O=R/'runs/v1650_comparison_completion'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name,provenance):
 p=R/name;value=json.loads(p.read_text());provenance[name]=sha(p);return value
def put(p,v):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n');t.replace(p)

def main():
 assert not(O/'ASSEMBLY_ONCE_CLAIM.json').exists()
 put(O/'ASSEMBLY_ONCE_CLAIM.json',dict(unix=time.time(),models=0,metadata_only=True))
 sources={};rows=[]
 g=read('evidence/phase22_formal/G4C/g4c_summary.json',sources)
 prereg=read('evidence/phase22_formal/G4C/data/records/G4C_PREREGISTRATION.json',sources)
 assert g['formal_complete']and g['n_scenarios']==100 and not g['post_open_tuning']and g['scenario_mismatch_n']==0
 assert prereg['methods']==['dwa','phase21_v11','phase22_v1']
 for method,label in [('phase21_v11','Phase21-v11'),('phase22_v1','SCCR / Phase22-v1'),('dwa','DWA-C3 vehicle adaptation')]:
  m=g['methods'][method];n=m['n'];success=m['safe_success']['n'];collision=m['collision']['n'];wall=m['wall_timeout_n']
  assert n==100 and success+collision+wall+m['env_timeout_n']+m['other_failure_n']==n
  rows.append(dict(benchmark='G4C_OLD_CONTRACT',method=label,unit='paired_whole_task',executed=n,successes=success,collisions=collision,wall_timeouts=wall,status='COMPLETE',actual_native=None,own_replay_native=None,goal_distance_m=None))
 f=read('evidence/phase22_formal/Final300/summary.json',sources)
 for method,label in [('phase21_v11','Phase21-v11'),('phase22_v1','SCCR / Phase22-v1')]:
  m=f['summary'][method];assert m['n']==300
  rows.append(dict(benchmark='FINAL300_OLD_CONTRACT',method=label,unit='paired_whole_task',executed=300,successes=m['safe_success_count'],collisions=m['collision_count'],wall_timeouts=m['wall_timeout_count'],status='COMPLETE_ORIGINAL_COMPOSITE_GATE_NOT_PASSED',actual_native=None,own_replay_native=None,goal_distance_m=None))
 assert not f['conclusion']['confirmatory_accuracy_safety_gate_pass']and not f['conclusion']['real_time_gate_phase22_v1_pass']
 relay=read('runs/v1370_overnight_controller_matrix/PARTIAL_RESULTS.json',sources)
 for row in relay:
  if row['stage']=='component':continue
  native=row.get('native')or{}
  rows.append(dict(benchmark='V1370_EXPOSED_DEVELOPMENT',method=row['branch'],unit=row['stage']+'_'+row['role'],executed=1,successes=int(row['passed']),collisions=None,wall_timeouts=None,status=row.get('classification',row.get('status','SEE_ORIGINAL_RESULT')),actual_native=native.get('new_actual_native'),own_replay_native=native.get('own_replay_native'),goal_distance_m=native.get('whole_goal_distance_m',(native.get('physical')or{}).get('goal_distance_m'))))
 priest=read('runs/v1518_compact_parent_control/CLOSED_REVIEW.json',sources)
 assert not priest['whole_route_passed']and priest['physical_native']==0
 formal=read('runs/v1643_formal_parent_metadata/FORMAL_LEDGER.json',sources)
 for row in formal['rows']:
  if not row['registered']:continue
  rows.append(dict(benchmark='REGISTERED_PHASE_MECHANISM',method='RP-CCR '+row['variant'],unit='new_phase_whole_task',executed=1,successes=int(row['model_result']is True),collisions=None,wall_timeouts=None,status=row['status'],actual_native=row['actual_native'],own_replay_native=row['own_replay_native'],goal_distance_m=None))
 methods=[
  dict(method='RP-CCR',identity='V1281 original contract',existing='exposed24/24 plus3complete repeats; registered newphase pair both non-arrival',next='current common-contract peer comparison not yet run',source='experiments/v1281_partial_reconnection_fixed24/owner.py'),
  dict(method='SCCR',identity='Phase22-v1 continuous corridor',existing='G4C60/100; Final300214/300 under old contract',next='current actuator/causal observation adapter required',source='runtime/mk-mini/envs/phase22/mkmini_phase22_v1_continuous_corridor_env.py'),
  dict(method='DWA',identity='frozen G4C C3 vehicle adaptation',existing='G4C61/100 under old contract',next='exact missing environment source restoration and current adapter required',source='runtime/mk-mini/envs/baselines/mkmini_ackermann_dwa_env.py'),
  dict(method='RPP',identity='ExecutableRPP 0.6 /0.4 /0.8 disclosed adaptations',existing='static passes/failures; dynamic non-arrival or evidence stop',next='prospective common-task source/owner/evidence qualification required',source='experiments/v1370_overnight_controller_matrix/route_ros.py'),
  dict(method='MPPI',identity='engineering coherent/deadband MPPI',existing='static non-arrival; dynamic dependency-unexecuted',next='no old retry; new prospective source/observation/control qualification required',source='experiments/v1344_causal_night_entry/coherent_mppi_causal_params.json'),
  dict(method='PRIEST',identity='polynomial+Phase response adaptation; author car mapping unresolved',existing=priest['first_error']+'; saved component only',next='exact author car mapping and genuine optimizer/control adapter required',source='experiments/v1485_priest_current_polynomial_seam/response_policy.py'),
  dict(method='TEB',identity='author topology trajectory optimizer, version not yet frozen',existing='literature only; no vehicle comparison',next='pin author core/version and qualify vehicle/causal observation interface',source=None),
  dict(method='SVG-MPPI',identity='author Stein variational guided MPPI, version not yet frozen',existing='literature only; no vehicle comparison',next='pin author core/version and qualify sampling/control interface',source=None),
  dict(method='PSF',identity='predictive safety filter; method-level vehicle adaptation absent',existing='literature only; no vehicle comparison',next='same nominal controller/model/constraints/terminal contract and faithful implementation',source=None),
  dict(method='PCBF',identity='predictive control barrier function; vehicle adaptation absent',existing='literature only; no vehicle comparison',next='same nominal controller/model/constraints/terminal contract and faithful implementation',source=None),
 ]
 for m in methods:
  p=R/m['source']if m['source']else None
  m['source_present']=bool(p and p.is_file());m['source_sha256']=sha(p)if m['source_present']else None
  m['new_common_benchmark_qualified']=False;m['physical_admission']=False
  if m['source_present']:sources[m['source']]=m['source_sha256']
 result=dict(closed=True,assembly_passed=True,comparisons_all_complete=False,methods=methods,rows=rows,provenance=sources,new_models=0,new_physical_native=0,new_replay_native=0,new_controller_or_numerical_imports=0,no_cross_benchmark_pooled_rate=True,historical_results_not_rerun=True,formal_denominator=20,formal_closed=formal['closed_assignments'],formal_unexecuted=formal['unexecuted_assignments'],recorded_unix=time.time())
 put(O/'EVIDENCE_REGISTRY.json',result)
 with(O/'RESULTS_BY_BENCHMARK.csv').open('w',newline='')as stream:
  writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 lines=['# Algorithm comparison completion: evidence and remaining execution','', 'Historical comparisons retain their original contracts. This is saved-metadata assembly, not new simulation or a pooled league table.','', '|Method|Existing evidence|Remaining concrete prerequisite|','|---|---|---|']
 for m in methods:lines.append('|'+m['method']+'|'+m['existing'].replace('|','/')+'|'+m['next'].replace('|','/')+'|')
 lines+=['','G4C: SCCR60/100 versus DWA61/100; no overall efficacy superiority. Final300:165/300 to214/300, but original composite and real-time gates failed. Recent RPP/MPPI and RP-CCR dynamic trials belong to different cohorts.','', 'All ten method identities are listed; unavailable implementations are not counted as executed failures. New shared benchmark has zero admitted/qualified external methods until source, observation, actuator, task, budget and evidence gates are complete.','', 'Raw provenance, exact SHA and benchmark-specific rows: runs/v1650_comparison_completion/EVIDENCE_REGISTRY.json and RESULTS_BY_BENCHMARK.csv. No prior closed round was rerun, reaudited or replayed.']
 (R/'docs/ALGORITHM_COMPARISON_COMPLETION_20261123.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(dict(methods=len(methods),separate_benchmark_rows=len(rows),metadata_assembly_passed=True,all_algorithm_comparisons_complete=False,models=0)))

if __name__=='__main__':main()
