"""Independent full saved-source replay and EVERY8-native complete stop audit."""
import sys,json,time,signal,hashlib,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];JOB=json.loads(Path(sys.argv[1]).read_text());O=Path(JOB['output']);SOURCE=Path(JOB['source'])
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(C));from geometry import Geometry
from source import Engine,initial,python_replay,COUNTS
from recovery_source import forecast_packet
import numpy as np

def main():
 start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('AUDIT1500')));signal.alarm(1500);assert hashlib.sha256(Path(JOB['table']).read_bytes()).hexdigest()==JOB['table_sha256'];x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());x['safe_terminal_pose']=json.loads((R/'runs/v1125_safe_goal_region/TERMINAL_SELECTION.json').read_text())['selected_body_pose'];file=SOURCE/('SELECTED.json'if(SOURCE/'SELECTED.json').exists()else'OPTIMIZATION.json');selection=json.loads(file.read_text());rows=selection['rows'];stored=np.load(SOURCE/'SELECTED_SOURCE.npz');z=np.load(JOB['table']);g=Geometry(x,{k:z[k]for k in ['bounds','centers']});e=Engine(x['setup']);ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);COUNTS['python_native']+=len(pu);error=max(float(abs(ps-stored['states']).max()),float(abs(pu-stored['controls']).max()));assert error<=1e-8,'INDEPENDENT_SOURCE_EVIDENCE_MISMATCH';proof,_=g.final(x,ps,pu,rows);assert proof['passed'],'INDEPENDENT_FULL_SOURCE_PROOF_MISMATCH';backups=[]
 for i in range(0,len(pu)-2200+1,8):
  origin={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};ss,uu=e.simulate(origin,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=g.final(dict(x,packet=packet,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'minimum_timed_raw_m':bp['minimum_timed_raw_m'],'terminal_cycle_raw_m':bp['terminal_full_cycle_raw_m'],'failed_checks':[k for k,v in bp['checks'].items()if not v]})
  if len(backups)%64==0:dump(O/'PARTIAL.json',{'backups':len(backups),'last_native':i,'failures':sum(not b['passed']for b in backups)})
 dump(O/'ALL8_BACKUPS.json',backups);signal.alarm(0);answer={'closed':True,'passed':all(b['passed']for b in backups),'models':0,'physical_integrations':0,'entire_source_independent_error':error,'entire_source_passed':proof['passed'],'backup_stride_native':8,'complete_stop_native':2200,'backup_count':len(backups),'failed_backup_count':sum(not b['passed']for b in backups),'counts':{'independent_python_native':COUNTS['python_native'],'backup_cpp_native':e.native},'wall_s':time.monotonic()-start,'not_physical_acceptance':True};dump(O/'COMPLETION.json',answer);print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
