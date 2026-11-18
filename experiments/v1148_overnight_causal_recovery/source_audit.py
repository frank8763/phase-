"""Separate saved-source admission, all complete stops independently recomputed."""
from primitives import *
import signal
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'))
from geometry import Geometry
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from fast_cycle import certify as cycle_certify
from recovery_source import forecast_packet

if __name__=='__main__':
 profile=json.loads(Path(sys.argv[1]).read_text());assert profile in json.loads((C/'PROFILES.json').read_text());out=Path(profile['output']);r=json.loads((out/'RESULT.json').read_text());assert r['passed'];signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('INDEPENDENT_SOURCE_AUDIT600')));signal.alarm(min(600,max(1,int(remaining()-15))))
 selected=json.loads((out/'SELECTED.json').read_text());x=selected['input'];rows=selected['rows'];stored=np.load(out/'SOURCE.npz');table=np.load(O/'actual_source/JOINT_TABLE.npz');g=Geometry(x,{k:table[k]for k in ['bounds','centers']});engine=Engine(x['setup']);origin=initial(x['packet']);ss,uu=engine.simulate(origin,rows);ps,pu,memory,episodes,active=python_replay(x['setup'],origin,rows);python_work=len(pu);maximum=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()),float(abs(stored['states']-ss).max()),float(abs(stored['controls']-uu).max()),float(abs(stored['memory']-memory).max()));assert maximum<=1e-8
 proof,_=g.final(x,ss,uu,rows);assert proof['passed']and proof['goal_upper_m']<=.45
 saved=json.loads((out/'ALL8_BACKUPS.json').read_text());nodes=sorted(set(list(range(0,len(pu)-2200+1,8))+[len(pu)-2200]));assert nodes==[row['native']for row in saved]and saved
 maximum_stop_error=0.
 for i,record in zip(nodes,saved):
  assert remaining()>10
  inp=dict(state=ps[i],last_ctrl=memory[i,:4],integral=float(memory[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bs,bu=engine.simulate(inp,[(0.,0.,2200,0)]);bsp,bup,*_=python_replay(x['setup'],inp,[(0.,0.,2200,0)]);python_work+=2200;maximum_stop_error=max(maximum_stop_error,float(abs(bs-bsp).max()),float(abs(bu-bup).max()));assert maximum_stop_error<=1e-8
  p=forecast_packet(x['packet'],ps[i],memory[i],i);p.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bx=dict(x,packet=p,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist());bp=cycle_certify(bx,bs,bu,[(0.,0.,2200,0)])
  if not bp['passed']:bp,_=g.final(bx,bs,bu,[(0.,0.,2200,0)])
  assert bp['passed']and bp['states_sha256']==record['states_sha256']and bp['controls_sha256']==record['controls_sha256']
 dump(out/'FINAL_INDEPENDENT_AUDIT.json',dict(passed=True,full_source_reconstructed=True,all8_complete_stops=len(nodes),full_source_error=maximum,all_stop_error=maximum_stop_error,analytical_cpp_native=engine.native,independent_python_native=python_work,models=0,physical_native=0,original_goal_physical_passed=False));signal.alarm(0)
