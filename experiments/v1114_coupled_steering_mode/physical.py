"""Reuse original static plant, qualified CPU factory, no physical changes."""
import importlib.util,sys
from common import R
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def create(out,task):
 sys.path.insert(0,str(R/'experiments/v858_nav2_verified'))
 import vehicle
 cpu=load('v1114_cpu_factory',R/'experiments/v1067_causal_replan_brake_reserve/factory.py')
 arena=load('v1114_original_static_arena',R/'experiments/v855_renewal_worker/arena.py')
 canonical=load('v1114_original_canonical_physical',R/'experiments/v1020_terminal_two_route_development/physical.py')
 old=vehicle.initialize;oldf=sys.modules.get('factory');olda=sys.modules.get('arena')
 vehicle.initialize=cpu.initialize;sys.modules['factory']=cpu;sys.modules['arena']=arena
 try:return canonical.create_vehicle(out,task)
 finally:
  vehicle.initialize=old
  for key,value in [('factory',oldf),('arena',olda)]:
   if value is None:sys.modules.pop(key,None)
   else:sys.modules[key]=value
def replay(v,end,out):
 return load('v1114_original_control_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay(v,end,out)
