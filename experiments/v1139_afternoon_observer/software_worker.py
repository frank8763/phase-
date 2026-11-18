"""Original stop contract at fixed refuge; every8 complete backups, no physical models."""
import sys,signal,importlib.abc,time
from afternoon_tools import *
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1138_backup_corridor'));import corridor_tools as t
np=t.np;Engine=t.Engine;Geometry=t.Geometry;initial=t.initial;python_replay=t.python_replay;forecast_packet=t.forecast_packet

def main():
 out=O/'software';start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE600')));signal.alarm(min(600,max(1,int(remaining()-120))));engine=None;error=None;backups=[];passed=False;proof=None;err=None;partial=False;python_native=0
 try:
  assert source_ok();x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());tab=np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz');g=Geometry(x,{k:tab[k]for k in ['bounds','centers']});src=R/'runs/v1136_route_clock_restore/dynamic_seed_v120';j=json.loads((src/'OPTIMIZATION.json').read_text());old=np.load(src/'SELECTED_SOURCE.npz');cut=12500;anchor=old['states'][cut,:3].copy();rows=t.prefix(j['rows'],cut);assert 1.65<=anchor[0]<=1.95 and -1.6<=anchor[1]<=-1.2 and -1.1<=anchor[2]<=-.5;engine=Engine(x['setup']);partial=True;ss,uu=engine.simulate(initial(x['packet']),rows);partial=False;cx=dict(x,goal=anchor[:2].tolist(),safe_terminal_pose=anchor.tolist());proof,_=g.final(cx,ss,uu,rows);assert abs(ss[:cut+1]-old['states'][:cut+1]).max()<=1e-8 and abs(uu[:cut]-old['controls'][:cut]).max()<=1e-8;dump(out/'SOURCE_PROOF.json',proof);ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);python_native=len(pu);err=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert err<=1e-8,'INDEPENDENT_MODEL_MISMATCH';np.savez_compressed(out/'SOURCE.npz',states=ps,controls=pu,memory=mem,coupled=episodes,active=active);dump(out/'ROWS.json',{'rows':rows,'cut':cut,'component_goal':anchor,'original_goal':x['goal'],'original_goal_reached':False})
  if proof['passed']:
   nodes=[*range(0,cut+1,8),cut]
   for i in sorted(set(nodes)):
    assert remaining()>60;origin={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};partial=True;bs,bu=engine.simulate(origin,[(0.,0.,2200,0)]);partial=False;packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=g.final(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'minimum_raw_m':bp['minimum_raw_m'],'cycle_terminal_raw_m':bp['terminal_full_cycle_raw_m'],'failed_checks':[k for k,v in bp['checks'].items()if not v],'states_sha256':sha_array(bs),'controls_sha256':sha_array(bu)})
    if len(backups)%64==0:dump(out/'PARTIAL.json',{'backups':len(backups),'last_native':i,'failed':sum(not r['passed']for r in backups),'analytical_cpp_native':engine.native})
   dump(out/'ALL8_BACKUPS.json',backups);passed=bool(backups and all(r['passed']for r in backups))
 except BaseException as e:
  import traceback
  error={'error':repr(e),'traceback':traceback.format_exc()};dump(out/'ERROR.json',error)
 finally:signal.alarm(0)
 result={'closed':True,'passed':passed and error is None,'source_proof':proof,'maximum_independent_error':err,'backup_count':len(backups),'failed_backups':sum(not b['passed']for b in backups),'counts':{'analytical_cpp_native':engine.native if engine else 0,'cpp_inflight_work_unknown':partial,'independent_python_native':python_native},'error':error,'models':0,'physical_integrations':0,'original_goal_reached':False,'wall_s':time.monotonic()-start};dump(out/'RESULT.json',result);print(encode(result));return 0 if error is None else 1

def sha_array(a):return hashlib.sha256(a.tobytes()).hexdigest()
if __name__=='__main__':sys.exit(main())
