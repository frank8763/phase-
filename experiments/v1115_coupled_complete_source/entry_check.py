"""Exact new-mode C++/Python calibration and episode-retaining stop seam."""
import sys,json,ast,ctypes,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1115_coupled_complete_source';sys.path.insert(0,str(C))
import run as driver
import numpy as np
from bindings import Predictor,initial,PARAMETERS,GAIN
from solver import Solver
def main():
 assert not(O/'ENTRY_QUALIFICATION.json').exists()
 component=json.loads((R/'records/nav2_v1114_20261113/COMPONENT_REVIEW.json').read_text());assert component['passed']and component['counts']['new_actual_native']==16200
 x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());seed=json.loads((R/'runs/v1111_sqp_joint_source/OPTIMIZATION.json').read_text())['z'];engine=Solver(x,np.array(pg['path']),pg['gear'],initial_guess=seed)
 fixture=json.loads((R/'experiments/v1114_coupled_steering_mode/STATIC_T0_SOURCE_FIXTURE.json').read_text());cpp_work=0;python_work=0;maximum=0.;episode_differences=[];negative=[]
 def cpp(state,memory,rows,episode=False):
  nonlocal cpp_work
  n=sum(int(r[2])for r in rows);ss=np.empty((n,8));uu=np.empty((n,4));p=engine.parameters.copy();p[10]=float(episode);tt=np.array([r[0]for r in rows]);vv=np.array([r[1]for r in rows]);nn=np.array([r[2]for r in rows],np.int32);mm=np.array([r[3]for r in rows],np.int32)
  code=engine.lib.profile(np.array(state,float),np.array(memory,float),tt,vv,nn,mm,len(rows),np.array(fixture['setup']['limits'],float),np.array(fixture['setup']['slew_per_second'],float),p,ss,uu);work=engine.lib.profile_work();cpp_work+=work
  return code,ss,uu,work
 for sign,name in [(1,'negative_to_positive'),(-1,'positive_to_negative')]:
  rows=[(0.,0.,2200,0),(-sign*.42722137342572125,0.,600,1),(0.,0.,2200,0),(sign*.42722137342572125,0.,600,1),(sign*.42722137342572125,.08,300,0),(0.,0.,2200,0)]
  with np.load(R/'experiments/v1114_coupled_steering_mode'/('PLAN_'+name+'.npz'))as z:saved={k:z[k].copy()for k in z.files}
  code,s,u,work=cpp(saved['states'][0],[0.]*5,rows);assert code==work==8100
  maximum=max(maximum,float(abs(s-saved['states'][1:]).max()),float(abs(u-saved['controls']).max()))
  k=2320;origin=initial(fixture['packet']);origin.update(state=saved['states'][k].copy(),last_ctrl=saved['memory'][k,:4].copy(),integral=float(saved['memory'][k,4]),coupled_episode=True)
  ps,pu,pr,pm,pf,pt,pe=driver.replay_rows(fixture,[(0.,0.,2200,0)],origin);python_work+=2200
  code,cs,cu,work=cpp(origin['state'],np.r_[origin['last_ctrl'],origin['integral']],[(0.,0.,2200,0)],True);assert code==work==2200
  maximum=max(maximum,float(abs(ps[1:]-cs).max()),float(abs(pu-cu).max()))
  code,wrong,_,_=cpp(origin['state'],np.r_[origin['last_ctrl'],origin['integral']],[(0.,0.,2200,0)],False);difference=float(abs(wrong-cs).max());assert code==2200 and difference>1e-7,'COUPLED_STOP_FLAG_NOT_EXERCISED';episode_differences.append(difference)
 for label,rows,state in [('target_cap',[(.5,0.,1,1)],np.zeros(8)),('moving_entry',[(0.,0.,1,1)],np.array([0.,0.,0.,.004,0.,0.,0.,0.])),('zero_tick',[(0.,0.,0,0)],np.zeros(8))]:
  code,_,_,work=cpp(state,[0.]*5,rows);assert code<0 and work==0,label;negative.append(label)
 cs,cu,rows,events=engine.simulate(engine.seed(),reserved_final=True);cpp_work+=engine.native
 ps,pu,*_=driver.replay_rows(x,rows);python_work+=len(pu);maximum=max(maximum,float(abs(cs-ps).max()),float(abs(cu-pu).max()));assert maximum<=1e-8,'QUALIFIED_MODEL_ACCELERATOR_CHANGED'
 generic=Solver(x,np.array(pg['path']),pg['gear']);z=generic.seed();assert z.shape==engine.seed().shape and np.isfinite(z).all();generic_no_history='read_text'not in __import__('inspect').getsource(Solver.seed)
 assert generic_no_history
 refused=[]
 for name in ['mujoco','physical','vehicle','factory','torch','rclpy']:
  try:__import__(name)
  except AssertionError:refused.append(name)
  else:raise AssertionError('PHYSICAL_IMPORT_ALLOWED '+name)
 for p in C.glob('*.py'):ast.parse(p.read_text())
 result=dict(passed=True,maximum_cpp_python_state_ctrl_error=maximum,both_physically_qualified_nominal_profiles_calibrated=True,real_seed_full_source_calibrated=True,coupled_rolling_stop_flag_exercised=True,missing_episode_stop_errors=episode_differences,invalid_cpp_cases_rejected=negative,all_failed_call_work_counted=True,generic_solver_seed_reads_no_saved_trace_or_vector=True,registered_saved_development_seed='V1111 qualified z only for this fixed EW software test',coefficient_frozen_from_V1114=GAIN,analytical_work=dict(cpp_native=cpp_work,python_native=python_work),imports_refused=refused,models=0,physical_integrations=0)
 (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
