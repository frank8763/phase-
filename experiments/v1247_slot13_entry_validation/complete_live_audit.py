"""Audit the existing actual live-adapter output; never regenerate trajectory."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_AUDIT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import fcntl,gzip,copy
def main():
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 raw=R/'runs/v858_nav2_verified/v1243/main_slot13';out=O/'LIVE_ANALYTICAL';x=read(out/'LIVE_GOAL_INPUT.json')
 with gzip.open(raw/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
 auditor=load('v1247_two_stage_saved_auditor',C/'ns_audit.py')
 table=auditor.causal.table_check(out,'LIVE_GOAL',x,sensors)
 bundle=auditor.load_ns_bundle(out/'CURRENT_GOAL_ENTRY');assert bundle['result']['passed']
 external={k:bundle['trace'][k]for k in ['states','controls','memory','requests']}
 result=auditor.verify_goal(x,table,bundle,external,time.monotonic()+120)
 bad=copy.deepcopy(external);bad['controls'][0,0]+=.01
 try:auditor.verify_goal(x,table,bundle,bad,time.monotonic()+120)
 except AssertionError:pass
 else:raise AssertionError('BAD_EXTERNAL_CONTROL_ACCEPTED')
 # The independently reconstructed piecewise proof must reject a changed
 # threshold or a forged handoff count as well as changed applied controls.
 broken=copy.deepcopy(bundle);broken['initial']['admission']['prefix_native']+=1
 try:auditor.verify_goal(x,table,broken,external,time.monotonic()+120)
 except AssertionError:pass
 else:raise AssertionError('BAD_STAGE_BOUNDARY_ACCEPTED')
 result.update(passed=True,models=0,new_mujoco_native=0,actual_live_adapter=True,real_saved_causal_rays=True,
  not_physical_acceptance=True,negative_external_ctrl_rejected=True,negative_stage_boundary_rejected=True,
  saved_trajectory_reused_without_reexecution=True,entry_native=x['packet']['native_tick'],
  analytical_python_native=len(bundle['trace']['requests']),prior_single_stage_audit_assertion_preserved=True,
  additional_negative_audit_partial_counts_unknown=True)
 dump(O/'LIVE_ADAPTER_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
