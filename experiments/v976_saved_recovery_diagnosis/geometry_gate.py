"""Two fixed saved causal states, full-cycle geometric alternative only. No dynamics."""
import importlib.abc,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v976_saved_recovery_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v968_rpp_closed_loop_night'))
import corridor_search as graph
assert Path(graph.__file__).resolve()==R/'experiments/v968_rpp_closed_loop_night/corridor_search.py'
graph.WALL_S=20. # Explicit smaller zero-model diagnostic cap, not a scientific threshold change.
x=json.loads((O/'RECOVERY_INPUTS.json').read_text());answers=[]
for i,row in enumerate(x['rows']):
 packet=row['search_packet'];source=row['search_source'];start=packet['body'][:3]
 before=time.monotonic();res=graph.search(start,[4.,-2.],x['known'],source['periodic'])
 answers.append(dict(fixed_index=i,source_tick=source['source_native_tick'],body_tick=packet['native_tick'],original_static_path_passed=row['proposal']['static_route']['passed'],old_prefix_status=row['proposal']['status'],old_prefix_goal_progress_m=row['proposal'].get('available_goal_progress_m',row['proposal'].get('nominal_goal_progress_m')),new_full_cycle_geometry=res,wall_s=time.monotonic()-before))
 (O/'GEOMETRY_GATE_PARTIAL.json').write_text(json.dumps(dict(completed=len(answers),models=0,integrations=0),indent=2)+'\n')
result=dict(models=0,integrations=0,private_dynamics_predictions=0,analytical_searches=2,max_wall_s_each=20,original_safety_threshold=.155,spatial_reserve_unchanged=graph.SPATIAL,interpolation_reserve_unchanged=graph.GAP,results=answers,scope='Same saved causal periodic polytope included in every reference edge, rather than static route then truncation. No actual tracking/arrival or mathematical completeness claim; finite budget.')
(O/'GEOMETRY_GATE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**{k:v for k,v in result.items()if k!='results'},'summary':[dict(index=a['fixed_index'],passed=a['new_full_cycle_geometry']['passed'],status=a['new_full_cycle_geometry']['status'],expanded=a['new_full_cycle_geometry'].get('expanded'),wall_s=a['wall_s'])for a in answers]},indent=2))
