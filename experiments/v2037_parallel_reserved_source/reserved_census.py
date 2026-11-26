"""Conservative fixed reservations replace racy whole-tree live scans.

Only each single-writer actual directory is measured while models run. No
missing file is silently treated as zero, and no concurrent cleanup is credited.
"""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[2];S=R/'runs/v2037_parallel_reserved_source'
MIB=1024**2;LIMIT=15*1024**3
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def global_admission(*,require_launch=False):
 b=read(S/'QUIESCENT_BASELINE.json');assert b['passed']and b['baseline_recorded_with_all_known_Phase_models_closed']
 assert b['limit_bytes']==LIMIT and b['root_reserve_bytes']==512*MIB and b['preparation_reserve_bytes']==64*MIB
 assert len(b['lanes'])==2 and all(x['task_bytes']==224*MIB and x['archive_bytes']==240*MIB and x['download_bytes']==32*MIB and x['metadata_bytes']==6*MIB for x in b['lanes'])
 peak=b['baseline_allruns_bytes']+b['preparation_reserve_bytes']+b['root_reserve_bytes']+sum(sum(x[k]for k in ['task_bytes','archive_bytes','download_bytes','metadata_bytes'])for x in b['lanes'])
 assert peak==b['joint_peak_bytes']and peak<LIMIT,'PARALLEL_RESERVED_GLOBAL_PEAK_REFUSED'
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==b['boot_id']
 if require_launch:
  p=read(S/'PREPARATION_FINAL.json')
  assert p['passed']and p['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and p['baseline_sha256']==sha(S/'QUIESCENT_BASELINE.json')
  assert p['all_phase_models_closed_when_checked']and p['allocated_since_baseline']<=64*MIB
 return dict(passed=True,joint_peak_bytes=peak,limit_bytes=LIMIT,baseline_sha256=sha(S/'QUIESCENT_BASELINE.json'),no_live_global_tree_scan=True,missing_files_not_ignored=True)
def measure(output,limits):
 proof=global_admission(require_launch=True);b=read(S/'QUIESCENT_BASELINE.json');output=Path(output).resolve();lane=next(x for x in b['lanes']if R/x['actual_path']==output)
 assert os.sched_getaffinity(0)=={lane['CPU']}and limits['maximum_task_evidence_bytes']==lane['task_bytes']
 # A readonly native peer and no transport writer exist inside live actual OUT.
 # Thus this exact original du call has one writer, which is this same thread.
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],text=True,timeout=10).split()[0])
 other=sum(sum(x[k]for k in ['task_bytes','archive_bytes','download_bytes','metadata_bytes'])for x in b['lanes']if x['actual_path']!=lane['actual_path'])
 upper=b['baseline_allruns_bytes']+b['preparation_reserve_bytes']+other+lane['metadata_bytes']+own
 # Original quota adds own pending holds +272MiB archive/readback +512MiB root.
 # Together with own task bound this is exactly <= the precharged global peak.
 assert upper+lane['archive_bytes']+lane['download_bytes']+b['root_reserve_bytes']<=proof['joint_peak_bytes']
 return own,upper
def transport_current_upper():
 proof=global_admission()
 # Existing transfer guards add their own32MiB window and global512MiB reserve.
 return proof['joint_peak_bytes']-(32+512)*MIB
