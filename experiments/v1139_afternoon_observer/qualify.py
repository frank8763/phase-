"""Actual physical worker/audit/report seams before any model; source and response negatives."""
import sys,math,tempfile,ast,importlib.abc
from afternoon_tools import *
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import numpy as np
sys.path.insert(0,str(C));import static_worker,static_audit

def main():
 assert not(O/'ROUND_WINDOW.json').exists();assert json.loads((O/'HISTORY_CONTROLLER_QUALIFICATION.json').read_text())['passed'];assert json.loads((O/'PREPARATION.json').read_text())['passed'];worker=static_worker.module();audit=static_audit.module().audit;fixture=json.loads((C/'STATIC_T0_SOURCE_FIXTURE.json').read_text());setup=fixture['setup'];negative=0;positive=0
 for task in json.loads((C/'TASKS.json').read_text()):
  with np.load(C/('PLAN_'+task['task_id']+'.npz'))as z:p={k:z[k].copy()for k in z.files}
  ss=p['states'];n=len(p['controls']);assert n==8000;phases=json.loads((C/('PHASES_'+task['task_id']+'.json')).read_text());q=np.zeros((n,11));q[:,:2]=ss[1:,:2];q[:,3]=np.cos(ss[1:,2]/2);q[:,6]=np.sin(ss[1:,2]/2);k=np.tan(ss[1:,6])/.6;q[:,7]=np.arctan(.6*k/(1-.27*k));q[:,9]=np.arctan(.6*k/(1+.27*k));vel=np.zeros((n,10));vel[:,0]=ss[1:,3]*np.cos(ss[1:,2])-ss[1:,4]*np.sin(ss[1:,2]);vel[:,1]=ss[1:,3]*np.sin(ss[1:,2])+ss[1:,4]*np.cos(ss[1:,2]);vel[:,5]=ss[1:,5];cmd=[[0.,*p['requests'][i,:2],ss[i,3],ss[i,5],bool(p['requests'][i,2])]for i in range(n)];journal=[]
  for phase in phases:
   for i in range(phase['begin'],phase['end']):journal.append({'phase':phase['name'],'nominal_index':i,'parked':bool(p['modes'][i]),'target':float(p['targets'][i]),'before_native':i,'last_ctrl':p['memory'][i,:4].tolist(),'integral':float(p['memory'][i,4])})
  with tempfile.TemporaryDirectory(dir=O,prefix='audit_fixture_')as folder:
   out=Path(folder);(out/'physics').mkdir();local=dict(task,output=str(out));trace={'qpos':q,'qvel':vel,'ctrl':p['controls'].copy(),'clearance':np.full(n,.3),'self_margin':np.full(n,.01)};result={'passed':True,'new_actual_native':n,'own_replay_native':n,'replay':{'passed':True},'physical':{'root_guard_native_count':n,'bad_contacts':0}}
   for name,value in [('RESULT.json',result),('physics/SETUP.json',setup),('physics/BODY_COMMANDS.json',cmd),('MODE_JOURNAL.json',journal),('ACTUAL_INITIAL_PACKET.json',fixture['packet'])]:dump(out/name,value)
   def put():np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
   put();assert audit(local,False)['passed'];positive+=1
   trace['qpos'][2300,0]+=.03;put();assert not audit(local,False)['passed'];trace['qpos'][2300,0]-=.03;negative+=1
   trace['ctrl'][2300,2]+=.01;put();assert not audit(local,False)['passed'];trace['ctrl'][2300,2]-=.01;negative+=1
   put();cmd[-1][1]=.12;dump(out/'physics/BODY_COMMANDS.json',cmd);assert not audit(local,False)['passed'];negative+=1
 # The actual report path uses strict encode, including nested numpy booleans.
 payload={'passed':np.bool_(True),'component':{'proof':{'checks':{'parked':np.bool_(False)}}},'counts':{'n':np.int64(14700)},'matrix':np.array([1.,2.])};text=encode(payload);assert json.loads(text)['component']['proof']['checks']['parked']is False
 with tempfile.TemporaryDirectory(dir=O,prefix='record_fixture_')as folder:
  p=Path(folder)/'report.md';p.write_text('# Actual report encoder\n'+text);assert 'false'in p.read_text()
  q=Path(folder)/'result.json';dump(q,payload);old=q.read_bytes()
  for bad in [float('nan'),float('inf'),object()]:
   try:dump(q,{'bad':bad})
   except (ValueError,TypeError):assert q.read_bytes()==old;negative+=1
   else:raise AssertionError('ILLEGAL_RECORD_ACCEPTED')
 for name in ['observer_worker','observer_audit','post_observation','physical','software_worker','campaign','watchdog','start']:
  m=load('qualified_afternoon_'+name,C/(name+'.py'));assert m is not None
 for p in C.glob('*.py'):ast.parse(p.read_text())
 # New normal-brake component uses existing .025 terminal tolerance, never mode .02 translation.
 original=json.loads((R/'runs/v1138_backup_corridor/COMPLETION.json').read_text())['component'];assert original['stop_drift_m']>.02 and original['stop_drift_m']<.025;assert original['source_proof']['checks']['safe_terminal_position'];assert not original['source_proof']['checks']['refuge_stop_drift_within02']
 result={'passed':True,'real_static_worker_entry_imported':True,'production_response_audit_positives':positive,'production_audit_and_record_negatives':negative,'actual_nested_numpy_report_roundtrip':True,'original_v1138_failed_unchanged':True,'normal_brake_and_parked_mode_contract_separated':True,'historical_controller_exact':True,'all_lazy_physical_entries_imported_without_models':True,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0};dump(O/'ENTRY_QUALIFICATION.json',result);print(encode(result))
if __name__=='__main__':main()
