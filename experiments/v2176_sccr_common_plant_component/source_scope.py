"""Immutable source-hash authority metadata, no old evidence content is cached."""
from pathlib import Path
from types import MappingProxyType
import os,hashlib
PROTECTED=frozenset({'NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','ACTUAL_CAUSAL_ENTRY_INPUT.json'})
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
class SourceScope:
 def __init__(self,root):self.root=Path(root);self._binding=None;self._files=None
 def verify(self,files,*,binding,initialization_started):
  assert isinstance(files,dict)and all(isinstance(n,str)and isinstance(h,str)and len(h)==64 for n,h in files.items())
  assert type(binding)is tuple and len(binding)==3 and all(isinstance(x,str)and len(x)==64 for x in binding)
  identity=(os.getpid(),Path('/proc/sys/kernel/random/boot_id').read_text().strip(),*binding)
  if self._binding is None:
   assert not initialization_started,'SOURCE_BOOTSTRAP_AFTER_INITIALIZER_FORBIDDEN'
   assert all(sha(self.root/n)==h for n,h in files.items()),'SOURCE_BOOTSTRAP_HASH_CHANGED'
   self._files=MappingProxyType(dict(files));self._binding=identity
  else:
   assert identity==self._binding,'SOURCE_BOOTSTRAP_AUTHORITY_CHANGED'
   assert dict(self._files)==files,'SOURCE_BOOTSTRAP_MANIFEST_CHANGED'
   assert all(sha(self.root/n)==h for n,h in files.items()if Path(n).name not in PROTECTED),'RUNTIME_READABLE_SOURCE_HASH_CHANGED'
  # Plain fresh dict for existing JSON/digest consumers, metadata strings only.
  return dict(self._files)
