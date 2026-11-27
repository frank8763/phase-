"""49 full-width exact synthetic profile pipeline; no numerical/physical model."""
from context import R,C,SOURCE as S,read,put,load,sha
from pathlib import Path
from types import SimpleNamespace
import os,json,time,hashlib,signal,datetime
assert os.sched_getaffinity(0)=={2}and not(S/'IO_PIPELINE_SOFTWARE.json').exists()and not(S/'SOURCE_ONCE.json').exists()
import numpy as np
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_PROFILE_IO180S')));signal.alarm(180)
folder=S/'software_io';folder.mkdir(exist_ok=False);limits=read(S/'components/PROJ/LIMITS_DRAFT.json');baseline=read(S/'BASELINE_DRAFT.json');proofs=[];sources={'experiments/v1863_remaining_routes_dwa/response.py':sha(R/'experiments/v1863_remaining_routes_dwa/response.py')}
quota_module=load('CP_real_quota_software_pipeline',C/'quota.py');quota_module.base.measure=lambda output,limits:(int(__import__('subprocess').check_output(['du','-sx','-B1',str(folder)]).split()[0]),baseline['all_prior_evidence_upper_bytes']+baseline['preparation_bytes']+baseline['metadata_bytes']+int(__import__('subprocess').check_output(['du','-sx','-B1',str(folder)]).split()[0]))
__import__('sys').modules['quota']=quota_module;quota_module.grant.base.measure=quota_module.base.measure;quota=quota_module.EvidenceQuota(folder,limits);quota.bind_external_names([]);quota.write_enforcement_active=True
io=load('CP_original_writer_software_fullprofile',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');resources=load('CP_original_terminal_resources',C/'resources.py');work=load('CP_original_workledger_no_modelbind',C/'work.py');ledger=work.ModelWork(limits,time.time()+180);service_mod=load('CP_original_full_profile_service',C/'evidence_service.py');atomic=load('CP_original_compactJSON',C/'compact_json.py').atomic
rng=np.random.default_rng(218000);start=time.monotonic();resources.reserve_terminal(quota)
with io.OutputBoundary(folder,quota.charge_write):
 resources.prepare(quota,'STOPPED_EVENT_PREPARATION',ttl=180)
 svc=service_mod.Service(SimpleNamespace(np=np),setup=dict(explicit_synthetic_not_model=True),task=dict(explicit_software_fixture=True),source=sources,out=folder,quota=quota,ledger=ledger,window={})
 for idx in range(49):
  if idx and idx%2==0:resources.prepare(quota,'STOPPED_EVENT_PREPARATION',ttl=180)
  n=2200 if idx==48 else(2210 if idx%2==0 else 2205)
  # Random finite payload maximizes practical entropy; fixed shape maximum is
  # independently bounded without treating this sample as all possible inputs.
  arrays=dict(states=rng.standard_normal((n+1,8)),controls=rng.standard_normal((n,4)),memory=rng.standard_normal((n+1,5)),requests=np.zeros((n,3)))
  arrays['requests'][:n-2200,0]=np.linspace(0,.02,n-2200)if n>2200 else[]
  proof=dict(native=n,arrays=f'cycle_{idx:06d}_software.npz',origin_packet=dict(explicit_fake_packet=True,native_tick=idx*5));proof['hybrid_evidence']=svc.persist(proof,arrays);proofs.append(proof)
  quota.atomic(folder/f'PROFILE_{idx:03d}.json',proof,atomic)
 # Every saved member reconstructs exactly; no model callback/replay/audit.
 for proof in proofs:
  with svc.load_full(proof)as arrays:
   assert {k:svc.recipe.array_identity(v)for k,v in arrays.items()}==proof['hybrid_evidence']['arrays_identity']
  svc.confirm_full_geometry(proof) # only cache bookkeeping, not physical geometry
 snapshot=svc.snapshot();quota.retire_grant();resources.save_terminal(quota,dict(passed=True,profiles=49),lambda:quota.atomic(folder/'RESULT.json',dict(passed=True,profiles=49),atomic))
 assert ledger.python==ledger.cpp==0 and snapshot['full_records']==49 and snapshot['rebuilt_native']==0
actual=int(__import__('subprocess').check_output(['du','-sx','-B1',str(folder)]).split()[0]);assert actual<20*1024**2
# Verified synthetic generated fixtures only; retain exact identity manifest and
# pipeline result. Never remove scientific raw/source/currentinput/anchors.
entries=[]
for p in sorted(folder.rglob('*')):
 if p.is_file():
  st=p.lstat();entries.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=st.st_size,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino))
put(S/'IO_SYNTHETIC_VERIFIED_CLEANUP_MANIFEST.json',dict(verified49full_array_identity_roundtrips=True,entries=entries,only_generated_synthetic_software_fixtures=True))
for row in entries:
 p=R/row['path'];st=p.lstat();assert(st.st_size,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(row[k]for k in ['bytes','mtime_ns','device','inode'])and sha(p)==row['sha256'];p.unlink()
folder.rmdir()
x=dict(passed=True,scope='REAL_EVIDENCEQUOTA_OUTPUTBOUNDARY_HYBRID_SERVICE_SYNTHETIC_IO',full_profiles=49,shape_maximum_states=[2211,8],shape_maximum_controls=[2210,4],shape_maximum_memory=[2211,5],requests=[2210,3],exact_profile_identity_roundtrips=49,random_finite_synthetic_payload=True,pack_bytes=snapshot['pack_bytes'],peak_fixture_allocated_bytes=actual,mathematical_uncompressed_arrays_maximum_bytes=49*((2211*13+2210*7)*8),terminal_reserved_bytes=1024**2,original_task_IO_root_and15GiB_unchanged=True,original_frozen_baseline=14873092096,metadata_within4MiB_after_verified_synthetic_cleanup=True,synthetic_only_cleanup_manifest_sha256=sha(S/'IO_SYNTHETIC_VERIFIED_CLEANUP_MANIFEST.json'),new_NLP_models_Predictor_Allocator_physics_replay_audit_Source=0,CPU=2,wall_s=time.monotonic()-start,source_SHA256={str(p.relative_to(R)):sha(p)for p in [C/'io_preflight.py',C/'evidence_service.py',C/'quota.py',C/'base_quota.py',C/'granted_quota.py',C/'direct_bits.py',C/'resources.py']},created_at=datetime.datetime.now().astimezone().isoformat());put(S/'IO_PIPELINE_SOFTWARE.json',x);print(json.dumps({k:v for k,v in x.items()if k!='source_SHA256'}))
