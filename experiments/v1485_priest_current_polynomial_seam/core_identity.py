"""Prepare pinned author/core/map identity without importing author code."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
CAPTURE=R/'runs/v1484_baseline_disposition_priest'
COMMIT='4eeb402f7ed576bc39e9bc679fa0c7cd212c7b41'
TREE='4792ffeb6b3d7255452d33fc4fe2093578af6014'
CORE=('priest/src/mpc_non_dy.py','priest/src/bernstein_coeff_order10_arbitinterval.py')
MAP=R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json'

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def exact(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class PreparedCore:
 def __init__(self,*,source_manifest):
  assert source_manifest and all(sha(R/p)==h for p,h in source_manifest.items()),'PRIEST_PREPARATION_SOURCE_CHANGED'
  required=[*C.glob('*.py'),C/'PROTOCOL.md',MAP,R/'experiments/v855_renewal_worker/KNOWN_FIELD.json',*(CAPTURE/'upstream'/p for p in CORE),CAPTURE/'ACQUISITION.json',CAPTURE/'TREE.json']
  required += [R/p for p in ['experiments/v1397_event_handoff_integration/route_event.py','experiments/v1397_event_handoff_integration/causal_bridge_field.py','experiments/v1423_integrated_route_audit/native_step.py','experiments/v1396_rpp_rpc_retirement/frames.py','experiments/v1288_baseline_interface/contract.py']]
  assert all(str(p.relative_to(R))in source_manifest for p in required),'PRIEST_SOURCE_MANIFEST_INCOMPLETE'
  self.sources=copy.deepcopy(source_manifest);self.source_manifest_sha256=digest(self.sources)
  acquisition=read(CAPTURE/'ACQUISITION.json');tree=read(CAPTURE/'TREE.json')
  assert acquisition['commit']==COMMIT and acquisition['tree']==tree['sha']==TREE and not tree['truncated']
  records={x['path']:x for x in acquisition['records']if 'path'in x};members=[]
  for path in CORE:
   p=CAPTURE/'upstream'/path;assert not p.is_symlink()
   raw=p.read_bytes();record=records[path]
   assert len(raw)==record['bytes']and hashlib.sha256(raw).hexdigest()==record['sha256']
   assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==record['git_blob_sha1']
   module=ast.parse(raw.decode('utf-8'),filename=path)
   if path==CORE[0]:
    cls=next(n for n in module.body if isinstance(n,ast.ClassDef)and n.name=='batch_crowd_nav')
    methods={n.name for n in cls.body if isinstance(n,ast.FunctionDef)}
    assert {'compute_projection_sampling','compute_cem','compute_controls','compute_obs_traj_prediction'}<=methods
   members.append(dict(path=path,sha256=record['sha256'],git_blob_sha1=record['git_blob_sha1'],bytes=len(raw)))
  self.public_map=read(MAP);assert self.public_map['source']=='experiments/v855_renewal_worker/KNOWN_FIELD.json'
  assert self.public_map['source_sha256']==sha(R/self.public_map['source'])
  self.public_map_sha256=digest(self.public_map)
  self.value=dict(schema=1,algorithm='ENGINEERING_PRIEST_POLYNOMIAL_PROPOSAL_WITH_PHASE_CURRENT_RESPONSE',scientific_revision=7,author_commit=COMMIT,author_tree=TREE,author_members=members,author_core_class='batch_crowd_nav',author_ROS_wrapper_excluded=True,unmodified_author_whole_system=False,D_PRIEST_car_example_reproduced=False,public_map_sha256=self.public_map_sha256,polynomial_order=10,coefficient_count_per_axis=11,coordinates='REAR_AXLE_WORLD_XY',body_to_rear_offset_m=.3,accepted_actual_control_domain='EMPTY_PENDING_SAME_RESPONSE_ACTUAL_CONTROLLER',optimizer_kwargs_not_yet_qualified=True,initial_boundary='CAUSAL_BACKWARD_ACTUAL_REAR_VELOCITY_SECANT_HINT_NOT_INSTANTANEOUS_ACCELERATION',response_policy='FROZEN_POLYNOMIAL6_DERIVATIVE_AVERAGE_SHORTEST_HEADING_NO_CLIP_ORIGINAL_GEAR_ONCE')
  self.identity_sha256=digest(self.value);self.owner_pid=os.getpid();self.boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  # Only frozen Phase definitions are preloaded. Never load the author module.
  folder=R/'experiments/v1397_event_handoff_integration';sys.path.insert(0,str(folder))
  self.event=__import__('route_event');assert Path(self.event.__file__).resolve()==folder/'route_event.py'
  self.field=exact('v1485_original_causal_coefficients',folder/'causal_bridge_field.py')
  self.native=exact('v1485_original_canonical_native_source',R/'experiments/v1423_integrated_route_audit/native_step.py')

 def hot_identity(self):
  assert self.owner_pid==os.getpid()and self.boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  assert digest(self.value)==self.identity_sha256 and digest(self.sources)==self.source_manifest_sha256,'PREPARED_PRIEST_SOURCE_IDENTITY_CHANGED'
  assert digest(self.public_map)==self.public_map_sha256,'PREPARED_PRIEST_PUBLIC_MAP_CHANGED'
  return self.identity_sha256

 def verify_closure_sources(self):
  assert all(sha(R/p)==h for p,h in self.sources.items()),'PRIEST_CLOSURE_SOURCE_CHANGED'
  return dict(source_manifest_sha256=self.source_manifest_sha256,all_sources_unchanged=True)
