"""Two live-case grants plus bounded retained closed cases, no live global du."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[2];S=R/'runs/v2045_remaining_parallel_source';MIB=1024**2
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def global_admission(*,require_launch=False):
 b=read(S/'QUIESCENT_BASELINE.json');assert b['passed']and b['baseline_recorded_with_all_known_Phase_models_closed']and b['limit_bytes']==15*1024**3
 assert b['preparation_reserve_bytes']==16*MIB and b['prior_closed_actual_reserve_bytes']==144*MIB and b['root_reserve_bytes']==512*MIB
 assert len(b['lanes'])==2 and all(x['task_bytes']==224*MIB and x['archive_bytes']==240*MIB and x['download_bytes']==32*MIB and x['metadata_bytes']==16*MIB for x in b['lanes'])
 peak=b['baseline_allruns_bytes']+b['preparation_reserve_bytes']+b['prior_closed_actual_reserve_bytes']+b['root_reserve_bytes']+sum(sum(x[k]for k in ['task_bytes','archive_bytes','download_bytes','metadata_bytes'])for x in b['lanes']);assert peak==b['joint_peak_bytes']and peak<b['limit_bytes']
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==b['boot_id']
 if require_launch:
  p=read(S/'PREPARATION_FINAL.json');assert p['passed']and p['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and p['baseline_sha256']==sha(S/'QUIESCENT_BASELINE.json')and p['allocated_since_baseline']<=16*MIB and p['all_phase_models_closed_when_checked']
 return dict(passed=True,joint_peak_bytes=peak,limit_bytes=b['limit_bytes'],no_live_global_tree_scan=True)
def measure(output,limits):
 proof=global_admission(require_launch=True);b=read(S/'QUIESCENT_BASELINE.json');output=Path(output).resolve();rid=output.parent.name;plan=read(S/'PLAN_LOCKED.json');row=next(x for rows in plan['methods'].values()for x in rows if x['round_id']==rid);lane=next(x for x in b['lanes']if x['method']==row['method'])
 assert output==R/row['root']/'actual'and os.sched_getaffinity(0)=={lane['CPU']}and limits['maximum_task_evidence_bytes']==224*MIB
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0]);other=sum(sum(x[k]for k in ['task_bytes','archive_bytes','download_bytes','metadata_bytes'])for x in b['lanes']if x['method']!=row['method'])
 upper=b['baseline_allruns_bytes']+b['preparation_reserve_bytes']+b['prior_closed_actual_reserve_bytes']+other+lane['metadata_bytes']+own
 assert upper+(272+512)*MIB<=proof['joint_peak_bytes'];return own,upper
def transport_current_upper():return global_admission()['joint_peak_bytes']-(32+512)*MIB
