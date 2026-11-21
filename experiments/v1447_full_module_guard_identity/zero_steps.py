"""Forbid native integration and prediction/control calls, including re-profiling."""
from contextlib import contextmanager
from pathlib import Path
import sys

@contextmanager
def forbid_steps(mj):
 names=('mj_step','mj_step1','mj_step2');originals={name:getattr(mj,name)for name in names}
 original_setprofile=sys.setprofile;previous=sys.getprofile();violations=[]
 def forbidden(*_,**__):
  violations.append('NATIVE_INTEGRATION_ATTEMPT');raise RuntimeError('INITIALIZER_NATIVE_STEPS_FORBIDDEN')
 def guard(frame,event,arg):
  if event=='c_call'and getattr(arg,'__name__','')in names:
   violations.append('NATIVE_C_INTEGRATION_ATTEMPT');raise RuntimeError('INITIALIZER_NATIVE_C_STEPS_FORBIDDEN')
  if event=='call'and Path(frame.f_code.co_filename).is_relative_to(Path(__file__).resolve().parents[2]):
   name=frame.f_code.co_name;file=Path(frame.f_code.co_filename).name
   if(name=='compute'and file in {'coupled_control.py','vehicle_control.py'})or(name in {'step','__init__'}and file in {'coupled_model.py','prediction.py','kernel.py'}):
    violations.append(file+':'+name);raise RuntimeError('INITIALIZER_PREDICTOR_OR_ALLOCATOR_COMPUTE_FORBIDDEN')
 def install(replacement):
  if getattr(replacement,'_initializer_zero_step_guard',False):return original_setprofile(replacement)
  def composed(frame,event,arg):
   guard(frame,event,arg)
   if replacement is not None:replacement(frame,event,arg)
  composed._initializer_zero_step_guard=True;original_setprofile(composed)
 for name in names:setattr(mj,name,forbidden)
 sys.setprofile=install;install(previous)
 try:yield violations
 finally:
  sys.setprofile=original_setprofile;original_setprofile(previous)
  for name,value in originals.items():setattr(mj,name,value)

