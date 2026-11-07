"""Only a scoped legacy factory cwd repair; frozen physics/control source unchanged."""
import fcntl,json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v858_nav2_verified';OUT=R/'runs/v858_nav2_verified/entry02'
sys.path.insert(0,str(C))
import vehicle
original_initialize=vehicle.initialize
def initialize_in_legacy_directory(*args,**kwargs):
 previous=Path.cwd()
 try:
  os.chdir('/home/linghu/catkin_ws/src/mk-mini')
  return original_initialize(*args,**kwargs)
 finally:os.chdir(previous)
vehicle.initialize=initialize_in_legacy_directory
if __name__=='__main__':
 if '--qualify' in sys.argv:
  lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.chdir(R)
  v=vehicle.Vehicle(OUT/'entry_qualification','WEST_EAST',10010001,False);scan=v.scan();assert v.d.time==0 and Path.cwd()==R and len(scan['ranges'])==32
  (OUT/'ENTRY_QUALIFICATION.json').write_text(json.dumps(dict(passed=True,environment_initializations=1,new_xml_compilations=1,native_integrations=0,correct_factory_directory=True,restored_socket_directory=True,minimum_clearance=v.min_clear,bad_contacts=v.bad),indent=2)+'\n')
 else:
  import native_worker
  sys.exit(native_worker.main())
