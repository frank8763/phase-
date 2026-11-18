"""Same qualified recorder/main/gates, fixed-prefix search declared explicitly."""
import sys,json,time,traceback,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1131_final_section_restore'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
spec=importlib.util.spec_from_file_location('restore_original_recording_flow',R/'experiments/v1130_timed_recording_continuation/run.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
sys.path.insert(0,str(C));from restore import Solver

def load_main(output=O):
 m=entry.load_main(output);m.C=C;m.Solver=Solver;return m

def main():
 assert not(O/'DRIVER_STARTED.json').exists();dump(O/'DRIVER_STARTED.json',{'pid':__import__('os').getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time(),'physical_models_authorized':False,'scope':'saved warm-start final-section diagnostic'});m=load_main()
 try:m.main()
 except BaseException as e:
  error={'error':repr(e),'traceback':traceback.format_exc(),'models':0,'physical_integrations':0};dump(O/'OUTER_ERROR.json',error)
  if not(O/'COMPLETION.json').exists():dump(O/'COMPLETION.json',{'closed':True,'passed':False,'scientific_verdict':None,'error':error,'counts':None,'models':0,'physical_integrations':0})
  raise
if __name__=='__main__':main()
