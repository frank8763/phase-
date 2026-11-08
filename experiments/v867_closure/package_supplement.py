"""Append closed software/operation sources; never rewrite the original execution archive."""
import fcntl,hashlib,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v867_closure';REC=R/'records/nav2_v867_20261108';C=Path(__file__).parent

def main():
 assert json.loads((REC/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed'];lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','REVIEW_PENDING','docs/paper_ras/CLAIM_EVIDENCE.json']:
  p=O/'snapshots'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,p)
 spec=importlib.util.spec_from_file_location('archive_tools',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=R/'runs/v867_margin_navigation/cloud';index=json.loads((m.OUT/'RECORD_INDEX.json').read_text());assert len(index['archives'])==1
 for g in index['archives']:
  for part in g['parts']:assert m.sha(m.OUT/part['name'])==part['sha256']
 files=[]
 for name in ['v868_inflation_software','v867_saved_diagnosis','v869_geometry_software','v870_search_direction','v871_search_direction_qualification','v872_raster_margin_qualification','v873_unsmoothed_qualification']:
  for base in [R/'experiments'/name,R/'runs'/name]:
   if base.exists():files.extend(p for p in m.walk(base)if'__pycache__'not in p.parts)
 files.extend(m.walk(O/'snapshots'));files.extend(m.walk(C))
 for name in ['campaign.console','finalize.console','FINALIZED.json']:
  p=R/'runs/v867_margin_navigation'/name
  if p.exists():files.append(p)
 for name in ['docs/NAV2_MARGIN_STATIC_DYNAMIC_V867_REPORT.md','docs/NAV2_GEOMETRY_SEARCH_20261108_ANALYSIS.md']:files.append(R/name)
 g=m.archive('v867-software-and-closure-supplement',files);index['archives'].append({k:v for k,v in g.items()if k!='files'});index['status']='LOCAL_MAIN_AND_SUPPLEMENT_ALL_SHA_VERIFIED_REMOTE_PENDING';index['created_supplement_unix']=time.time()
 for p in [m.OUT/'RECORD_INDEX.json',REC/'RECORD_INDEX.json']:p.write_text(json.dumps(index,indent=2)+'\n')
 O.mkdir(exist_ok=True);print('IMMUTABLE_ORIGINAL_PLUS_SUPPLEMENT_PACKAGED')
if __name__=='__main__':main()
