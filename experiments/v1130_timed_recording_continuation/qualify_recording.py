"""Exercise original main optimization/error/completion recording with fixtures."""
import sys,json,hashlib,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1130_timed_recording_continuation';sys.path.insert(0,str(C))
from run import load_main,dump
import numpy as np
class FixtureSolver:
 def __init__(self,*args,**kwargs):self.native=17;self.calls=1;self.in_call=False;self.optimizer_exit={'status':0};self.failure=False
 def solve(self):return {'z':np.array([1.]),'constraints':{'restoration_targets_met':np.bool_(False)}},[]
 def simulate(self,*args,**kwargs):return np.zeros((2,8)),np.zeros((1,4)),[(0.,0.,2200,0)],[]
class ErrorFixture(FixtureSolver):
 def solve(self):raise RuntimeError('INJECTED_RECORDING_PATH_ERROR')

def main():
 before=hashlib.sha256((R/'experiments/v1128_timed_terminal_source/run.py').read_bytes()).hexdigest();results=[]
 for name,cls in [('record_numpy_proof',FixtureSolver),('record_exception',ErrorFixture)]:
  out=O/name;out.mkdir();(out/'QUALIFICATION.json').write_text('{"passed":true}\n');m=load_main(out);m.Solver=cls;m.final_gate=lambda *args:({'passed':False,'checks':{'safe_terminal_position':np.bool_(False),'safe_terminal_heading':np.bool_(True)},'mode_envelopes':[]},np.zeros((1,3)));m.main();completion=json.loads((out/'COMPLETION.json').read_text());assert completion['closed']and not completion['passed']and completion['counts']['optimizer_cpp_native']==17;assert completion['models']==completion['physical_integrations']==0
  if name=='record_numpy_proof':assert (out/'OPTIMIZATION.json').exists()and completion['error']is None
  else:assert 'INJECTED_RECORDING_PATH_ERROR'in completion['error']['error']and(out/'ERROR.json').exists()
  results.append({'case':name,'passed':True,'scope':'synthetic recording path only, no solver or dynamics'})
 assert before==hashlib.sha256((R/'experiments/v1128_timed_terminal_source/run.py').read_bytes()).hexdigest();answer={'passed':True,'actual_immutable_main_flow_recording_cases':results,'original_scientific_sources_unchanged':True,'physical_models':0,'physical_integrations':0,'analytical_dynamics_integrations':0,'real_solver_calls':0};dump(O/'RECORDING_FLOW_QUALIFICATION.json',answer);print(json.dumps(answer))
if __name__=='__main__':main()
