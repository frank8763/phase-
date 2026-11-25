"""Concrete saved constructor mapping regression plus adversarial classifier."""
from context import R,O,read
from mapping_scope import classify
import os,hashlib
from pathlib import Path

def check():
 pins=read(O/'CONSTRUCTOR_DEPENDENCY_PINS.json')['namespace_ELF_files_SHA256'];saved=read(R/'runs/v1960_rpp_resource_before_guard/AFTER_CONSTRUCTOR_MAPS.json')['new'];ELFs=0;data=0
 for n,row in saved.items():
  if n.startswith('/dev/shm/'):
   # Old capture has exact names/permissions/SHA only; new runtime measures identity/size.
   augmented=dict(row,bytes=4096,uid=os.getuid(),regular=True,symlink=False);magic=b'DATA';data+=1
  else:
   p=R/'runs/v856_nav2_foundation/rootfs'/n.lstrip('/')if n.startswith('/opt/')else Path(n)
   with p.open('rb')as f:magic=f.read(4)
   assert magic==b'\x7fELF'and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];augmented=row;ELFs+=1
  classify(n,augmented,magic,pins,os.getuid())
 assert data==5 and ELFs==125
 row=dict(sha256='a',permissions=['rw-s'],bytes=4096,uid=os.getuid(),regular=True,symlink=False);name='/dev/shm/fastrtps_port7000';assert classify(name,row,b'DATA',{},os.getuid())=='nonexecuting_middleware_shared_data';neg=[]
 cases=[('ELF_disguised_as_SHM',name,row,b'\x7fELF'),('unknown_name','/dev/shm/arbitrary',row,b'DATA'),('bad_hex','/dev/shm/fastrtps_zzzz',row,b'DATA')]
 for k,v in [('permissions',['r-xs']),('permissions',['rw-p']),('bytes',0),('bytes',16*1024**2+1),('uid',os.getuid()+1),('regular',False),('symlink',True)]:cases.append((k+str(v),name,{**row,k:v},b'DATA'))
 for label,n,rr,magic in cases:
  try:classify(n,rr,magic,{},os.getuid())
  except AssertionError:neg.append(label)
  else:raise AssertionError('BAD_MAPPING_ACCEPTED:'+label)
 return dict(passed=True,saved_ELFs_exact_SHA=ELFs,saved_nonELF_names_and_permissions=5,negative_cases=neg,old_SHM_identity_not_captured=True,new_runtime_requires_measured_uid_type_size=True,DLL_loads=0,controller_constructors=0,solver_calls=0)
