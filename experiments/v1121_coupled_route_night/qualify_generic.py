"""Generic live seed and every125 complete stop; analytical only."""
import sys,json,time,importlib.abc,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from source import solve,python_replay,initial,final_gate,Engine,COUNTS
from recovery_source import forecast_packet
import numpy as np

def main():
 assert not(O/'GENERIC_QUALIFICATION.json').exists();start=time.monotonic();x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());p=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());answer={'passed':False};stops=[];engine=None
 try:
  result=solve(x,p['path'],p['gear']);answer.update(generic_proof=result['proof'],optimizer_exit=result['optimizer_exit'],selected_z=result['selected_z'],rows=result['rows'],generic_source_passed=result['passed']);ss,uu,memory,episodes,active=python_replay(x['setup'],initial(x['packet']),result['rows']);COUNTS['python_native']+=len(uu);error=max(float(abs(ss-result['states']).max()),float(abs(uu-result['controls']).max()));assert error<=1e-8;answer['cpp_python_error']=error;assert result['passed'],'GENERIC_SOURCE_REFUSED'
  np.savez_compressed(O/'GENERIC_SOURCE.npz',states=ss,controls=uu,requests=result['requests'],memory=memory,episodes=episodes,active=active)
  engine=Engine(x['setup'])
  for i in range(0,len(uu)-2200,125):
   origin={'state':ss[i].copy(),'last_ctrl':memory[i,:4].copy(),'integral':float(memory[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};cs,cu=engine.simulate(origin,[(0.,0.,2200,0)]);ps,pu,*_=python_replay(x['setup'],origin,[(0.,0.,2200,0)]);COUNTS['python_native']+=2200;error=max(float(abs(ps-cs).max()),float(abs(pu-cu).max()));assert error<=1e-8;packet=forecast_packet(x['packet'],ss[i],memory[i],i);packet.update(body_lateral=float(ss[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=False);y=dict(x,packet=packet,goal=ps[-1,:2].tolist());proof,_=final_gate(y,ps,pu,[(0.,0.,2200,0)]);stops.append({'offset':i,'passed':proof['passed'],'minimum_raw_m':proof['minimum_raw_m'],'maximum_error':error});assert proof['passed'],'ROLLING_COMPLETE_STOP_REFUSED'
  answer['passed']=True
 except BaseException as e:answer.update(error=repr(e),traceback=traceback.format_exc())
 answer.update(complete_stops=stops,cpp_stop_native=engine.native if engine else 0,analytical_counts=COUNTS,models=0,physical_integrations=0,wall_s=time.monotonic()-start,closed=True,seed_policy='current geometry curvature only, no saved z in live construction');(O/'GENERIC_QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps({k:v for k,v in answer.items()if k not in ['rows','selected_z','complete_stops']}),flush=True)
if __name__=='__main__':main()
