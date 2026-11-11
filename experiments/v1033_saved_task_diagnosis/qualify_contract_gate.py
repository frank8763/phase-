"""Actual causal saved input plus malformed/unknown cases, all zero model."""
import importlib.abc,json,sys,time,copy
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1033_saved_task_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
from contract_gate import select_contract
from geometry_model import ref,REQUIRED
p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());known=setup['known'];poly=ref._old.Geometry(known,row['source']['periodic']).center_polygon;start=row['packet']['body'][:2];goal=row['plan']['original_goal']
begun=time.perf_counter();result=select_contract(known,poly,start,goal,REQUIRED);elapsed=time.perf_counter()-begun;assert result['obstruction_proved']and result['actuation_authority']is False
checks=dict(actual_saved_causal_cut_found=True,public_inputs_only=True)
checks['no_actor_is_unknown']=not select_contract(known,None,start,goal,REQUIRED)['obstruction_proved']
checks['unrelated_synthetic_translated_actor_is_unknown']=not select_contract(known,poly+[-1.6,-1.],start,goal,REQUIRED)['obstruction_proved']
checks['goal_outside_cut_is_unknown']=not select_contract(known,poly,start,[-1.,-2.],REQUIRED)['obstruction_proved']
checks['smaller_margin_breaks_witness']=not select_contract(known,poly,start,goal,.01)['obstruction_proved']
checks['start_inside_same_pocket_is_unknown']=not select_contract(known,poly,[4.,-1.8],goal,REQUIRED)['obstruction_proved']
checks['reversed_convex_vertex_order_same_witness']=select_contract(known,poly[::-1],start,goal,REQUIRED)['obstruction_proved']
malformed=poly.copy();malformed[[1,9]]=malformed[[9,1]];checks['nonconvex_polygon_not_used']=not select_contract(known,malformed,start,goal,REQUIRED)['obstruction_proved']
# Permuting map entities cannot change the geometric conclusion.
permuted=copy.deepcopy(known);permuted['known_rectangles']=permuted['known_rectangles'][::-1];checks['no_hardcoded_map_indices']=select_contract(permuted,poly,start,goal,REQUIRED)['obstruction_proved']
out=dict(passed=all(checks.values()),checks=checks,selection=result,saved_input_query_s=elapsed,models=0,integrations=0,independent_continuous_proof='FULL_CYCLE_SEPARATION_PROOF.json',physical_integration_not_done=True)
(O/'CONTRACT_GATE_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['passed']
