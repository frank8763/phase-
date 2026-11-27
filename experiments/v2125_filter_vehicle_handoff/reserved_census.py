"""One new bounded lane; all older retained evidence is included in baseline."""
from pathlib import Path
import json,os,subprocess
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name;MIB=1024**2
def admission():
 b=json.loads((S/'BASELINE_DRAFT.json').read_text());assert b['limit_bytes']==16106127360 and b['old_joint_peak_upper_bytes']==16095019008
 assert b['task_bytes']==224*MIB and b['archive_bytes']==240*MIB and b['download_bytes']==32*MIB and b['metadata_bytes']==8*MIB and b['root_bytes']==512*MIB
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes'])
 assert peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes']and b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,limit_bytes=b['limit_bytes'])
def measure(output,limits):
 from context import O
 b=json.loads((S/'BASELINE_DRAFT.json').read_text());proof=admission();output=Path(output).resolve()
 assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*MIB
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0])
 upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(272+512)*MIB<=proof['joint_peak_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*MIB
