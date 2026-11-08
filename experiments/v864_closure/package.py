"""Closed V864 raw evidence and V865 unfinished preparation; shared runtime remains in old Releases."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v864_closure';REC=R/'records/nav2_v864_20261107'
def main():
 assert json.loads((REC/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed']
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','REVIEW_PENDING','docs/paper_ras/CLAIM_EVIDENCE.json']:
  p=O/'snapshots'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,p)
 spec=importlib.util.spec_from_file_location('archive_tools',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True)
 roots=['runs/v858_nav2_verified/v864_static','runs/v864_rpp_static_regression','runs/v864_diagnosis','runs/v865_global_margin_preparation','experiments/v864_rpp_static_regression','experiments/v864_diagnosis','experiments/v865_global_margin_preparation','records/nav2_v864_20261107','runs/v864_closure/snapshots']
 files=[]
 for root in roots:files += [p for p in m.walk(R/root)if 'cache'not in p.relative_to(R/root).parts and '__pycache__'not in p.parts]
 for name in ['docs/NAV2_RPP_STATIC_V864_REPORT.md','docs/paper_ras/MANUSCRIPT_WORKING.md','docs/paper_ras/VALIDATION_ORDER.md','docs/STORAGE_POLICY.md']:files.append(R/name)
 g=m.archive('v864-static-diagnosis-evidence',files)
 index=dict(format_version=1,repository='frank8763/phase-',release_tag='phase-nav2-v864-20261107',release_url='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v864-20261107',created_unix=time.time(),archives=[{k:v for k,v in g.items()if k!='files'}],dependencies=['records/nav2_v856_20261107/RECORD_INDEX.json : v856-ros-runtime','records/nav2_v863_execution_20261107/RECORD_INDEX.json : signed RPP plugin and original successful WE'],scientific_outcome='V864_FIRST_STATIC_NS_FUNCTIONAL_FAILED;4UNEXECUTED; V865_CONFIG_PREPARED_NOT_ROS_OR_PHYSICAL_QUALIFIED; DYNAMIC_NOT_RUN',status='LOCAL_SOURCE_MEMBER_DECOMPRESSION_AND_PART_SHA_VERIFIED')
 for p in [REC/'RECORD_INDEX.json',m.OUT/'RECORD_INDEX.json']:p.write_text(json.dumps(index,indent=2)+'\n')
 print('PACKAGING_DONE',flush=True)
if __name__=='__main__':main()
