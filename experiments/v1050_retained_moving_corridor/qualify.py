"""Production executor/audit interface exercise; synthetic future is NOT physics."""
import ast,importlib.abc,subprocess,sys,tempfile
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(Path(__file__).resolve().parent))
from kernel import *
from execute import execute,regenerate
from audit import audit_native
def main():
 plan=json.loads((O/'SELECTED_PLAN.json').read_text());ss=np.asarray(plan['state_path']);rr=np.asarray(plan['planned_body_requests']);uu=np.asarray(plan['predicted_actuator_controls']);checks_={};negative=[]
 class Plant:
  def __init__(self,offset=None):self.count=0;self.offset=offset
  def step(self,*request):assert np.array_equal(request,rr[self.count]);self.count+=1
  def body(self):
   q=ss[self.count].copy()
   if self.offset and self.count==3:q[self.offset[0]]+=self.offset[1]
   return [*q[:4],q[5]]
  def steering_sample(self):
   q=ss[self.count].copy()
   if self.offset and self.count==3 and self.offset[0]==6:q[6]+=self.offset[1]
   k=math.tan(q[6])/.6;return np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k)),0.,0.])
 assert execute(Plant(),plan,time.time()+300)['passed'];checks_['whole_production_executor']=True
 for name,offset in [('position',(0,.041)),('heading',(2,.036)),('steering',(6,.016))]:
  try:execute(Plant(offset),plan,time.time()+300)
  except AssertionError:negative.append(name)
  else:raise AssertionError('UNREJECTED '+name)
 H=R/'runs/v1047_day_relay_20261111/inputs/history';setup=json.loads((H/'physics/SETUP.json').read_text());packet=json.loads((O/'INPUT_SOURCE.json').read_text())['packet'];regenerate(setup,packet,plan);checks_['actual_entry_profile_regeneration']=True;z=dict(np.load(H/'physics/NATIVE_TRACE.npz'));commands=json.loads((H/'physics/BODY_COMMANDS.json').read_text());n=len(rr);q=np.repeat(z['qpos'][-1:],n,axis=0);q[:,:2]=ss[1:,:2];q[:,3:7]=np.c_[np.cos(ss[1:,2]/2),np.zeros((n,2)),np.sin(ss[1:,2]/2)];k=np.tan(ss[1:,6])/.6;q[:,setup['steering_qpos_addresses']]=np.c_[np.arctan(.6*k/(1-.27*k)),np.arctan(.6*k/(1+.27*k))];u=np.repeat(z['ctrl'][-1:],n,axis=0);u[:,setup['actuator_ids']]=uu
 fixture=dict(qpos=np.vstack([z['qpos'],q]),qvel=np.vstack([z['qvel'],np.zeros((n,z['qvel'].shape[1]))]),ctrl=np.vstack([z['ctrl'],u]),clearance=np.r_[z['clearance'],np.full(n,.3)],self_margin=np.r_[z['self_margin'],np.full(n,.01)]);commands+= [[0.,*rr[i,:2],ss[i,3],ss[i,5],float(rr[i,2])]for i in range(n)]
 raw=R/'runs/v858_nav2_verified/v1050';raw.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=raw,prefix='software_fixture_')as folder:
  out=Path(folder);(out/'physics').mkdir();np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**fixture);r=dict(passed=True,completed_native=len(commands),own_replay_native=len(commands),actual_original_goal_reached=True,historical_replay_maximum_error=0.,physical=dict(fully_recorded_native=len(commands),root_guard_native_count=len(commands),bad_contacts=0),replay=dict(passed=True,maximum_qpos_qvel_ctrl_mocap_error=0.))
  for name,value in [('physics/SETUP.json',setup),('physics/BODY_COMMANDS.json',commands),('RESULT.json',r),('FRESH_PLAN.json',plan)]:dump(out/name,value)
  task=dict(output=str(out));proof=audit_native(task,True);assert proof['passed'],proof;checks_['production_saved_native_audit_interface']=True;fixture['qpos'][23643,0]+=.041;np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**fixture);assert not audit_native(task,True)['passed'];negative.append('saved_qpos_tamper')
 for name in ['full_worker','driver','watchdog','close','start']:load('v1050_qualification_'+name,C/(name+'.py'))
 checks_['production_modules_import_under_model_ban']=True
 p=subprocess.run([str(R/'run_phase.sh'),'experiments/v1050_retained_moving_corridor/full_worker.py',str(C/'TASK_full_main.json'),str(O/'NO_AUTHORITY.json')],cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr;checks_['actual_entry_guard_blocks_unapproved']=True
 for path in C.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
 checks_['all_sources_parse']=True;checks_['outputs_new']=all(not Path(t['output']).exists()for t in json.loads((C/'FULL_TASKS.json').read_text()));assert checks_['outputs_new'];assert HARD_END==1794400200.;checks_['root_deadline_not_extended']=True
 dump(O/'QUALIFICATION.json',dict(passed=all(checks_.values()),checks=checks_,rejected_negative_cases=negative,synthetic_interface_fixture_only=True,new_mjb_audit=False,models=0,integrations=0));print(json.dumps(dict(passed=True,checks=checks_,negative=negative,models=0)))
if __name__=='__main__':main()
