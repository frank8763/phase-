"""Closed-only evidence transport; preserve sources and decompressed-member SHA."""
import fcntl,hashlib,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v858_nav2_verified';OUT=ROOT/'cloud';REC=R/'records/nav2_v858_v859_20261107'
sys.path.insert(0,str(R/'experiments/v856_nav2_closure'))
import package_records as pack
def main():
 for path in [ROOT/'COMPLETION.json',ROOT/'entry02/COMPLETION.json',ROOT/'v859_steering/QUALIFICATION_COMPLETION.json',ROOT/'v860_prediction/COMPLETION.json']:
  d=json.loads(path.read_text());assert d['closed']
 assert(R/'REVIEW_PENDING').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert json.loads((ROOT/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed'];OUT.mkdir(exist_ok=True)
 pack.OUT=OUT;pack.REC=REC;files=[]
 for p in pack.walk(ROOT):
  if p.relative_to(ROOT).parts[0]in ['cloud','audit_qualification']:continue
  files.append(p)
 for name in ['NAV2_VERIFIED_V858_REPORT.md','NAV2_STEERING_V859_REPORT.md','NAV2_PREDICTION_V860_REPORT.md']:files.append(R/'docs'/name)
 for c in ['v858_nav2_verified','v858_nav2_verified_entry','v859_nav2_steering','v860_nav2_prediction']:
  files.extend(p for p in(R/'experiments'/c).iterdir()if p.is_file()and p.suffix in ['.py','.json','.yaml','.md'])
 # Mutable operating pointers are already copied to ROOT/closing_snapshot.
 a=pack.archive('v858-v860-evidence',files);index=dict(format_version=1,repository='frank8763/phase-',release_tag='phase-nav2-v858-v860-20261107',release_url='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v858-v860-20261107',created_unix=time.time(),archives=[{k:v for k,v in a.items()if k!='files'}],dependencies=[dict(release='phase-nav2-v856-20261107',groups=['v856-evidence','v856-ros-runtime'],reason='Original component replay inputs and verified ROS runtime; already archived, do not duplicate')],scientific_outcome=json.loads((ROOT/'FINAL_INDEPENDENT_AUDIT.json').read_text())['outcome'],status='LOCAL_SOURCE_DECOMPRESSION_AND_PART_SHA_VERIFIED_REMOTE_PENDING')
 for base in [REC,OUT]:(base/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
 print('PACKAGE_COMPLETE',flush=True)
if __name__=='__main__':main()
