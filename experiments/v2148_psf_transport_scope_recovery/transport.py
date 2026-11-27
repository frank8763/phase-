"""Own IO recovery namespace; original scientific source stays byte-frozen."""
import ast,copy,os,sys,json,time,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;OLD=R/'experiments/v2147_psf_full_route';ROOT=R/'runs/v2147_psf_full_route';D=S/'recovery'
sys.path.insert(0,str(OLD));import context
m=context.load('untouched_v2147_transport_functions',OLD/'evidence.py')
read=m.read;put=m.put;sha=m.sha

def bound():
 # Only archive source subgrant16 (runtime48, both within64 aggregate), own
 # physical transport namespace and tags differ. All original scientific bytes
 # stay frozen and each member is verified by established archive/readback.
 text=(OLD/'evidence.py').read_text();tree=ast.parse(text)
 fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='archive')
 text=ast.unparse(fn).replace('64 if runtime else 2','48 if runtime else 16').replace('v2147-','v2148-')
 space=dict(vars(m),C=C,SOURCE_D=D)
 def scope(rid):
  assert rid is None or rid=='PSF';return (ROOT,D)if rid is None else(ROOT/'components/PSF',S/'runtime_archives/PSF')
 space['scope']=scope;exec(compile(text,'<bounded-original-archive-own-namespace>','exec'),space)
 deliver=ast.unparse(next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='deliver'))
 # Preserve original quota census and all network semantics; exact new tag only.
 deliver=deliver.replace("C / 'reservation.py'","OLD / 'reservation.py'").replace('phase-v2147-filter-vehicle-handoff-source-20261127','phase-v2148-psf-source-transport-recovery-20261127').replace('v2147_source','v2148_source')
 space.update(OLD=OLD);exec(compile(deliver,'<bounded-original-delivery-own-namespace>','exec'),space)
 return space

def ref(rid=None):
 target=D if rid is None else S/'runtime_archives/PSF';target.mkdir(parents=True,exist_ok=True)
 assert not(target/'SOURCE_SYNC_RESULT.json').exists()
 p=ROOT/'recovery/SOURCE_SYNC_RESULT.json';v=read(p);assert v['remote_verified']and v['head']=='95006747a0f4d5bfafcd638be85bc33351357d9a'
 put(target/'SOURCE_SYNC_RESULT.json',dict(head=v['head'],remote_verified=True,push_executed=False,ref_executed=False,original_source_sync_path=str(p.relative_to(R)),original_source_sync_sha256=sha(p),new_helper_late_Release_members_not_in_original_Git=True))

def chain():
 r=read(D/'FULL_REMOTE_VERIFIED.json');assert r['passed']and read(D/'TRANSPORT_CLEANUP.json')['passed']and not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 files=read(ROOT/'SOURCE_FREEZE.json')['files'];old=read(m.P/'SOURCE_FREEZE.json')['files'];index=read(D/'ARCHIVE_INDEX.json');members={x['path']:x for x in index['files']}
 assert all(old.get(n)==h or members.get(n,{}).get('sha256')==h for n,h in files.items())and all(sha(R/n)==h for n,h in files.items())
 prior=read(m.P/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert prior['passed']and prior['all_frozen_members_remote_chain_covered']
 for p in C.iterdir():
  if p.is_file():assert members[str(p.relative_to(R))]['sha256']==sha(p)
 v=dict(passed=True,all_frozen_members_remote_chain_covered=True,uncovered_members=[],source_members=len(files),source_commit=r['source_commit'],index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(D/'ARCHIVE_INDEX.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),source_sync_result_path=str((D/'SOURCE_SYNC_RESULT.json').relative_to(R)),source_sync_result_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),models_authorized=False,late_transport_helper_recovered_by_Release_members=True,failed_original_partial_archive_unchanged=True)
 put(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json',v);put(ROOT/'POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True,recovery_sha256=sha(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),actual_remote_all_SHA=True,cleanup_sha256=sha(D/'TRANSPORT_CLEANUP.json'),models_authorized=False));put(S/'SOURCE_CHAIN_CLOSED.json',v);print(json.dumps(dict(passed=True,source_members=len(files))))

def check():
 assert not(S/'HELPER_CHECK_ONCE.json').exists();put(S/'HELPER_CHECK_ONCE.json',dict(unix=time.time(),models=0))
 assert read(ROOT/'SOURCE_QUALIFICATION.json')['passed']and not(ROOT/'components/PSF/PILOT_ONCE_CLAIM.json').exists()
 assert not(ROOT/'recovery/FINALIZED.json').exists()and not(ROOT/'recovery/ARCHIVE_INDEX.json').exists()and read(ROOT/'recovery/ARCHIVE_CLAIM.json')['archive_cap']==2*1024**2
 files=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 assert read(ROOT/'BASELINE_DRAFT.json')['archive_bytes']==64*1024**2
 b=bound()
 for rid in [None,'PSF']:compile(b['deliver'](rid,preview=True),'preview','exec')
 # Single owner body and original admission are unchanged. No model import.
 assert all(not(ROOT/'components/PSF'/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 put(S/'HELPER_SOFTWARE_PROOF.json',dict(passed=True,models=0,NLP=0,physics=0,replay=0,original_source_SHA_all_verified=len(files),old_qualification_not_repeated=True,source_cap_bytes=16*1024**2,runtime_cap_bytes=48*1024**2,aggregate_archive_reservation=64*1024**2,new_push=False,late_helper_memberSHA_recovery=True))
 print('transport helper check PASS')

if __name__=='__main__':
 os.sched_setaffinity(0,{5});stage=sys.argv[1];rid=sys.argv[2]if len(sys.argv)>2 else None
 if stage=='check':check()
 elif stage=='archive':bound()['archive'](rid)
 elif stage=='ref':ref(rid)
 elif stage=='deliver':raise SystemExit(bound()['deliver'](rid))
 elif stage=='chain':chain()
 else:raise AssertionError(stage)
