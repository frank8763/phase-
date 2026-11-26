"""CPU4 independent saved-result readout, no model/solver/replay/audit."""
from pathlib import Path
import os,json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import evidence as e
R=e.R;C=e.C;S=e.ROOT
def main():
 a=e.read(S/'EVIDENCE_ADMISSION.json');assert os.sched_getaffinity(0)=={4}and not a['models_authorized']and time.time()<a['absolute_end_unix']
 assert a['source_freeze_sha256']==e.sha(S/'SOURCE_FREEZE.json')and e.read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 O=S/'evidence_lane';assert not(O/'RESULT.json').exists()
 priest=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual';shadow=e.read(priest/'cycle_000000_shadow.json');raw=e.read(priest/'PRIEST_RAW_CURRENT_PROPOSAL.json')
 readout=dict(closed=True,passed=True,models=0,solver_calls=0,physics=0,replay=0,new_independent_audits=0,formal_trials=0,PRIEST=dict(raw_request=raw['raw_request'],minimum_predicted_m=shadow['minimum_raw_m'],required_predicted_m=shadow['required_raw_m'],deficit_m=shadow['required_raw_m']-shadow['minimum_raw_m'],failed_checks=[k for k,v in shadow['checks'].items()if not v],original_component_passed=False,raw_control_was_not_applied=True,interpretation='Original engineering preview fails conservative full-stop geometry before any normal command; do not change thresholds or claim native polynomial infeasible'),SCCR=e.read(R/'runs/v1942_sccr_applicability_decision/RESULT.json')['disposition'],PCBF=e.read(R/'runs/v2106_pcbf_saved_return_analysis/RESULT.json')['finding'],whole_route_mechanism_gain_established=False,more_algorithms_do_not_guarantee_arrivals=True,source_paths_SHA256={str(p.relative_to(R)):e.sha(p)for p in [priest/'cycle_000000_shadow.json',priest/'PRIEST_RAW_CURRENT_PROPOSAL.json',R/'runs/v2106_pcbf_saved_return_analysis/RESULT.json']})
 e.put(O/'RESULT.json',readout);print(json.dumps(readout))
if __name__=='__main__':main()
