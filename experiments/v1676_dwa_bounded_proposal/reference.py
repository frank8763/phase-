"""Pinned PythonRobotics equations plus one explicit Ackermann sample mask."""
import ast,copy,hashlib,types,math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
UP=R/'runs/v1675_dwa_reference_intake/upstream/PathPlanning/DynamicWindowApproach/dynamic_window_approach.py'
FUNCTIONS=['dwa_control','motion','calc_dynamic_window','predict_trajectory','calc_control_and_trajectory','calc_obstacle_cost','calc_to_goal_cost']
def admissible(v,w,maximum_curvature):
 return v>=.005 and abs(w)<=v*maximum_curvature+1e-12
def source_nodes(source):
 assert source[str(UP.relative_to(R))]==hashlib.sha256(UP.read_bytes()).hexdigest(),'DWA_REFERENCE_SOURCE_CHANGED'
 tree=ast.parse(UP.read_text());selected=[];proof={}
 for name in ['RobotType',*FUNCTIONS]:
  node=next(n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name==name);before=ast.dump(node,include_attributes=False);node=copy.deepcopy(node)
  if name=='calc_control_and_trajectory':
   outer=next(n for n in node.body if isinstance(n,ast.For));inner=next(n for n in outer.body if isinstance(n,ast.For))
   assert ast.unparse(outer.iter)=='np.arange(dw[0], dw[1], config.v_resolution)'and ast.unparse(inner.iter)=='np.arange(dw[2], dw[3], config.yaw_rate_resolution)'
   assert ast.unparse(inner.body[0])=='trajectory = predict_trajectory(x_init, v, y, config)'
   inner.body.insert(0,ast.parse("if not _phase_admissible(float(v),float(y),config.maximum_curvature):\n continue").body[0])
   reverted=copy.deepcopy(node);a=next(n for n in reverted.body if isinstance(n,ast.For));b=next(n for n in a.body if isinstance(n,ast.For));b.body.pop(0)
   assert ast.dump(reverted,include_attributes=False)==before,'DWA_OBJECTIVE_OR_SELECTION_CHANGED'
  else:assert ast.dump(node,include_attributes=False)==before
  proof[name]=dict(original_AST_SHA256=hashlib.sha256(before.encode()).hexdigest(),phase_AST_SHA256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),only_Ackermann_sample_mask_added=name=='calc_control_and_trajectory')
  selected.append(node)
 return selected,proof
def bind(np,source,config_data):
 from enum import Enum
 nodes,proof=source_nodes(source);namespace=dict(np=np,math=math,Enum=Enum,_phase_admissible=admissible)
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(UP),'exec'),namespace)
 config=types.SimpleNamespace(**config_data);config.robot_type=namespace['RobotType'].rectangle
 assert config.robot_stuck_flag_cons==0.,'CAR_CANNOT_USE_REFERENCE_IN_PLACE_ROTATION'
 counts=dict(query_attempts=0,query_returns=0,dynamic_window_calls=0,candidate_trajectory_calls=0,candidate_trajectory_returns=0,reference_motion_calls=0,total_modelwork=None)
 for name,key in [('motion','reference_motion_calls'),('calc_dynamic_window','dynamic_window_calls')]:
  original=namespace[name]
  def counted(*a,_original=original,_key=key,**k):counts[_key]+=1;return _original(*a,**k)
  namespace[name]=counted
 original=namespace['predict_trajectory']
 def trajectories(*a,**k):
  counts['candidate_trajectory_calls']+=1;value=original(*a,**k);counts['candidate_trajectory_returns']+=1;return value
 namespace['predict_trajectory']=trajectories
 def query(state,goal,obstacles):
  assert counts['query_attempts']==0,'DWA_QUERY_ONCE_NO_RETRY'
  counts['query_attempts']=1;answer=namespace['dwa_control'](state,config,goal,obstacles);counts['query_returns']=1;return answer
 return query,counts,proof,namespace,config
