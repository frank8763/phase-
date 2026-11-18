"""Actual whole-history/new-component audit fixture and causal-control negatives; zero dynamics."""
import sys,math,tempfile,importlib.abc
from afternoon_tools import *
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import numpy as np
sys.path.insert(0,str(C));from observer_audit import audit

def main():
 assert not(O/'ROUND_WINDOW.json').exists();src=R/'runs/v1138_backup_corridor';d={k:v.copy()for k,v in np.load(src/'REFUGE_SOURCE.npz').items()};rows=json.loads((src/'REFUGE_ROWS.json').read_text());ss=d['states'];uu=d['controls'];mem=d['memory'];n=len(uu);base=20160;total=base+n;oldroot=R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST';history={k:v.copy()for k,v in np.load(oldroot/'physics/NATIVE_TRACE.npz').items()};setup=json.loads((oldroot/'physics/SETUP.json').read_text());entry=json.loads((oldroot/'COUPLED_ENTRY.json').read_text())['packet'];oldcmd=json.loads((oldroot/'physics/BODY_COMMANDS.json').read_text());task=json.loads((C/'OBSERVER_TASK.json').read_text());targets=[];speeds=[];modes=[]
 for target,v,k,m in rows['rows']:targets.extend([target]*int(k));speeds.extend([v]*int(k));modes.extend([bool(m)]*int(k))
 q=np.tile(history['qpos'][base-1],(n,1));vel=np.zeros((n,history['qvel'].shape[1]));q[:,:2]=ss[1:,:2];q[:,3:7]=0;q[:,3]=np.cos(ss[1:,2]/2);q[:,6]=np.sin(ss[1:,2]/2);k=np.tan(ss[1:,6])/.6;q[:,setup['steering_qpos_addresses'][0]]=np.arctan(.6*k/(1-.27*k));q[:,setup['steering_qpos_addresses'][1]]=np.arctan(.6*k/(1+.27*k));vel[:,0]=ss[1:,3]*np.cos(ss[1:,2])-ss[1:,4]*np.sin(ss[1:,2]);vel[:,1]=ss[1:,3]*np.sin(ss[1:,2])+ss[1:,4]*np.cos(ss[1:,2]);vel[:,5]=ss[1:,5];kd=(1+np.tan(ss[1:,6])**2)/.6*ss[1:,7]
 for side,addr in zip([1,-1],setup['steering_qvel_addresses']):vel[:,addr]=.6*kd/((1-side*.27*k)**2+(.6*k)**2)
 ctrl=np.zeros((n,history['ctrl'].shape[1]));ctrl[:,setup['actuator_ids']]=uu;trace={k:np.concatenate([history[k][:base],value])for k,value in [('qpos',q),('qvel',vel),('ctrl',ctrl),('clearance',np.full(n,.3)),('self_margin',np.full(n,.01))]};trace['mocap_pos']=np.concatenate([history['mocap_pos'][:base],np.tile(history['mocap_pos'][base-1],(n,1,1))]);trace['mocap_quat']=np.concatenate([history['mocap_quat'][:base],np.tile(history['mocap_quat'][base-1],(n,1,1))]);cmd=oldcmd[:base]+[[0.,speeds[i],0. if modes[i]or speeds[i]==0 else speeds[i]*math.tan(targets[i])/.6,float(ss[i,3]),float(ss[i,5]),False]for i in range(n)];journal=[{'native':base+i,'component_index':i,'mode':modes[i],'target':targets[i],'speed':speeds[i],'last_ctrl':mem[i,:4].tolist(),'integral':float(mem[i,4]),'phase':'final_stop'if i>=12500 else'observation_prefix'}for i in range(n)];cert=[{'current':{'passed':True},'prospective':{'passed':True}}];result={'passed':True,'new_actual_native':total,'own_replay_native':total,'replay':{'passed':True},'physical':{'root_guard_native_count':total,'bad_contacts':0},'original_goal_reached':False,'actual_new_observations':1}
 with tempfile.TemporaryDirectory(dir=O,prefix='observer_audit_fixture_')as folder:
  out=Path(folder);(out/'physics').mkdir();soft=out/'software';soft.mkdir();np.savez_compressed(soft/'SOURCE.npz',states=ss,controls=uu);dump(soft/'ROWS.json',rows);local=dict(task,output=str(out))
  for p,v in [('RESULT.json',result),('physics/SETUP.json',setup),('physics/BODY_COMMANDS.json',cmd),('MODE_JOURNAL.json',journal),('STOP_CERTIFICATES.json',cert),('ACTUAL_SAVED_ENTRY.json',entry)]:dump(out/p,v)
  def put():np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
  put();proof=audit(local,False,soft);dump(O/'OBSERVER_AUDIT_FIXTURE_PROOF.json',proof);assert proof['passed'],proof;negatives=0
  trace['ctrl'][base+500,setup['actuator_ids'][2]]+=.01;put();assert not audit(local,False,soft)['passed'];trace['ctrl'][base+500,setup['actuator_ids'][2]]-=.01;negatives+=1
  trace['qpos'][100,0]+=.01;put();assert not audit(local,False,soft)['passed'];trace['qpos'][100,0]-=.01;negatives+=1
  put();cert[0]['current']['passed']=False;dump(out/'STOP_CERTIFICATES.json',cert);assert not audit(local,False,soft)['passed'];negatives+=1
 result={'passed':True,'whole_historical_plus_refuge_saved_audit_positive':True,'negative_cases':negatives,'synthetic_fixture_only_not_new_model_or_actual_response':True,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0};dump(O/'OBSERVER_AUDIT_QUALIFICATION.json',result);print(encode(result))
if __name__=='__main__':main()
