"""Read-only complete configuration and size checks, no SOURCE claim or neural calls."""
from common import *
import ast,subprocess
P=R/'runs/v2162_pcbf_conditioned_current100'

def candidate():
 parent=read(P/'SOURCE_FREEZE.json')['files'];files=dict(parent)
 for folder in [C,R/'experiments/v2164_sccr_measured_union_sensor',R/'experiments/v2163_pcbf100_ref_readback_recovery']:
  for p in folder.iterdir():
   if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in S.iterdir():
  if p.is_file()and p.suffix=='.json'and p.name not in {'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}:files[str(p.relative_to(R))]=sha(p)
 proof=read(R/'runs/v2164_sccr_measured_union_sensor/RESULT.json')
 for n,h in proof['input_and_source_SHA256'].items():assert sha(R/n)==h;files[n]=h
 for p in [R/'runs/v2164_sccr_measured_union_sensor/RESULT.json',R/'runs/v2164_sccr_measured_union_sensor/OBSERVATION_ACTION_CONTRACT.json',R/'runs/v2164_sccr_measured_union_sensor/PREPARATION_CHECKPOINT.json',P/'FINAL_CHECKPOINT.json',P/'components/PCBF/COMPLETION.json',P/'components/PCBF/POST_COMPONENT_STORAGE_BARRIER.json']:
  files[str(p.relative_to(R))]=sha(p)
 from actors import SPECS
 for n,h in SPECS.values():assert sha(R/n)==h;files[n]=h
 return parent,files

def check():
 assert not(S/'SOURCE_ONCE.json').exists()and not(O/'OWNER_ONCE.json').exists()and not(O/'NUMERICAL_ADMISSION.json').exists()
 assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'components/PCBF/POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 assert not(P/'LAUNCH_IDENTITY.json').exists()and not(P/'components/PCBF/OWNED_CHILD.json').exists()
 for name in ['SOFTWARE_PROOF.json','SAVED_INPUT_SOFTWARE_PROOF.json','ENVIRONMENT_READINESS.json','LAZY_IMPORT_READINESS.json','ENVIRONMENT_GUARD_PROOF.json']:assert read(S/name)['passed'],name
 for p in C.glob('*.py'):ast.parse(p.read_text())
 main=next(x for x in ast.parse((C/'worker.py').read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='main');assert 'authority()'in ast.unparse(main.body[0])
 text=(C/'owner.py').read_text();assert all(n in text for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock'])and 'CPU=2'in text
 from evidence import deliver
 for rid in [None,'POLICY']:compile(deliver(rid,preview=True),'prospective_sccr_transport','exec')
 parent,files=candidate();assert all(sha(R/n)==h for n,h in files.items());raw=sum((R/n).stat().st_size for n,h in files.items()if parent.get(n)!=h)
 assert raw+512*1024<12*1024**2,'SOURCE_ARCHIVE_CONSERVATIVE_RAW_UPPER'
 from reservation import admission
 budget=admission();assert read(S/'SOFTWARE_PROOF.json')['explicit_network_constructors']==0
 return dict(passed=True,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,source_once_not_consumed=True,new_source_members=len(files),new_delta_members=sum(parent.get(n)!=h for n,h in files.items()),delta_raw_bytes=raw,source_archive_cap=12*1024**2,runtime_archive_cap=4*1024**2,full_SCCR_qualified=False,budget=budget)
if __name__=='__main__':
 v=check();dump(S/'PRE_SOURCE_PREFLIGHT.json',v);print(json.dumps(v))
