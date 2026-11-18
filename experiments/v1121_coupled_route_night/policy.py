"""Evidence-backed functional relay is distinct from a hard experiment anomaly."""
def classify(code,result,audit):
 n=result.get('new_actual_native');replay=result.get('replay',{});physical=result.get('physical',{})
 if not isinstance(n,int)or n<=0 or result.get('own_replay_native')!=n:return 'HARD'
 if not replay.get('passed')or replay.get('maximum_qpos_qvel_ctrl_mocap_error',float('inf'))>1e-8 or replay.get('contact_mismatched_ticks')!=0:return 'HARD'
 if physical.get('bad_contacts')!=0 or physical.get('minimum_actual_clearance_m',-1.)<.15-1e-8:return 'HARD'
 if not audit.get('evidence_passed',audit.get('passed')):return 'HARD'
 if code==0 and result.get('passed')and audit.get('passed'):return 'PASSED'
 if result.get('functional_refusal_safely_stopped')and not result.get('passed')and not audit.get('functional_passed',False):return 'FUNCTIONAL_STOPPED'
 return 'HARD'
