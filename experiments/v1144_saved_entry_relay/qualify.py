"""Execute THE actual worker saved-entry AST branch on the real failed packet."""
import sys,ast,copy,tempfile,importlib.abc
from evening_tools import *
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import initial

def main():
 assert not(O/'DRIVER_STARTED.json').exists();parent=R/'runs/v1142_evening_observer';closed=json.loads((parent/'COMPLETION.json').read_text());assert closed['closed']and closed['physical_counts']['new_observer_component_native']==0
 p=json.loads((R/'runs/v1143_saved_entry_preparation/RECONSTRUCTED_ACTUAL_PACKET.json').read_text());expected=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text())['packet'];tree=ast.parse((C/'observer_worker.py').read_text());nodes=[n for n in ast.walk(tree)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='dump'and n.value.args and 'SAVED_ENTRY_COMPARISON.json'in ast.unparse(n)];assert len(nodes)==1,'ACTUAL_COMPARISON_CALLSITE_NOT_FOUND';code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(C/'observer_worker.py'),'exec');negative=[]
 def call(packet):
  with tempfile.TemporaryDirectory(dir=O,prefix='actual_entry_fixture_')as folder:
   namespace={'p':packet,'x':{'packet':expected},'initial':initial,'out':Path(folder),'dump':dump};exec(code,namespace);return json.loads((Path(folder)/'SAVED_ENTRY_COMPARISON.json').read_text())
 proof=call(p);assert proof['passed']and proof['maximum_state_error']==0 and proof['maximum_controller_error']==0 and proof['integral_error']==0
 for name,change in [('position',lambda z:z['body'].__setitem__(0,z['body'][0]+.001)),('heading',lambda z:z['body'].__setitem__(2,z['body'][2]+.001)),('speed',lambda z:z['body'].__setitem__(3,z['body'][3]+.001)),('steering',lambda z:z['steering']['position'].__setitem__(0,z['steering']['position'][0]+.001)),('memory',lambda z:z['controller_memory']['last_ctrl'].__setitem__(0,z['controller_memory']['last_ctrl'][0]+.001)),('integral',lambda z:z['controller_memory'].__setitem__('integral',z['controller_memory']['integral']+.001)),('nonfinite',lambda z:z['body'].__setitem__(0,float('nan')))]:
  q=copy.deepcopy(p);change(q)
  try:call(q)
  except AssertionError:negative.append(name)
  else:raise AssertionError('TAMPER_ACCEPTED '+name)
 for name in ['observer_worker','observer_audit','post_observation','goal_source','physical','campaign','watchdog']:
  assert load('qualified_actual_saved_relay_'+name,C/(name+'.py')) is not None
 for f in C.glob('*.py'):ast.parse(f.read_text())
 # Actual output-parent and strict report/result encoding, not just imports.
 for folder in [O,O/'software']:
  with tempfile.TemporaryDirectory(dir=folder,prefix='output_fixture_')as tmp:
   q=Path(tmp)/'RESULT.json';dump(q,{'passed':np.bool_(True),'nested':{'no':np.bool_(False)}});assert json.loads(q.read_text())['passed']
 original=json.loads((R/'experiments/v1142_evening_observer/SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/path)==h for path,h in original.items());w=(parent/'ROUND_WINDOW.json').read_bytes();assert json.loads(w)['absolute_deadline_unix']==1794661200.
 result={'passed':True,'actual_worker_AST_comparison_branch_executed':True,'real_V1142_saved_packet_green':proof,'negatives_rejected':negative,'all7_lazy_actual_entries_imported':True,'output_parent_and_final_encoder_checked':True,'parent_failed_and_source_preserved':True,'no_deadline_extension':True,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0};dump(O/'ENTRY_QUALIFICATION.json',result);print(encode(result))
if __name__=='__main__':main()
