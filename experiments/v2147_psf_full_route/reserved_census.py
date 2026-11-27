"""Frozen original upper minus independently remote-verified duplicate credit."""
from pathlib import Path
import json,os,subprocess
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name;MIB=1024**2
def admission():
 from context import read,sha
 b=read(S/'BASELINE_DRAFT.json');old=R/'runs/v2144_sccr_depth_resource_units/BASELINE_DRAFT.json';assert sha(old)==b['prior_baseline_sha256'];prior=read(old)
 p=R/'runs/v2145_verified_whole_transport_recovery/RESULT.json';assert sha(p)==b['verified_duplicate_cleanup_sha256'];credit=read(p)
 assert credit['passed']and credit['closed']and credit['freed_allocated_bytes']==b['verified_duplicate_credit_bytes']==121692160
 assert all(not(R/z['path']).exists()for z in credit['removed'])and sum(z['allocated']for z in credit['removed'])==b['verified_duplicate_credit_bytes']
 for group in credit['groups_closed']:
  d=R/'runs/v2145_verified_whole_transport_recovery/runtime_archives'/group;assert read(d/'FULL_REMOTE_VERIFIED.json')['passed']and read(d/'TRANSPORT_CLEANUP.json')['passed']
 assert b['frozen_prior_baseline_bytes']==prior['frozen_prior_baseline_bytes']==14873092096 and b['all_prior_evidence_upper_bytes']==prior['all_prior_evidence_upper_bytes']+56*MIB-b['verified_duplicate_credit_bytes']
 assert b['limit_bytes']==16106127360 and b['old_joint_peak_upper_bytes']==16095019008 and b['task_bytes']==224*MIB and b['archive_bytes']==64*MIB and b['root_bytes']==512*MIB and b['download_bytes']==32*MIB
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes']);assert peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes']and b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*MIB>=24_000_000
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,limit_bytes=b['limit_bytes'],verified_duplicate_credit_bytes=b['verified_duplicate_credit_bytes'],original_frozen_baseline_unchanged=True)
def measure(output,limits):
 from context import O
 b=json.loads((S/'BASELINE_DRAFT.json').read_text());output=Path(output).resolve();assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*MIB
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0]);upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(64+32+512)*MIB<=b['old_joint_peak_upper_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*MIB
