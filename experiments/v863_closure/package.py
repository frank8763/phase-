"""Archive the two closed runs and signed RPP plugin provenance, without base-runtime duplication."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v862_v863_closure';REC=R/'records/nav2_v863_execution_20261107'
def main():
 assert json.loads((REC/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed']
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','REVIEW_PENDING','docs/paper_ras/CLAIM_EVIDENCE.json']:
  p=O/'snapshots'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,p)
 spec=importlib.util.spec_from_file_location('archive_tools',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True)
 roots=['runs/v858_nav2_verified/v862_ready_static','runs/v858_nav2_verified/v863_rpp_static','runs/v862_execution_20261107','runs/v863_execution_20261107','runs/v863_rpp_preparation','experiments/v862_execution_20261107','experiments/v863_rpp_preparation','records/nav2_v862_execution_20261107','records/nav2_v863_execution_20261107','runs/v862_v863_closure/snapshots']
 files=[]
 for root in roots:
  files += [p for p in m.walk(R/root)if 'cache'not in p.relative_to(R/root).parts and '__pycache__'not in p.parts]
 for name in ['docs/NAV2_READY_STATIC_V862_EXECUTION_REPORT.md','docs/NAV2_RPP_STATIC_V863_REPORT.md','docs/paper_ras/MANUSCRIPT_WORKING.md','docs/RAS_RESEARCH_ROADMAP_20261107.md']:files.append(R/name)
 plugin=json.loads((R/'runs/v863_rpp_preparation/PLUGIN_READY.json').read_text());files += [R/row['path']for row in plugin['new_files']]
 group=m.archive('v862-v863-evidence',files)
 index=dict(format_version=1,repository='frank8763/phase-',release_tag='phase-nav2-v862-v863-20261107',release_url='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v862-v863-20261107',created_unix=time.time(),archives=[{k:v for k,v in group.items()if k!='files'}],base_runtime_dependency='records/nav2_v856_20261107/RECORD_INDEX.json : v856-ros-runtime',scientific_outcome='V862_MPPI_STATIC_FAILED; V863_RPP_ONE_STATIC_DEVELOPMENT_ROUTE_PASSED; DYNAMIC_NOT_RUN',status='LOCAL_SOURCE_MEMBER_DECOMPRESSION_AND_PART_SHA_VERIFIED')
 for p in [REC/'RECORD_INDEX.json',m.OUT/'RECORD_INDEX.json']:p.write_text(json.dumps(index,indent=2)+'\n')
 print('PACKAGING_DONE',flush=True)
if __name__=='__main__':main()
