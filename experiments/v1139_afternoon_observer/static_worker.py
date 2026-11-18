"""Use original qualified static response worker with new frozen .12 plans and authority."""
import sys,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C));from afternoon_tools import *
def source():
 s=(R/'experiments/v1114_coupled_steering_mode/worker.py').read_text();s=s.replace('C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))',"C=R/'experiments/v1139_afternoon_observer';sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))")
 s=s.replace('from common import R,O,dump,sha,remaining,source_ok,pin,RESOURCE','from afternoon_tools import R,O,dump,sha,remaining,source_ok,pin,RESOURCE,encode');s=s.replace("runs/v858_nav2_verified/v1114","runs/v858_nav2_verified/v1139");s=s.replace('8100','8000');s=s.replace('from execution import applied_step,complete_stop_source,execute_complete_stop','from static_execution import applied_step,complete_stop_source,execute_complete_stop');s=s.replace('print(json.dumps(', 'print(encode(')
 return s

def module():
 m=types.ModuleType('afternoon_static_worker');m.__file__=str(C/'static_worker.py');m.R=R;exec(compile(source(),str(C/'static_worker.py'),'exec'),m.__dict__);return m
if __name__=='__main__':sys.exit(module().main())
