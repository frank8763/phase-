"""One substantive fresh-measurement control integration; all preludes before Source."""
from context import R,C,SOURCE as S,O,read,put,sha,remaining,predecessors_closed
from pathlib import Path
import ast,os,gzip,io,tarfile,json
P=R/'runs/v2177_priest_vector_orientation'
EXCLUDED={'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}
def candidate():
 old=read(P/'SOURCE_FREEZE.json')['files'];files=dict(old)
 for root in [C,R/'experiments/v2178_projection_trajectory_readout',R/'experiments/v2179_current_plan_cursor']:
  for p in root.glob('*'):
   if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for root in [S,R/'runs/v2178_projection_trajectory_readout',R/'runs/v2179_current_plan_cursor']:
  for p in root.glob('*.json'):
   if p.name not in EXCLUDED:files[str(p.relative_to(R))]=sha(p)
 for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json','OWNER_CLOSED.json','LAUNCH_IDENTITY.json','components/MATH/RESULT.json','components/MATH/COMPLETION.json','components/MATH/OWNED_CHILD.json','components/MATH/POST_MATH_STORAGE_BARRIER.json','runtime_archives/MATH/ARCHIVE_INDEX.json','runtime_archives/MATH/FULL_REMOTE_VERIFIED.json','runtime_archives/MATH/TRANSPORT_CLEANUP.json']:
  files[str((P/n).relative_to(R))]=sha(P/n)
 for p in O.glob('*.json'):files[str(p.relative_to(R))]=sha(p)
 for n in ['docs/ORIENTATION_PROJECTION_V2177_V2178_RESULT.md','docs/CURRENT_PLAN_CURSOR_V2179_V2180_PREPARATION.md']:files[n]=sha(R/n)
 return old,files

def check(require_auth=False):
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists()and not(S/'DISPATCH_ONCE.json').exists()
 assert predecessors_closed()and all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 from reserved_census import admission,idle
 handles=idle();budget=admission()
 for n in ['FRESH_PROBLEM_SOFTWARE.json','HANDSHAKE_SOFTWARE.json','PEER_BODY_SOFTWARE.json','SOCKET_PIPELINE_SOFTWARE.json','SOFTWARE_SNAPSHOT_RECONCILIATION.json','CLIENT_SOFTWARE.json','NAVIGATION_SOFTWARE.json','IO_PIPELINE_SOFTWARE.json','CHEAP_INTERFACE_PROOF.json','FINAL_SEAMS.json','ROOT_NAMESPACE_PROOF.json']:
  assert read(S/n)['passed'],n
 assert read(R/'runs/v2179_current_plan_cursor/PROOF_SCHEMA_SUPPLEMENT.json')['passed']
 import evidence
 assert evidence.P==P and evidence.CASES=={'PROJ':'PROJ'}
 for rid in [None,'PROJ']:compile(evidence.deliver(rid,preview=True),'fresh_projection_delivery','exec')
 task=read(O/'PILOT_TASK.json');locked=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=next(x['task']for x in locked['tasks']if x['task']['task_id']=='common_01')
 for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[k]==original[k]
 assert task['method']=='ORIENTATION_PROJECTION_CP_V1'and task['maximum_control_native']==120 and task['maximum_plans']==49 and task['maximum_current_native_queries']==1 and not task['formal_common_task']
 assert read(O/'LIMITS_DRAFT.json')==read(R/'runs/v2176_sccr_common_plant_component/components/SCCR/LIMITS_DRAFT.json')
 for p in C.glob('*.py'):ast.parse(p.read_text())
 old,files=candidate();assert all(sha(R/n)==h for n,h in files.items());delta={n:h for n,h in files.items()if old.get(n)!=h}
 # Exact candidate-only compression rehearsal in memory, no archive claim/file.
 buffer=io.BytesIO()
 with gzip.GzipFile(fileobj=buffer,mode='wb',compresslevel=3,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as tar:
  for name in sorted(delta):
   raw=(R/name).read_bytes();i=tarfile.TarInfo(name);i.size=len(raw);tar.addfile(i,io.BytesIO(raw))
 compressed=len(buffer.getvalue());assert compressed+256*1024<2*1024**2,'SOURCE_ARCHIVE_CAPACITY'
 if require_auth:assert remaining(read(S/'AUTHORIZATION.json'))>6900
 return dict(passed=True,source_members=len(files),delta_members=len(delta),candidate_archive_rehearsal_compressed_bytes=compressed,source_archive_reserved_bytes=2*1024**2,models_NLP_physics_Source=0,scope='ORIENTATION_PROJECTION_CP_COMPONENT',original_physical_audit_gates_unchanged=True,original_safety_modules_byte_exact=read(S/'CHEAP_INTERFACE_PROOF.json')['byte_identical_safety_physical_capture_replay_modules'],budget=budget,all_cheap_preflights_before_source_clock=True)
if __name__=='__main__':x=check();put(S/'PRE_SOURCE_PREFLIGHT.json',x);print(json.dumps(x))
