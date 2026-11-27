"""Admit exact installed dependency bytes, including lazily imported Torch code."""
from common import R,S,read,sha
from pathlib import Path
import importlib.abc,importlib.machinery
class PinnedLibraries(importlib.abc.MetaPathFinder):
 def __init__(self):
  a=read(S/'ENVIRONMENT_READINESS.json');self.pins=dict(a['loaded_python_file_sha256'],**a['loaded_native_library_sha256']);self.pins.update(read(S/'ENVIRONMENT_LAZY_DEPENDENCIES.json')['python_or_native_files']);late=read(S/'LAZY_IMPORT_READINESS.json');self.pins.update(late['loaded_python_file_sha256']);self.pins.update(late['loaded_native_library_sha256'])
 def find_spec(self,fullname,path=None,target=None):
  spec=importlib.machinery.PathFinder.find_spec(fullname,path)
  if spec and spec.origin and '/site-packages/'in spec.origin:
   p=Path(spec.origin).resolve();assert str(p)in self.pins,'UNPINNED_SCCR_LIBRARY:'+str(p);assert sha(p)==self.pins[str(p)],'SCCR_LIBRARY_SOURCE_CHANGED:'+str(p)
  return None
