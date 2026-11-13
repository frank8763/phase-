"""Zero-model evidence review of the completed analytical preparation series."""
import sys,json,hashlib,fcntl,math,ast
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_coupled_source_20261113';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();import numpy as np
NAMES=['v1115_coupled_complete_source','v1116_native_path_constraints','v1117_fixed_tick_native_sqp','v1118_coupled_live_qualification','v1119_integer_cusp_timing','v1120_explicit_timing_seed']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not(D/'FINALIZED_REVIEW.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 rows=[]
 for name in NAMES:
  O=R/'runs'/name;x=json.loads((O/'COMPLETION.json').read_text());assert x['closed']and x['models']==x['physical_integrations']==0 and x['guard_original']and x.get('frozen_source_unchanged',x.get('source_unchanged'))
  frozen=json.loads((O/'SOURCE_FREEZE.json').read_text());assert all(sha(R/n)==h for n,h in frozen.items()),name
  if name!='v1118_coupled_live_qualification':
   with np.load(O/'CONTROLLER_SOURCE.npz')as z:
    n=len(z['requests']);assert len(z['states'])==n+1 and len(z['controls'])==len(z['command_modes'])==len(z['steering_targets'])==len(z['coupled_episodes'])==n;assert np.isfinite(z['states']).all()and np.isfinite(z['controls']).all()
   checks=x['complete_review']['checks'];assert x['python_accounting']['python_full_source']==n;assert x['cpp_python_maximum_error']<=1e-8
   if x['passed']:
    assert all(checks.values());stops=x['complete_review']['rolling_stops'];assert len(stops)==len(range(0,n-2200,125))and all(t['passed']for t in stops);assert x['python_accounting']['python_rolling_stops']==2200*len(stops);assert(O/'COMPLETE_REFERENCE_CONTRACT.json').is_file()
   else:assert not all(checks.values())or x.get('error')or not x['complete_review'].get('passed');assert x['handoff_selection']['mode']=='RETAINED_COMPLETE_STOP'
   counts=dict(cpp_native=x['cpp_accounting']['completed_native'],python_native=sum(x['python_accounting'].values()),entry=x['entry_analytical_work']);failed=[k for k,v in checks.items()if not v]
  else:
   assert x['passed']and len(x['suffixes'])==24 and x['maximum_state_ctrl_error']<=1e-8 and x['missing_active_refused']and x['inconsistent_episode_refused'];n=None;counts={k:x[k]for k in ['cpp_native','python_native']};failed=[]
  rows.append(dict(name=name,passed=x['passed'],selected_native=n,wall_s=x['wall_s'],counts=counts,failed_final_gates=failed,model_integrations=0))
 result=dict(evidence_integrity_passed=True,software_outcomes=rows,physical_models=0,physical_integrations=0,old_NS_observed_route_pass_preserved=True,same_version_three_route_passed=False,new24_executed=False,new24_denominator=None,new12h_physical_root_started=False,complete_recovery_source_passed=rows[-1]['passed'],physical_window_authorization='RPCCR_COUPLED_ROUTE_AUTHORIZATION_20261113.json',guard_original=True,execution_lock_idle=True,source_unchanged=True,actual_executor_and_independent_auditor_qualification_still_required=True)
 dump(D/'FINALIZED_REVIEW.json',result)
 report=R/'docs/RPCCR_COUPLED_ROUTE_PREPARATION_20261113_REPORT.md';report.write_text('# Coupled-mode route preparation\n\nThe prior NS observed route success is preserved. V1114 both physical steering/restart/stop components passed, but that is not same-version three-route or24 acceptance. The new independently authorized12-hour physical root has not started. Every operation reviewed here used zero physical models and integrations.\n\nV1115–V1117 complete-source candidates were rejected under unchanged endpoint and mode-envelope gates. Read-only diagnosis found nearly saturated first-three-gear steering, so V1119 explicitly searches bounded integer timings before one constrained refinement. V1119 selection returned the old timing seed; this defect is preserved explicitly. V1120 selects its refinement seed only from the new timing beams and retains the original hard admission gates. V1118 mode-state suffix seam passed24 full suffix tests with maximum state/control error2.78e-16; it does not replace physical route qualification.\n\nNext physical launch requires complete source admission plus actual executor and independent auditor qualifications. Same-version three-route mains and exact complete repeats must ALL pass before the fixed24 list may start within the same nonextendable12-hour root. Old failures/results/windows remain unchanged. No24 denominator/rate is reported for unexecuted tasks.\n\n```json\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n```\n')
 for p in (R/'experiments/v1119_closed_software_review').glob('*.py'):ast.parse(p.read_text())
 pointer=R/'CURRENT_EXPERIMENT.json';cur=json.loads(pointer.read_text());assert cur.get('active_run')in [None,'runs/v1119_integer_cusp_timing','runs/v1120_explicit_timing_seed'];cur.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_preparation_review=result,latest_report=str(report.relative_to(R)),latest_mode_suffix_qualification=dict(passed=True,completion='runs/v1118_coupled_live_qualification/COMPLETION.json',scope='24 software suffixes, not physical integration'))
 dump(pointer,cur)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- 耦合完整源软件准备闭批复核：'+json.dumps(rows,ensure_ascii=False)+'；所有新实际模型/积分0，旧NS成功保留，同版本三路线/24均未完成，新授权12h物理根未启动。下一先完整源与实际执行/独立审核接口全资格，再物理三路线全主/重复过后才条件24。见docs/RPCCR_COUPLED_ROUTE_PREPARATION_20261113_REPORT.md。\n')
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
