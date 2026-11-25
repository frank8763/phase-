"""Saved actual mapping feedback loop; no DLL/constructor/solver."""
from context import R,O,read,put,load
import hashlib,time

def main():
 start=time.monotonic();scope=load('rpp_exact_scope',__import__('pathlib').Path(__file__).with_name('dependency_scope.py'));inputs=read(O/'INPUT_BINDING.json');maps=read(R/'runs/v1946_rpp_transitive_tls_dependencies/NATIVE_LOADED_MAPS_BEFORE_VALIDATION.json')['new'];allowed=inputs['namespace_ELF_files_SHA256'];kinds={};baseline=[]
 for name,row in maps.items():
  p=R/'runs/v856_nav2_foundation/rootfs'/name.lstrip('/')if name.startswith('/opt/ros/')else __import__('pathlib').Path(name)
  if name in scope.WAIT_FILES:magic=b'WAIT';row={**row,'permissions':['rw-s']}
  else:
   with p.open('rb')as f:magic=f.read(4)
   assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
  kinds[name]=scope.validate_new_mapping(name,row,magic,allowed)
  if magic==b'\x7fELF'and name not in read(R/'runs/v1946_rpp_transitive_tls_dependencies/INPUT_BINDING.json')['namespace_ELF_files_SHA256']:baseline.append(name)
 assert len(baseline)==11 and len(kinds)==91
 negatives=[]
 examples=[('unknown_ELF','/unknown/lib.so',{'sha256':'a'*64},b'\x7fELF',{}),('changed_ELF','/pin.so',{'sha256':'a'*64},b'\x7fELF',{'/pin.so':'b'*64}),('ELF_named_wait',next(iter(scope.WAIT_FILES)),{'sha256':'a'*64},b'\x7fELF',{}),('unknown_nonELF','/dev/shm/other',{'permissions':['rw-s']},b'WAIT',{}),('executable_wait',next(iter(scope.WAIT_FILES)),{'permissions':['r-xs']},b'WAIT',{}),('missing_permissions',next(iter(scope.WAIT_FILES)),{},b'WAIT',{})]
 for label,name,row,magic,pins in examples:
  try:scope.validate_new_mapping(name,row,magic,pins)
  except AssertionError:negatives.append(label)
  else:raise AssertionError('BAD_MAPPING_ACCEPTED:'+label)
 put(O/'INVENTORY_SOFTWARE_RESULT.json',dict(passed=True,closed=True,saved_mappings=91,ELFs=89,non_executable_wait_files=2,saved_prior_inventory_missing_ELFs=baseline,negative_cases=negatives,models=0,DLL_loads=0,controller_constructors=0,solver_calls=0,wait_classification_saved_permissions_not_captured=True,real_load_requires_measured_permissions=True,wall_s=time.monotonic()-start))
 print('PASS saved91/ELF89; prior11 missing; six negative mapping cases; no DLL')
if __name__=='__main__':main()
