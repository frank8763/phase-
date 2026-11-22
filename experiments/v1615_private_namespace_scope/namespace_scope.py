"""Own the original cold definition aliases while the canonical owner pauses.

Only original loader COLLISION_NAMES are parked, after exact frozen source
validation. Resident module objects/globals are retained, never rewritten.
Fresh private modules are retained as objects and installed only in an owned
scope. Original loader import/code/parameter identity checks remain mandatory.
No model constructor, state write, physics step or fresh-source authority here.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sys
import threading
import types
R=Path(__file__).resolve().parents[2]
MARKER='phase_v1615_owned_private_definition_namespace'
MISSING=object()

class Bank:
 def __init__(self,*,source,definitions):
  self.source=dict(source);self.names=tuple(definitions.COLLISION_NAMES)
  assert self.names and len(set(self.names))==len(self.names)
  assert MARKER not in sys.modules,'PRIVATE_NAMESPACE_OTHER_OWNER_ACTIVE'
  self.owner=os.getpid(),threading.get_ident();self.depth=0;self.failed=False;self.primary=None
  self.actual={n:sys.modules.get(n,MISSING)for n in self.names}
  self.private=None;self.activations=0;self.last_restore_verified=False
  self.actual_sources={n:self.identity(m)for n,m in self.actual.items()if m is not MISSING}

 def identity(self,module):
  assert isinstance(module,types.ModuleType),'PRIVATE_NAMESPACE_UNBOUND_MODULE_OBJECT'
  filename=getattr(module,'__file__',None)
  assert filename is not None,'PRIVATE_NAMESPACE_UNBOUND_MODULE_FILE'
  p=Path(filename);assert p.is_absolute()and p.resolve().is_relative_to(R),'PRIVATE_NAMESPACE_SOURCE_OUTSIDE_PHASE'
  relative=str(p.resolve().relative_to(R));assert relative in self.source,'PRIVATE_NAMESPACE_UNREGISTERED_SOURCE'
  identity=hashlib.sha256(p.read_bytes()).hexdigest()
  assert identity==self.source[relative],'PRIVATE_NAMESPACE_SOURCE_CHANGED'
  return dict(path=relative,sha256=identity)

 def check_actual(self):
  assert self.owner==(os.getpid(),threading.get_ident()),'PRIVATE_NAMESPACE_OWNER_CHANGED'
  assert not self.failed,'PRIVATE_NAMESPACE_NOT_RETRIED_AFTER_FAILURE'
  assert MARKER not in sys.modules,'PRIVATE_NAMESPACE_OTHER_OWNER_ACTIVE'
  for name,module in self.actual.items():
   assert sys.modules.get(name,MISSING)is module,'PRIVATE_NAMESPACE_RESIDENT_IDENTITY_CHANGED:'+name
   if module is not MISSING:assert self.identity(module)==self.actual_sources[name]

 @contextmanager
 def activate(self):
  if self.depth:
   assert self.owner==(os.getpid(),threading.get_ident())and getattr(sys.modules.get(MARKER),'bank',None)is self
   assert not self.failed,'PRIVATE_NAMESPACE_POISONED_SCOPE'
   self.depth+=1
   try:yield self
   except BaseException as error:
    self.failed=True;self.primary=self.primary or error;raise
   finally:self.depth-=1
   return
  try:self.check_actual()
  except BaseException as error:self.failed=True;self.primary=self.primary or error;raise
  self.depth=1;self.last_restore_verified=False
  marker=types.ModuleType(MARKER);marker.__file__=__file__;marker.bank=self
  original_path=list(sys.path);first=None;mutated=False
  try:
   for name in self.names:sys.modules.pop(name,None)
   mutated=True;sys.modules[MARKER]=marker
   if self.private is not None:
    for name,module in self.private.items():
     self.identity(module);sys.modules[name]=module
   self.activations+=1
   yield self
   if self.failed:raise self.primary or AssertionError('PRIVATE_NAMESPACE_POISONED_SCOPE')
  except BaseException as error:
   first=error;self.failed=True;self.primary=self.primary or error;raise
  finally:
   try:
    if mutated:
     # Capture only the old loader's explicitly owned aliases. Source/code
     # proof from that unchanged loader is checked by the caller as before.
     fresh={n:sys.modules[n]for n in self.names if n in sys.modules}
     for module in fresh.values():self.identity(module)
     if self.private is None:self.private=fresh
     else:assert fresh==self.private,'PRIVATE_NAMESPACE_ALIAS_SET_CHANGED'
   except BaseException as error:
    self.failed=True
    if first is not None:first.secondary=repr(error)
    else:first=error
   finally:
    # Restoration is attempted independently of private proof failures.
    try:
     if mutated:
      for name in self.names:sys.modules.pop(name,None)
      for name,module in self.actual.items():
       if module is not MISSING:sys.modules[name]=module
      matching=sys.modules.get(MARKER)is marker
      if matching:sys.modules.pop(MARKER,None)
     sys.path[:]=original_path
     if mutated:assert matching,'PRIVATE_NAMESPACE_MARKER_CHANGED'
     assert all(sys.modules.get(n,MISSING)is m for n,m in self.actual.items())
     self.last_restore_verified=True
    except BaseException as error:
     self.failed=True
     if first is not None:first.secondary_namespace_restore=repr(error)
     else:first=error
    finally:self.depth=0
   if first is not None and sys.exc_info()[0]is None:raise first

 def proof(self):
  return dict(scope='SOURCE_BOUND_MODULE_OWNERSHIP_ONLY',activations=self.activations,
   actual_aliases=self.actual_sources,private_aliases=None if self.private is None else{n:self.identity(m)for n,m in self.private.items()},
   canonical_resident_objects_restored=self.last_restore_verified,failed=self.failed,
   first_error=None if self.primary is None else repr(self.primary),
   model_or_physical_permission=False,actual_state_reset=False,parameters_modified=False)
