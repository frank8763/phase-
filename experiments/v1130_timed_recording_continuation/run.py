"""Operation-only continuation; exact immutable V1128 science and main flow."""
import sys,types,importlib.util,json,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1130_timed_recording_continuation';OLD=R/'experiments/v1128_timed_terminal_source'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump,scalar

def load_main(output=O):
 sys.path.insert(0,str(OLD));spec=importlib.util.spec_from_file_location('unchanged_v1128_main_flow',OLD/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.C=C;m.O=Path(output);m.dump=dump
 def normalized_dumps(value,**kwargs):return json.dumps(value,default=scalar,allow_nan=False,**kwargs)
 m.json=types.SimpleNamespace(loads=json.loads,dumps=normalized_dumps);return m

def main():
 assert not(O/'DRIVER_STARTED.json').exists();dump(O/'DRIVER_STARTED.json',{'pid':__import__('os').getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time(),'physical_models_authorized':False});m=load_main()
 try:m.main()
 except BaseException as e:
  error={'error':repr(e),'traceback':traceback.format_exc(),'models':0,'physical_integrations':0,'science_unchanged':True};dump(O/'OUTER_RECORDING_ERROR.json',error)
  if not(O/'COMPLETION.json').exists():dump(O/'COMPLETION.json',{'closed':True,'passed':False,'scientific_verdict':None,'reason':'Unexpected operation error, preserve exact existing OPTIMIZATION counters if available','error':error,'counts':None,'models':0,'physical_integrations':0,'no_physical_launch':True})
  raise
if __name__=='__main__':main()
