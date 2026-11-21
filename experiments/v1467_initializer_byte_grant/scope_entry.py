"""Only new initializer grant phase and chunked XML byte admission."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1464_canonical_ready_handoff';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('INITIALIZER_GRANT_ENTRY_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='INITIALIZER_PREWRITE_BYTE_GRANT_AND_XML_CHUNKS'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('INITIALIZER_GRANT_ENTRY_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negatives=[]
 io=exact('v1467_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1467_current_scope',C/'contract.py')
 def rejected(label,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError,FileNotFoundError):negatives.append(label);return
  raise AssertionError('INITIALIZER_GRANT_NEGATIVE_ACCEPTED:'+label)
 try:
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   prior=contract.read(FO/'SCOPE_QUALIFICATION.json');assert prior['passed']and prior['models']==prior['physical_native']==0
   oldfrozen=contract.read(FO/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in oldfrozen.items())
   unchanged=[]
   for p in sorted(C.glob('*.py')):
    if p.name in {'scope_entry.py','quota.py','lifecycle.py'}:continue
    restored=p.read_text().replace('v1467_initializer_byte_grant','v1464_canonical_ready_handoff').replace('v1467','v1464')
    assert ast.dump(ast.parse(restored))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_GRANT_CHANGE:'+p.name;unchanged.append(p.name)
   old_quota=R/'experiments/v1449_route_initializer_binding/quota.py';qsource=(C/'quota.py').read_text().replace(",'CANONICAL_INITIALIZER_PREPARATION'",'').replace("else(180 if phase=='CANONICAL_INITIALIZER_PREPARATION'else 2)","else 2")
   assert ast.dump(ast.parse(qsource))==ast.dump(ast.parse(old_quota.read_text())),'GRANT_CHANGED_BEYOND_EXPLICIT_PHASE_AND_TTL'
   life_source=(C/'lifecycle.py').read_text().replace('v1467_initializer_byte_grant','v1464_canonical_ready_handoff').replace('v1467','v1464')
   life_source=life_source.replace("quota_module=exact('v1464_actual_initializer_grant_quota',N/'quota.py')","quota_module=exact('v1432_actual_pre_wire_byte_quota',C/'quota.py')")
   line="   evidence_quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=180,external_writers=evidence_quota.external_writers)\n"
   assert line in life_source;life_source=life_source.replace(line,'')
   assert ast.dump(ast.parse(life_source))==ast.dump(ast.parse((F/'lifecycle.py').read_text())),'LIFECYCLE_CHANGED_BEYOND_INITIALIZER_GRANT'
   life=exact('v1467_exact_scope_lifecycle',C/'lifecycle.py');sup=exact('v1467_once_supervisor',C/'supervisor.py')
   rejected('native_missing_newscope_admission',lambda:life.run(task,{},{}));rejected('once_missing_newscope_admission',lambda:sup.launch('first_event'))
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);qmodule=exact('v1467_exact_initializer_grant',C/'quota.py');boundary=exact('v1467_exact_frozen_boundary',C/'bounded_io.py')
   folder=O/'software_XML';folder.mkdir();quota=qmodule.EvidenceQuota(folder,limits);quota.bind_external_names([]);quota.external_writers=[];quota.write_enforcement_active=True
   # There are no children in this software scope: reserve the complete56MiB
   # future role caps as holds, do not forge live writer/source metadata.
   caps=contract.read(C/'WRITER_CAPS.json');assert sum(caps.values())==56*1024**2
   for role,cap in caps.items():quota.hold('future_external:'+role,cap)
   original_used=qmodule.base.used;calls=[]
   def counted(path):calls.append(str(path));return original_used(path)
   qmodule.base.used=counted;emissions=[]
   def charge(path,n):emissions.append(dict(path=str(path.relative_to(folder)),bytes=n));return quota.charge_write(path,n)
   try:
    with boundary.OutputBoundary(folder,charge):
     proof=quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=180,external_writers=[])
     prewire=len(calls);assert prewire==2 and proof['maximum_held_bytes']==sum(quota.holds.values())
     tree=ET.ElementTree(ET.Element('mujoco'))
     for i in range(100):ET.SubElement(tree.getroot(),'geom',dict(name='software_geom_'+str(i),size='.1 .2 .3',description='中文 only software XML'))
     expected=ET.tostring(tree.getroot(),encoding='unicode');path=folder/'CHUNKED_SOFTWARE.xml';tree.write(path,encoding='unicode')
     assert path.read_text()==expected and len(calls)==prewire,'HOT_INITIALIZER_XML_TRIGGERED_FULL_RUNS_DU'
     emitted=sum(row['bytes']for row in emissions if row['path']==path.name);assert emitted==8192+len(expected.encode())
     assert len(emissions)>100 and quota.grant['remaining_bytes']==16*1024**2-emitted
     quota.grant['expires_monotonic']=time.monotonic()-1;rejected('expired_initializer_grant',lambda:quota.charge_write(folder/'expired',1))
     quota.retire_grant()
     rejected('initializer_ttl_cannot_expand',lambda:quota.prepare_grant(4096,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=181,external_writers=[]))
     quota.prepare_grant(4096,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=180,external_writers=[])
     rejected('initializer_capacity_before_write',lambda:(folder/'TOO_LARGE.xml').write_text('x'*4097));assert not(folder/'TOO_LARGE.xml').exists()
     quota.retire_grant();quota.write_enforcement_active=False
   finally:qmodule.base.used=original_used
   storage=sup.budget.storage_preflight(limits)
   inherited=dict(oldfrozen);inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negatives,entry_gates=prior['entry_gates'],external_writer_hook_qualification=prior['external_writer_hook_qualification'],writer_source_proofs=prior['writer_source_proofs'],source_hashes=inherited,storage_preflight=storage,reused_ready_scope_entry_SHA=contract.sha(FO/'SCOPE_QUALIFICATION.json'),normalized_unchanged_production_files=unchanged,initializer_grant_phase_and_TTL_only_quota_change=True,initializer_prepare_only_lifecycle_change=True,all_external_future_caps_held_bytes=sum(caps.values()),live_child_metadata_not_forged=True,XML_write_chunks=len(emissions),full_du_calls_before_XML=prewire,full_du_calls_during_XML=0,actual_write_bytes_including_open_overhead=emitted,lossless_XML_roundtrip=True,init180_and_originalscience_unchanged=True,old_runtime_failure_retained=True,whole_route_admission=False,live_event_runtime_passed=False,source_remote_recovery_still_required=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1
