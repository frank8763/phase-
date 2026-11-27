"""All cheap scope, dependency, namespace, bytes and recovery checks before Source once."""
from context import R,C,ROOT,O,P,read,put,sha,remaining,predecessor_closed
import ast,subprocess,os,json,time
EXCLUDED={'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}
PRIOR=['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json','LAUNCH_IDENTITY.json','owner.console','components/SCCR/COMPLETION.json','components/SCCR/RUNTIME_CLOSED_REVIEW.json','components/SCCR/POST_COMPONENT_STORAGE_BARRIER.json','components/SCCR/OWNED_CHILD.json','runtime_archives/SCCR/ARCHIVE_INDEX.json','runtime_archives/SCCR/FULL_REMOTE_VERIFIED.json','runtime_archives/SCCR/TRANSPORT_CLEANUP.json','recovery/ARCHIVE_INDEX.json','recovery/FULL_REMOTE_VERIFIED.json','recovery/TRANSPORT_CLEANUP.json']
def candidate():
 old=read(P/'SOURCE_FREEZE.json')['files'];files=dict(old)
 for p in C.iterdir():
  if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in ROOT.glob('*.json'):
  if p.name not in EXCLUDED:files[str(p.relative_to(R))]=sha(p)
 for p in (ROOT/'software_writer').glob('*.json'):files[str(p.relative_to(R))]=sha(p)
 for n in PRIOR:files[str((P/n).relative_to(R))]=sha(P/n)
 for n in ['docs/PRIEST_VECTOR_ORIENTATION_V2177_REPORT.md','docs/SCCR_COMPONENT_V2176_REPORT.md']:files[n]=sha(R/n)
 return old,files

def check(require_auth=False):
 assert os.sched_getaffinity(0)=={5}and not(ROOT/'SOURCE_ONCE.json').exists()and not(ROOT/'LAUNCH_ONCE.json').exists()
 assert all(not(O/n).exists()for n in ['NUMERICAL_ADMISSION.json','OWNER_ONCE.json','WORKER_ONCE.json','RESULT.json','COMPLETION.json','OWNED_CHILD.json']);assert predecessor_closed()
 from reservation import admission,idle
 handles=idle();budget=admission()
 for n in ['INITIAL_VECTOR_GATE.json','ROUTE_TIMING_GATE.json','COLLOCATION_SOFTWARE_GATE.json','NORMALIZED_SOFTWARE_GATE.json','DEPENDENCY_IMPORT_PROOF.json','UNADMITTED_WORKER_REFUSAL.json','CASE_WORKER_SOFTWARE_PROOF.json','CASE_ATTRIBUTION_SUPPLEMENT.json','LIFECYCLE_SOFTWARE_PROOF.json']:
  assert read(ROOT/n)['passed'],n
 cases=read(ROOT/'CASES_LOCKED.json');assert cases['maximum_NLP_calls']==2 and len(cases['positive_cases'])==2 and not cases['physical_authority']and not cases['native_author_PRIEST']and cases['first_failure_stops']
 assert sha(C/'collocation.py')=='9bbf7b5ef016b756526f0de0b3501812d6b4c6fa85b7556fd2c6f2db33200a82'
 for p in C.glob('*.py'):ast.parse(p.read_text())
 import evidence
 assert evidence.P==P and evidence.CASES=={'MATH':'MATH'}
 for rid in [None,'MATH']:
  t=evidence.deliver(rid,preview=True);compile(t,'bounded_orientation_math_delivery','exec')
  for token in ['phase-v2177-orientation-projection-math-20261127','CASE_ID','BOUND_D','RESERVED_TRANSPORT_USAGE','end=min(start+600']:assert token in t,token
  assert 'phase-v2156'not in t and 'phase-v2006'not in t and 'assert rid in CASES'in t
 old,files=candidate();assert all(sha(R/n)==h for n,h in files.items())
 d={n:h for n,h in files.items()if old.get(n)!=h};raw=sum((R/n).stat().st_size for n in d);upper=raw+len(d)*2048+512*1024;assert upper<2*1024**2
 if require_auth:assert remaining(read(ROOT/'AUTHORIZATION.json'))>1800
 return dict(passed=True,source_members=len(files),delta_members=len(d),source_raw_bytes=raw,uncompressed_source_tar_upper=upper,budget=budget,all_inherited_source_exact=True,all_source_SHA=True,real_NLP_models_physics=0,maximum_NLP_calls=2,fixed_math_scope_not_author_PRIEST=True,source_once_not_consumed=True)
if __name__=='__main__':x=check();put(ROOT/'PRE_SOURCE_PREFLIGHT.json',x);print(json.dumps(x))
