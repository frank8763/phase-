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
def main():
 assert not(O/'ENTRY_QUALIFICATION.json').exists()
 checks={};refused=[];tasks=json.loads((C/'TASKS.json').read_text());fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());setup=fixture['setup']
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
   journal[2300]['parked']=False;dump(out/'MODE_JOURNAL.json',journal);assert not audit(local,False)['passed'];journal[2300]['parked']=True;dump(out/'MODE_JOURNAL.json',journal);refused.append(task['task_id']+'_mode_tamper')
   cmds[-1][1]=.08;dump(out/'physics/BODY_COMMANDS.json',cmds);assert not audit(local,False)['passed'];refused.append(task['task_id']+'_missing_complete_tail')
 for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 checks['all_sources_parse']=True;checks['first_failure_policy']=permitted([])and permitted([dict(passed=True)])and not permitted([dict(passed=False)])
 for name in ['worker','physical','start','finalize','watchdog']:
  spec=importlib.util.spec_from_file_location('qualified_v1112_'+name,C/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 checks['lazy_entry_imports_zero_models']=True
 proc=subprocess.run(command(tasks[0]),cwd=R,capture_output=True,text=True,timeout=5);assert proc.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in proc.stderr;checks['actual_isolated_command_guard']=True
 checks['new_task_outputs']=len(tasks)==2 and all(not Path(t['output']).exists()for t in tasks)
 for name in ['mujoco','vehicle','torch','rclpy']:
  try:__import__(name)
  except AssertionError:refused.append('import_'+name)
  else:raise AssertionError('PHYSICAL_IMPORT_ALLOWED')
 result=dict(passed=all(checks.values()),checks=checks,rejected_negative_cases=refused,models=0,physical_integrations=0,new_analytical_dynamics=0,source='saved synthetic schema is software qualification only, not measured response')
 dump(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result));assert result['passed']
from pathlib import Path
if __name__=='__main__':main()
