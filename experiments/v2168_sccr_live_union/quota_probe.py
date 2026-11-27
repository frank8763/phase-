"""Bounded metadata/serialization stress through the original output boundary.

Only measurement is an explicit software fixture; no actual-output directory,
model, actor or simulator is created. Eight MiB capture hold is a stress input,
not a promised future capture bound or assumed compression credit.
"""
from context import R,C,SOURCE as S,read,put,load,sha
from pathlib import Path
import fcntl,os,sys,types,subprocess,json,traceback
def main():
 assert os.sched_getaffinity(0)=={2}and not(S/'QUOTA_OUTPUT_BOUNDARY_PROOF.json').exists()
 locks=[]
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 import numpy as np
 out=S/'quota_software';out.mkdir(exist_ok=False);oldquota=sys.modules.get('quota');result=dict(passed=False,models=0,renderer_constructors=0,NN_inference=0,physics=0,replay=0,source_once_claimed=False)
 try:
  b=read(S/'BASELINE_DRAFT.json');limits=read(S/'components/SCCR/LIMITS_DRAFT.json')
  grant=load('new_union_actual_granted_quota_fixture',C/'granted_quota.py');boundary=load('new_union_actual_output_boundary_fixture',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');atomic=load('new_union_compact_json_fixture',C/'compact_json.py').atomic;resources=load('new_union_resources_fixture',C/'resources.py')
  def measure(output,unused):
   assert Path(output)==out;own=int(subprocess.check_output(['du','-sx','-B1',str(out)],timeout=10).split()[0]);return own,b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']+own
  grant.base.measure=measure;sys.modules['quota']=types.SimpleNamespace(base=grant.base)
  q=grant.EvidenceQuota(out,limits);q.bind_external_names([]);q.write_enforcement_active=True;resources.reserve_terminal(q)
  initial=resources.prepare(q,'CANONICAL_INITIALIZER_PREPARATION',cap=16*1024**2,ttl=180);q.retire_grant();q.hold('canonical-physical-prefix',8*1024**2)
  old=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual';grants=[];maximum=0;records=0
  def save(name,value):
   nonlocal maximum,records
   q.atomic(out/name,value,atomic);records+=1;maximum=max(maximum,(out/name).stat().st_size)
  with boundary.OutputBoundary(out,q.charge_write):
   for i,k in enumerate([0,5,10]):
    grants.append(resources.prepare(q,'STOPPED_EVENT_PREPARATION'))
    for name in [f'cycle_{i:06d}_origin.json',f'SCCR_DEPTH_{k:06d}.json']:
     save(name,read(old/name))
    save(f'UNION_WIDEST_NUMPY_{k:06d}.json',dict(explicit_synthetic_fixture=True,complete186=np.full(186,np.finfo(np.float32).max,np.float32),base107=np.full(107,-np.finfo(np.float32).max,np.float32),norm_arrays=[np.linspace(0,1,n,dtype=np.float32)for n in [36,32,15,24,15]],passed=np.bool_(True),counts=np.int64(2),residual=np.array([1.,-1.],np.float32)))
    save('PROGRESS.json',dict(explicit_synthetic_fixture=True,constructor_returns=np.int64(2),forward_returns=np.int64(2*(i+1)),inflight=None))
    q.admit((old/'DWA_PREDICTIONS.pack').stat().st_size,'SAVED_COMPLETE_FIVE_PROFILE_BYTE_WIDTH_STRESS_NO_ARRAY_RECONSTRUCTION')
   resources.prepare(q,'COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300)
   q.admit(2*1025904+8192,'SAVED_FULL_STATE_NPLUS1_UNCOMPRESSED_WIDTH_STRESS_NOT_NEW_CAPTURE')
  negatives=[]
  def reject(name,fn):
   try:fn()
   except(AssertionError,ValueError,TypeError):negatives.append(name)
   else:raise AssertionError('SOFTWARE_OUTPUT_NEGATIVE_ACCEPTED:'+name)
  reject('nonfinite_serializer',lambda:atomic(out/'REFUSED_NONFINITE.json',dict(a=np.float64(np.nan))))
  reject('foreign_output_write',lambda:q.charge_write(S/'foreign_output',1))
  reject('invalid_negative_byte_count',lambda:q.charge_write(out/'bad',-1))
  q.retire_grant();q.release('canonical-physical-prefix');q.release(resources.TERMINAL_KEY)
  result.update(passed=True,closed=True,actual_original_grant_and_boundary_used=True,production_census_unchanged=True,software_only_measurement_substitution=True,original_initializer_grant_bytes=initial['capacity_bytes'],stress_capture_hold_bytes=8*1024**2,minimum_grant_capacity_bytes=min(g['capacity_bytes']for g in grants),serialization_records=records,maximum_output_record_bytes=maximum,negative_cases=negatives,actualfuture_capture_bound_not_claimed=True,raw_array_or_model_reconstruction=0,source_SHA256={str(p.relative_to(R)):sha(p)for p in [Path(__file__),C/'granted_quota.py',C/'compact_json.py',C/'resources.py']})
 except BaseException as e:result.update(closed=True,error=repr(e),traceback=traceback.format_exc())
 finally:
  if oldquota is None:sys.modules.pop('quota',None)
  else:sys.modules['quota']=oldquota
 put(S/'QUOTA_OUTPUT_BOUNDARY_PROOF.json',result);print(json.dumps({k:v for k,v in result.items()if k!='source_SHA256'}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
