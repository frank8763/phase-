"""Explicit software stress fixture through ORIGINAL quota, grants, compact writer and boundary.
No physical/numerical calls. Measurement substitution exists only in this script;
production census/budget functions stay untouched. Synthetic capture hold20MiB
is a stress input, not a theorem bounding future actual capture.
"""
from pathlib import Path
import os,json,subprocess,traceback
from context import R,C,SOURCE as S,read,put,load,sha

def main():
 assert os.sched_getaffinity(0)=={2};out=S/'quota_software02';out.mkdir();result=dict(passed=False,models=0,new_NLP=0,physical_native=0,replay=0,explicit_software_measurement_fixture=True)
 try:
  limits=read(S/'components/PCBF/LIMITS_DRAFT.json');b=read(S/'BASELINE_DRAFT.json')
  grant=load('actual_granted_quota_fixture',C/'granted_quota.py');boundary=load('actual_OutputBoundary_fixture',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');atomic=load('actual_compact_writer_fixture',C/'compact_json.py').atomic;resources=load('actual_grant_stage_fixture',C/'resources.py')
  def measure(output,unused):
   assert Path(output)==out
   own=int(subprocess.check_output(['du','-sx','-B1',str(out)],timeout=10).split()[0])
   return own,b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']+own
  grant.base.measure=measure
  # resources.prepare imports quota.base; bind ONLY fixture module name locally.
  import sys,types
  old=sys.modules.get('quota');sys.modules['quota']=types.SimpleNamespace(base=grant.base)
  q=grant.EvidenceQuota(out,limits);q.bind_external_names([]);q.write_enforcement_active=True
  resources.reserve_terminal(q);resources.prepare(q,'CANONICAL_INITIALIZER_PREPARATION',cap=16*1024**2,ttl=180)
  q.retire_grant();q.hold('canonical-physical-prefix',20*1024**2);grants=[]
  def save(n,v):return q.atomic(out/n,v,atomic)
  oldout=R/'runs/v2151_psf_wrapper_identity_binding/components/PSF/actual';wire=S/'software/PCBF'
  with boundary.OutputBoundary(out,q.charge_write):
   for i in range(100):
    if i%10==0:grants.append(resources.prepare(q,'STOPPED_EVENT_PREPARATION'))
    for suffix in ['WIRE','RESULT']:
     n=f'FILTER_QUERY_{i:03d}_{suffix}.json';save(n,read(wire/n))
    for suffix in ['origin','shadow','admission_0','executed']:
     n=f'cycle_{i:06d}_{suffix}.json';save(n,read(oldout/f'cycle_{5*i:06d}_{suffix}.json'))
    # Exact saved-recipe record bytes stress bounded writes without reconstructing.
    q.admit(2*1024**2,'FIXTURE_NATIVE_AND_COMPLETE_PREDICTIONS_HEADROOM')
   resources.prepare(q,'COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300)
   save('FILTER_NATIVE_CONSOLE.json',read(wire/'FILTER_NATIVE_CONSOLE.json'))
  metadata=__import__('context').metadata().verify_all(out)
  assert len(grants)==10 and metadata['records']==600
  assert q.holds['canonical-physical-prefix']==20*1024**2
  q.retire_grant();q.release('canonical-physical-prefix');q.release(resources.TERMINAL_KEY)
  if old is None:sys.modules.pop('quota',None)
  else:sys.modules['quota']=old
  result.update(passed=True,ordered_queries=100,immutable_records=metadata,stress_capture_hold_bytes=20*1024**2,original_initializer_grant_bytes=16*1024**2,grant_refresh_every_queries=10,minimum_grant_capacity_bytes=min(g['capacity_bytes']for g in grants),stress_fixture_not_future_capture_bound=True,all_new_output_under_original_boundary=True,production_census_not_modified=True)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 result['closed']=True;put(S/'QUOTA_OUTPUT_BOUNDARY_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
