"""Real ROS import qualification; no vehicle or navigation, no candidate mutation."""
import ast,hashlib,importlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v911_periodic_causal_navigation';O=R/'runs/v912_startup_dependency_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical'}:raise RuntimeError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import ros_worker
# Match real bridge construction order before examining lazy imports.
sys.path.insert(0,str(C));import motion_publisher
sys.path.insert(0,str(C));import dynamic_proxy
# Imported production workers add exactly their original dependency paths.
names=set()
for file in ['ros_bridge.py','motion_publisher.py','dynamic_proxy.py','supervise.py']:
 tree=ast.parse((C/file).read_text())
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom)and n.module:names.add(n.module)
  elif isinstance(n,ast.Import):names.update(x.name for x in n.names)
missing=[];loaded={}
for name in sorted(names):
 try:m=importlib.import_module(name);loaded[name]=getattr(m,'__file__',None)
 except ImportError as e:missing.append(dict(module=name,error=repr(e)))
assert [r['module']for r in missing]==['map_readiness','refuge_logic'],missing
# refuge_logic belongs to an unreachable legacy branch (refuge_mode=False),
# still resolve it explicitly for complete direct-import inventory.
spec=importlib.util.spec_from_file_location('refuge_logic',R/'experiments/v907_recovery_corridor_memory/refuge_logic.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy);sys.modules['refuge_logic']=legacy
# Prepare only explicit compatibility-module preload. Original scientific source
# remains frozen. This probe does not authorize or launch any resumed model.
path=R/'experiments/v909_timed_command_contract/map_readiness.py'
spec=importlib.util.spec_from_file_location('map_readiness',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.modules['map_readiness']=m
from types import SimpleNamespace as NS
import numpy as np
message=NS(metadata=NS(size_x=1000,size_y=1000,resolution=.01,origin=NS(position=NS(x=-5.,y=-5.))),header=NS(frame_id='map'),data=np.where(m.STATIC,254,0).astype(np.uint8).ravel().tolist())
checks=dict(missing_dependency_reproduced=True,all_other_direct_and_lazy_ros_imports_loaded=len(loaded)==len(names)-2,original_map_module_positive=m.inspect_map(message)['passed'])
message.data=[255]*1000000;checks['unknown_master_rejected']=not m.inspect_map(message)['passed']
message.data=[0]*1000000;checks['missing_static_master_rejected']=not m.inspect_map(message)['passed']
message.metadata.size_x=999;checks['wrong_dimensions_rejected']=not m.inspect_map(message)['passed']
from handshake import verify_sources
verify_sources(R,C/'SOURCE_FREEZE.json');checks['v911_frozen_source_unchanged']=True
result=dict(passed=all(checks.values()),checks=checks,missing=missing,loaded=loaded,compatibility_module_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),models=0,integrations=0,navigation_goals=0,scope='All direct/lazy imports in four actual ROS policy modules and real readiness positive/negative checks. Not full startup lifecycle proof, not physical validation, no resumed authority.')
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='loaded'}));assert result['passed']
