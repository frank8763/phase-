"""Exact inherited frozen actor body, new physical-sensor source authority."""
from context import R,C,SOURCE,O,read,sha,admission
from pathlib import Path
import ast,copy,io,json,zipfile,os,sys,importlib.abc,importlib.machinery
ORIGINAL=R/'experiments/v2165_sccr_dual_actor_component/actors.py'
ENV=R/'runs/v2165_sccr_dual_actor_component'
def authority():
 task=read(O/'PILOT_TASK.json');a,w,files=admission(task)
 assert task['scope']=='SCCR_FRESH_LIVE_UNION_ZERO_ACTUATION_COMPONENT'and task['maximum_control_native']==10 and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert not(O/'COMPLETION.json').exists(),'CLOSED_UNION_POLICY_NOT_REUSABLE'
 for name in ['ENVIRONMENT_READINESS.json','LAZY_IMPORT_READINESS.json']:
  e=read(ENV/name)
  for field in ['loaded_python_file_sha256','loaded_native_library_sha256']:
   for path,h in e[field].items():assert sha(path)==h,'FROZEN_ACTOR_HOST_DEPENDENCY_CHANGED'
 return a,files
class PinnedLibraries(importlib.abc.MetaPathFinder):
 def __init__(self):
  e=read(ENV/'ENVIRONMENT_READINESS.json');self.pins=dict(e['loaded_python_file_sha256'],**e['loaded_native_library_sha256']);self.pins.update(read(ENV/'ENVIRONMENT_LAZY_DEPENDENCIES.json')['python_or_native_files']);e=read(ENV/'LAZY_IMPORT_READINESS.json');self.pins.update(e['loaded_python_file_sha256']);self.pins.update(e['loaded_native_library_sha256'])
 def find_spec(self,n,path=None,target=None):
  spec=importlib.machinery.PathFinder.find_spec(n,path)
  if spec and spec.origin and '/site-packages/'in spec.origin:
   p=Path(spec.origin).resolve();assert str(p)in self.pins and sha(p)==self.pins[str(p)],'UNPINNED_OR_CHANGED_UNION_POLICY_DEPENDENCY:'+str(p)
  return None
# Execute only the original literal specifications and exact class body, no
# actor/network construction at module import. SOURCE checks this AST identity.
tree=ast.parse(ORIGINAL.read_text());nodes=[copy.deepcopy(n)for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='FrozenActor'or isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SPECS'for t in n.targets)]
assert len(nodes)==2
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ORIGINAL),'exec'),globals())
