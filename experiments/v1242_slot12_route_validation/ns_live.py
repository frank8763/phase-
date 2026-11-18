"""Generate the NS recovery from freshly measured full state and causal rays."""
from pathlib import Path
import importlib.util,sys,time
R=Path(__file__).resolve().parents[2]
def private(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
_tools=private('phase_v1242_ns_live_tools',R/'experiments/v1195_eight_gib_timed_refuge/route_tools.py')
globals().update({k:v for k,v in vars(_tools).items()if not k.startswith('_')})
goal_entry=private('phase_v1242_ns_package_loader',R/'experiments/v1241_fine_route_reconnection/package_loader.py').get_goal_entry()
def execute(v,setup,original,end,evidence,out,packet_fn,output,*,remaining_fn):
 assert setup['case']['id']=='NORTH_SOUTH' and remaining_fn()>270 and time.time()<end-240,'NS_SCOPE_OR_DEADLINE'
 evidence,meta=bridge.fresh_evidence(v,setup);x=bridge.current_input(v,setup,evidence);x['goal']=setup['case']['goal_xy']
 assert x['goal']==setup['case']['goal_xy'],'NS_REGISTERED_GOAL_CHANGED'
 assert previous.stopped(x['packet']),'NS_CURRENT_REST_REQUIRED'
 entry=v.count;v._chain_phase='ns_current_goal';v._chain_episode=False;v._live_load=False
 v._chain_counts=dict(cpp_native=0,python_native=0,LP_calls=0);v.adapter.parked_target=None
 dump(out/'LIVE_GOAL_INPUT.json',x);dump(out/'LIVE_GOAL_PROVENANCE.json',meta)
 table,calls=bridge.joint_table(x['source']);v._chain_counts['LP_calls']+=calls;np.savez_compressed(out/'LIVE_GOAL_TABLE.npz',**table)
 target=out/'CURRENT_GOAL_ENTRY';target.mkdir()
 try:
  answer=goal_entry.execute(v,setup,x,table,time.monotonic()+max(0.,end-time.time()-120),lambda:time.time()<end-120 and remaining_fn()>150,packet,lambda p:dump(out/'PARTIAL_PROGRESS.json',p),target)
 finally:
  v._chain_counts['cpp_native']+=getattr(v,'_goal_cpp_native',0)
  v._chain_counts['python_native']+=len(getattr(v,'_goal_journal',[]))
  v._chain_counts['admission_python_native']=answer['admission_python_native']if 'answer'in locals()else None
 return dict(passed=True,entry_native=entry,observer_native=0,goal=answer,current_state_and_time_regeneration=True,old_library_certificate_reused=False,formal_retained_commit=False)
