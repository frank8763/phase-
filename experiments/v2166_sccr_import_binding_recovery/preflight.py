from common import *
import ast
P=R/'runs/v2165_sccr_dual_actor_component'
def candidate():
 parent=read(P/'SOURCE_FREEZE.json')['files'];files=dict(parent)
 for p in C.iterdir():
  if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in S.iterdir():
  if p.is_file()and p.suffix=='.json'and p.name not in {'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}:files[str(p.relative_to(R))]=sha(p)
 for n in ['OWNER_CLOSED.json','components/POLICY/COMPLETION.json','components/POLICY/worker.console','components/POLICY/WORKER_ONCE.json','components/POLICY/POST_POLICY_STORAGE_BARRIER.json','runtime_archives/POLICY/FULL_REMOTE_VERIFIED.json','runtime_archives/POLICY/TRANSPORT_CLEANUP.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json']:
  p=P/n;files[str(p.relative_to(R))]=sha(p)
 return parent,files
def check():
 assert not(S/'SOURCE_ONCE.json').exists()and all(not(O/n).exists()for n in ['OWNER_ONCE.json','NUMERICAL_ADMISSION.json','COMPLETION.json','OWNED_CHILD.json'])
 assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'components/POLICY/POST_POLICY_STORAGE_BARRIER.json')['passed']
 for p in [P/'LAUNCH_IDENTITY.json',P/'components/POLICY/OWNED_CHILD.json']:
  i=read(p);stat=Path('/proc',str(i['pid']),'stat');assert not stat.exists()or stat.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 assert read(S/'PRELUDE_BINDING_PROOF.json')['red_old_and_green_corrected']and read(S/'SOFTWARE_PROOF.json')['passed']
 old=R/'experiments/v2165_sccr_dual_actor_component/worker.py';expected=old.read_text().replace('import numpy as np,torch,importlib.metadata','import numpy as np,torch\n from importlib.metadata import version as package_version').replace("importlib.metadata.version('stable-baselines3')","package_version('stable-baselines3')");assert expected==(C/'worker.py').read_text()
 for p in C.glob('*.py'):ast.parse(p.read_text())
 from evidence import deliver
 for rid in [None,'POLICY']:compile(deliver(rid,preview=True),'controlled_binding_recovery_transport','exec')
 parent,files=candidate();assert all(sha(R/n)==h for n,h in files.items());raw=sum((R/n).stat().st_size for n,h in files.items()if parent.get(n)!=h);assert raw+512*1024<12*1024**2
 from reservation import admission
 return dict(passed=True,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,source_once_not_consumed=True,one_import_binding_revision_only=True,inherited_numerical_and_import_proofs_not_rerun=True,source_members=len(files),delta_members=sum(parent.get(n)!=h for n,h in files.items()),delta_raw_bytes=raw,budget=admission())
if __name__=='__main__':
 v=check();dump(S/'PRE_SOURCE_PREFLIGHT.json',v);print(json.dumps(v))
