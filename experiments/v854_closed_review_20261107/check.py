"""Check closed actual runs and identify the exact provenance assertion; no models."""
import fcntl,gzip,hashlib,importlib.abc,json,signal,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('CLOSED_REVIEW_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v854_closed_review_20261107';ROOT=R/'runs/v854_daytime_input_continuation';W=R/'experiments/v853_maneuver_worker'


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('CLOSED_REVIEW_180S')));signal.alarm(180);assert not(OUT/'RESULT.json').exists();inputs={}
    def read(p):
        b=p.read_bytes();inputs[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return json.loads(gzip.decompress(b)if p.suffix=='.gz'else b)
    def lines(p):
        b=p.read_bytes();inputs[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return[json.loads(x)for x in b.splitlines()]
    final=read(ROOT/'FINALIZED.json');independent=read(ROOT/'FINAL_INDEPENDENT_AUDIT.json');window=read(ROOT/'ROUND_WINDOW.json');assert window['round_closed']and final['source_and_decompressed_sha_verified']and final['source_unchanged']
    frozen=read(R/'experiments/v854_daytime_input_continuation/CANDIDATE_FREEZE.json')
    for path,value in frozen['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==value,('FROZEN_INPUT_CHANGED',path)
    runs=[]
    for variant in ['A32','B64']:
        pair=R/f'runs/v853_maneuver_worker/v853_{variant}_main_slot01/paired';cell=pair/'geometry_memory';result=read(cell/'result.json');replay=read(pair/'NATIVE_REPLAY_AUDIT.json');canonical=read(pair/'INDEPENDENT_CANONICAL_AUDIT.json');trace=read(cell/'trace.json');latency=read(cell/'CONTROL_LATENCY.json')
        assert replay['maximum_full_native_state_ctrl_error']==0 and replay['replay_integration_steps']==result['physics_steps']
        assert result['contacts']['robot_obstacle_contact_records']==result['contacts']['unknown_contact_records']==0
        distances=[x['goal_distance_m']for x in trace]
        runs.append(dict(variant=variant,outcome=result['outcome'],public_steps=result['public_steps'],native_steps=result['physics_steps'],elapsed_minutes=result['elapsed_s']/60,final_goal_m=result['goal_distance_m'],closest_goal_m=min(distances),closest_goal_step=distances.index(min(distances)),backup_public_steps=result['backup_steps'],backup_fraction=result['backup_steps']/result['public_steps'],minimum_actual_clearance_m=result['minimum_dynamic_native_clearance_m'],native_replay_error=0,all_audits_completed=variant=='A32',canonical_failed_checks=[k for k,v in canonical['checks'].items()if not v],decision_p50_s=latency['p50_s'],decision_p95_s=latency['p95_s']))
    pair=R/'runs/v853_maneuver_worker/v853_B64_main_slot01/paired';audit=read(pair/'INDEPENDENT_CANONICAL_AUDIT.json');bad=[r for r in audit['forward_admission_checks']if not r['passed']];assert len(bad)==1 and bad[0]['step']==936 and[k for k,v in bad[0]['checks'].items()if not v]==['registered_five_low_speed']
    decisions=lines(pair/'geometry_memory/control_decisions.jsonl');r=[x for x in decisions if x['step']==936 and x['stage']=='BACKUP_APPEND'and x.get('candidate_role')=='ORDINARY'][-1];tails=r['detail']['candidates'];forward=[x for x in tails if x['library']=='FORWARD_EXTENSION'];original=[x for x in tails if x['library']=='ORIGINAL'];assert len(original)==16 and all(x['reason']is not None for x in original)and len(forward)==1 and forward[0]['reason']is None
    c=read(pair/'geometry_memory/progress_certificates/certificate_0936.json.gz');assert c['minimum_causal_predicted_clearance_m']>=.155 and c['terminal_speed_m_s']<=.025
    sys.path.insert(0,str(W));from audit_maneuver import check_certificate
    proof=check_certificate(c);assert proof['normal_allowed']
    cause=dict(step=936,failed_audit='forward_tail_extension_provenance.registered_five_low_speed',actually_examined_forward_candidates=1,old_auditor_requires_examined_forward_candidates=5,first_registered_candidate_passed=True,independent_saved_maneuver_proof=proof,physical_thresholds_satisfied=True,explanation='V853 changed complete maneuver selection to first feasible; old canonical forward-library audit still requires all five recorded trials. This audit applicability was not adapted before freeze. Does not change B64 actual NO_RESERVED_RECOVERY_COMMAND non-arrival or qualify unexecuted audits.')
    guard=(R/'REVIEW_PENDING').read_bytes();assert guard==(ROOT/'REVIEW_PENDING.before').read_bytes()
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    current=read(R/'CURRENT_EXPERIMENT.json');assert current['status']=='REVIEW_PENDING'and current['active_pid']is None and not Path('/proc/479697').exists()
    result=dict(status='CLOSED_REVIEW_COMPLETE_NO_NEW_MODEL_WORK',stop_local=datetime.fromtimestamp(window['closed_unix'],timezone(timedelta(hours=8))).isoformat(),running=False,runs=runs,stop_cause=cause,backend=read(ROOT/'cpu_batch_qualification/RESULT.json'),original_freeze_files_verified=len(frozen['files']),original_archive_source_and_decompressed_sha_verified=final['source_and_decompressed_sha_verified'],original_finalized_unchanged=True,unexecuted_variant='C328',unexecuted_total_navigation=16,new_models=0,new_integrations=0,new_navigation=0,training_updates=0,review_pending_restored=True,execution_lock_idle=True,no_restart=True)
    (OUT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(OUT/'INPUT_SHA256.json').write_text(json.dumps(inputs,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
