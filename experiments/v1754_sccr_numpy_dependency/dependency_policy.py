"""Permit only exact NumPy ctypes bootstrap; never authorize another dynamic library."""
import hashlib,importlib.abc,sys,time
from pathlib import Path

def verify_pins(spec):
 for name,expected in spec['files_SHA256'].items():
  p=Path(name);assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected,'NUMPY_DEPENDENCY_CHANGED:'+name
 return len(spec['files_SHA256'])

def allow_ctypes(event,args,phase,caller,expected,prior_process_loads):
 # CPython ctypes initializes pythonapi=PyDLL(None) once. No named library,
 # symbol address, retry, or subsequent application loader call is admitted.
 return event=='ctypes.dlopen' and tuple(args)==(None,) and phase=='NUMPY_IMPORT' and caller==expected and prior_process_loads==0

def qualify():
 expected='/exact/ctypes/__init__.py';assert allow_ctypes('ctypes.dlopen',(None,),'NUMPY_IMPORT',expected,expected,0)
 cases=[('ctypes.dlopen',('libunsafe.so',),'NUMPY_IMPORT',expected,0),('ctypes.dlopen',(None,),'QUERY',expected,0),('ctypes.dlopen',(None,),'SOURCE',expected,0),('ctypes.dlopen',(None,),'NUMPY_IMPORT','/wrong/caller',0),('ctypes.dlopen',(None,),'NUMPY_IMPORT',expected,1),('ctypes.dlsym',(None,'foo'),'NUMPY_IMPORT',expected,0),('ctypes.call_function',(123,()),'QUERY',expected,0)]
 for event,args,phase,caller,count in cases:assert not allow_ctypes(event,args,phase,caller,expected,count),'DEPENDENCY_SCOPE_NEGATIVE_ACCEPTED'
 return len(cases)

class Bootstrap(importlib.abc.MetaPathFinder):
 def __init__(self,spec):
  self.spec=spec;self.phase='BEFORE_IMPORT';self.process_loads=0;self.events=[];self.started=None;self.import_wall_s=None;self.import_returned=False;self.identities={}
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'ctypes','_ctypes'}:
   assert self.phase=='NUMPY_IMPORT' and name in {'ctypes','ctypes._endian','_ctypes'},'CTYPES_IMPORT_OUTSIDE_NUMPY_BOOTSTRAP:'+name
 def audit(self,event,args):
  if not event.startswith('ctypes.'):return
  caller=str(Path(sys._getframe(1).f_code.co_filename).resolve())
  allowed=allow_ctypes(event,args,self.phase,caller,self.spec['ctypes_init'],self.process_loads)
  self.events.append(dict(event=event,phase=self.phase,caller=caller,process_handle_only=event=='ctypes.dlopen'and tuple(args)==(None,),allowed=allowed))
  assert allowed,'UNAUTHORIZED_CTYPES_EVENT:'+event
  self.process_loads+=1
 def numpy_import(self):
  assert self.phase=='BEFORE_IMPORT' and 'numpy'not in sys.modules and 'ctypes'not in sys.modules,'NUMPY_NOT_FRESH'
  verify_pins(self.spec);self.phase='NUMPY_IMPORT';self.started=time.monotonic();sys.meta_path.insert(0,self)
  try:
   import numpy as np
   expected={'numpy':self.spec['numpy_package']+'/__init__.py','numpy._core._internal':self.spec['numpy_package']+'/_core/_internal.py','ctypes':self.spec['ctypes_init'],'_ctypes':self.spec['ctypes_extension']}
   for name,path in expected.items():
    module=sys.modules[name];actual=Path(module.__file__).resolve();assert actual==Path(path).resolve() and hashlib.sha256(actual.read_bytes()).hexdigest()==self.spec['files_SHA256'][path],'RESIDENT_DEPENDENCY_IDENTITY:'+name
    self.identities[name]=dict(path=str(actual),sha256=self.spec['files_SHA256'][path])
   self.import_returned=True;return np
  finally:self.import_wall_s=time.monotonic()-self.started;self.phase='QUERY_SEALED'
 def record(self):
  return dict(numpy_import_returned=self.import_returned,numpy_import_wall_s=self.import_wall_s,ctypes_process_handle_loads=self.process_loads,ctypes_audit_events=self.events,resident_identities=self.identities,arbitrary_library_or_symbol_admission=False,internal_numpy_native_calls_unknown=True,ctypes_audit_not_a_complete_native_call_counter=True,external_dependency_file_count=len(self.spec['files_SHA256']),external_environment_not_archived_by_pin_JSON=True)
