"""Production saved-audit positive/negative qualification, zero physical APIs."""
import sys,json,math,ast,importlib.abc,importlib.util,tempfile,subprocess,copy
from common import C,R,O,dump
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
import numpy as np
from logic import kernel,response_passed,ERROR_LIMIT,measured_rest,ready_to_drive
sys.path.insert(0,str(C))
from audit import audit
from campaign import permitted,command
from execution import applied_step,execute_complete_stop,complete_stop_source
from logic import Adapter,SteeringModeRefusal
def main():
 assert not(O/'ENTRY_QUALIFICATION.json').exists()
 checks={};refused=[];tasks=json.loads((C/'TASKS.json').read_text());fixture=json.loads((C/'STATIC_T0_SOURCE_FIXTURE.json').read_text());setup=fixture['setup']
 from fixture_contract import validate_task,validate_actual
 assert validate_task(tasks[0],fixture)and validate_actual(tasks[0],fixture,setup,setup['model_sha256'])
 checks['actual_saved_static_contract']=True
 # Actual saved refusal input: retained strict entry rejects, an explicitly
 # entered motion mode accepts the measured drift under its new envelope.
 rejected_body=json.loads((R/'records/nav2_v1113_20261113/SAVED_PREFIX_REVIEW.json').read_text());mv=rejected_body['actual_last_longitudinal_m_s'];mw=.052071769438645485
 meta=kernel.Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),kernel.PARAMETERS).adapter;meta.__class__=Adapter;meta.parked_target=-.42722137342572125
 try:meta.compute(0.,0.,mv,mw,False)
 except SteeringModeRefusal:refused.append('actual_drift_cannot_enter_steering')
 else:raise AssertionError('MOVING_ENTRY_ACCEPTED')
 meta.compute(0.,0.,0.,0.,False);meta.compute(0.,0.,mv,mw,False);checks['bounded_motion_handles_old_refusal']=True
 class Plant:
  def __init__(self):self.adapter=meta;self.count=0;self.requests=[];self.speed=.011
  def body(self):return [0.,0.,0.,self.speed,0.]
  def step(self,v,w,stale):self.adapter.compute(v,w,self.speed,0.,stale);self.count+=1;self.requests.append((v,w));self.speed=0.
 plant=Plant();journal=[];rejected=[];before=meta.last.copy()
 try:applied_step(plant,[0.,0.],True,-.42722137342572125,'park_first',0,journal,rejected)
 except SteeringModeRefusal:pass
 else:raise AssertionError('EXCESS_MOTION_NOT_REJECTED')
 assert plant.count==0 and not journal and len(rejected)==1 and np.array_equal(before,meta.last)
 execute_complete_stop(lambda v,w,m,t,p,i:applied_step(plant,[v,w],m,t,p,i,journal,rejected),lambda:True)
 assert plant.count==len(journal)==2200 and all(v==w==0. for v,w in plant.requests)and len(rejected)==1;checks['production_refusal_to_full2200_stop']=True
 stop_proof,_,_=complete_stop_source(setup,fixture['packet']);assert stop_proof['passed'];checks['actual_origin_full_stop_qualification']=True
 with np.load(O/'input/TRACE.npz')as saved:
  q=saved['qpos'][-1];vel=saved['qvel'][-1];a=q[3:7];yaw=math.atan2(2*(a[0]*a[3]+a[1]*a[2]),1-2*(a[2]**2+a[3]**2))
 source_journal=json.loads((O/'input/MODE_JOURNAL.json').read_text());last=source_journal[-1];origin=copy.deepcopy(fixture['packet']);origin.update(body=[*q[:2],yaw,float(vel[0]*math.cos(yaw)+vel[1]*math.sin(yaw)),float(vel[5])],body_lateral=float(-vel[0]*math.sin(yaw)+vel[1]*math.cos(yaw)),coupled_episode=True);origin['steering'].update(position=q[setup['steering_qpos_addresses']].tolist(),velocity=vel[setup['steering_qvel_addresses']].tolist());origin['controller_memory']=dict(last_ctrl=last['last_ctrl'],integral=last['integral'])
 real_stop,_,_=complete_stop_source(setup,origin);assert real_stop['passed'];checks['old_actual_refusal_full_state_stop_certificate']=True
 predicted_work=4400
 old=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text())
 assert setup['model_sha256']!=old['setup']['model_sha256']
 cases=[('old_dynamic_fixture',old)]
 for label,change in [('dynamic',lambda x:x['setup'].update(dynamic=True)),('actor',lambda x:x['setup'].update(actor={})),('case',lambda x:x['setup']['case'].update(id='WEST_EAST')),('seed',lambda x:x['setup'].update(seed=1)),('t0',lambda x:x['packet'].update(native_tick=1)),('memory',lambda x:x['packet']['controller_memory'].update(integral=.1))]:
  z=copy.deepcopy(fixture);change(z);cases.append((label,z))
 for label,z in cases:
  try:validate_task(tasks[0],z)
  except AssertionError:refused.append('pre_model_'+label)
  else:raise AssertionError('SCOPE_NEGATIVE_ACCEPTED '+label)
 for label,change in [('model',lambda x:x.update(model_sha256='0'*64)),('limits',lambda x:x['limits'][0].__setitem__(0,-99.)),('noise',lambda x:x['noise'].update(lidar_call=999))]:
  z=copy.deepcopy(setup);change(z)
  try:validate_actual(tasks[0],fixture,z,z['model_sha256'])
  except AssertionError:refused.append('actual_setup_'+label)
  else:raise AssertionError('SETUP_NEGATIVE_ACCEPTED '+label)
 assert response_passed(np.zeros(3))
 for k in range(3):
  e=np.zeros(3);e[k]=ERROR_LIMIT[k]+.001;assert not response_passed(e);refused.append('production_response_'+str(k))
 assert not response_passed([float('nan'),0,0]);refused.append('nonfinite_response')
 assert measured_rest([0,0,0,0,0],[0,0,0,0])and not measured_rest([0,0,0,.004,0],[0,0,0,0])
 assert ready_to_drive([0,0,0,0,0],[0,0,0,0],0)and not ready_to_drive([0,0,0,0,0],[0,0,0,0],.1)
 for task in tasks:
  with np.load(C/('PLAN_'+task['task_id']+'.npz'))as z:p={k:z[k].copy()for k in z.files}
  ss=p['states'];n=len(p['controls']);phases=json.loads((C/('PHASES_'+task['task_id']+'.json')).read_text());q=np.zeros((n,11));q[:,:2]=ss[1:,:2];q[:,3]=np.cos(ss[1:,2]/2);q[:,6]=np.sin(ss[1:,2]/2)
  curvature=np.tan(ss[1:,6])/.6;q[:,7]=np.arctan(.6*curvature/(1-.27*curvature));q[:,9]=np.arctan(.6*curvature/(1+.27*curvature));vel=np.zeros((n,10));vel[:,0]=ss[1:,3]*np.cos(ss[1:,2])-ss[1:,4]*np.sin(ss[1:,2]);vel[:,1]=ss[1:,3]*np.sin(ss[1:,2])+ss[1:,4]*np.cos(ss[1:,2]);vel[:,5]=ss[1:,5]
  cmds=[[0.,*p['requests'][i,:2],ss[i,3],ss[i,5],bool(p['requests'][i,2])]for i in range(n)];journal=[]
  for phase in phases:
   for i in range(phase['begin'],phase['end']):journal.append(dict(phase=phase['name'],nominal_index=i,parked=bool(p['modes'][i]),target=float(p['targets'][i]),before_native=i,last_ctrl=p['memory'][i,:4].tolist(),integral=float(p['memory'][i,4])))
  with tempfile.TemporaryDirectory(dir=O,prefix='zero_model_fixture_')as folder:
   out=Path(folder);(out/'physics').mkdir();local=dict(task,output=str(out));trace=dict(qpos=q,qvel=vel,ctrl=p['controls'].copy(),clearance=np.full(n,.3),self_margin=np.full(n,.01))
   result=dict(passed=True,new_actual_native=n,own_replay_native=n,replay=dict(passed=True),physical=dict(root_guard_native_count=n,bad_contacts=0))
   for path,value in [('RESULT.json',result),('physics/SETUP.json',setup),('physics/BODY_COMMANDS.json',cmds),('MODE_JOURNAL.json',journal),('ACTUAL_INITIAL_PACKET.json',fixture['packet'])]:dump(out/path,value)
   def put():np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
   put();proof=audit(local,False);assert proof['passed'],proof;checks['production_saved_audit_'+task['task_id']]=True
   trace['qpos'][2300,0]+=.02;put();assert not audit(local,False)['passed'];trace['qpos'][2300,0]-=.02;refused.append(task['task_id']+'_actual_pose')
   trace['ctrl'][2300,2]+=.01;put();assert not audit(local,False)['passed'];trace['ctrl'][2300,2]-=.01;put();refused.append(task['task_id']+'_actual_ctrl')
   before_velocity=trace['qvel'][2300,:2].copy();heading=ss[2301,2];trace['qvel'][2300,0]=.009*math.cos(heading);trace['qvel'][2300,1]=.009*math.sin(heading);put();bad=audit(local,False);assert not bad['coupled_speed_prediction_passed'];trace['qvel'][2300,:2]=before_velocity;put();refused.append(task['task_id']+'_coupled_speed_error')
   journal[2300]['parked']=False;dump(out/'MODE_JOURNAL.json',journal)
   try:assert not audit(local,False)['passed']
   except SteeringModeRefusal:pass
   journal[2300]['parked']=True;dump(out/'MODE_JOURNAL.json',journal);refused.append(task['task_id']+'_mode_tamper')
   cmds[-1][1]=.08;dump(out/'physics/BODY_COMMANDS.json',cmds);assert not audit(local,False)['passed'];refused.append(task['task_id']+'_missing_complete_tail')
 for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 checks['all_sources_parse']=True;checks['first_failure_policy']=permitted([])and permitted([dict(passed=True)])and not permitted([dict(passed=False)])
 for name in ['worker','physical','start','finalize','watchdog']:
  spec=importlib.util.spec_from_file_location('qualified_v1114_'+name,C/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 checks['lazy_entry_imports_zero_models']=True
 proc=subprocess.run(command(tasks[0]),cwd=R,capture_output=True,text=True,timeout=5);assert proc.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in proc.stderr;checks['actual_isolated_command_guard']=True
 checks['new_task_outputs']=len(tasks)==2 and all(not Path(t['output']).exists()for t in tasks)
 for name in ['mujoco','vehicle','torch','rclpy']:
  try:__import__(name)
  except AssertionError:refused.append('import_'+name)
  else:raise AssertionError('PHYSICAL_IMPORT_ALLOWED')
 result=dict(passed=all(checks.values()),checks=checks,rejected_negative_cases=refused,models=0,physical_integrations=0,new_analytical_dynamics=predicted_work,source='saved synthetic schema is software qualification only, not measured response')
 dump(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result));assert result['passed']
from pathlib import Path
if __name__=='__main__':main()
