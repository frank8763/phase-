"""Execute the current complete stop when the prospective command is refused.
No promise of a robust retained invariant; current proof and live response are
both mandatory. This module never converts a stop into goal success.
"""
from pathlib import Path
import sys,math
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import original
q=original.q;np=q.np

def decision(proofs):
 assert len(proofs)==2 and all(isinstance(p.get('passed'),bool)for p in proofs)
 if not proofs[0]['passed']:return 'REFUSE_NO_CURRENT_CERTIFICATE'
 return 'CONTINUE'if proofs[1]['passed']else 'EXECUTE_CURRENT_STOP'

def execute_current_stop(v,proofs,predictions,origin_packet,packet_fn,observe,permit,save):
 assert decision(proofs)=='EXECUTE_CURRENT_STOP','CURRENT_STOP_NOT_AUTHORIZED'
 expected=np.asarray(predictions[0]);assert expected.shape==(2201,8) and np.isfinite(expected).all(),'COMPLETE_STOP_PREDICTION_REQUIRED'
 initial=packet_fn(v);assert initial['native_tick']==origin_packet['native_tick'] and abs(initial['sim_time']-origin_packet['sim_time'])<=1e-8
 assert np.max(abs(q.initial(initial)['state']-expected[0]))<=1e-8,'STOP_ORIGIN_CHANGED'
 assert np.max(abs(np.asarray(initial['controller_memory']['last_ctrl'])-origin_packet['controller_memory']['last_ctrl']))<=1e-8 and abs(initial['controller_memory']['integral']-origin_packet['controller_memory']['integral'])<=1e-8,'STOP_MEMORY_CHANGED'
 start=v.count;maximum=np.zeros(3);actual=[q.initial(initial)['state'].copy()];journal=[];complete=False
 try:
  for i in range(2200):
   assert permit(),'STOP_HARD_DEADLINE'
   v.adapter.parked_target=None
   before=v.count;v.step(0.,0.,False);assert v.count==before+1
   p=packet_fn(v);state=q.initial(p)['state'];actual.append(state.copy());d=state-expected[i+1]
   error=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);maximum=np.maximum(maximum,error)
   journal.append(dict(before_native=before,request=[0.,0.,False],response_error=error))
   assert(error<=[.04,.035,.015]).all(),'STOP_RESPONSE_REFUSED'
   if v.count%5==0:observe(v.scan())
  final=packet_fn(v);assert original.previous.stopped(final),'STOP_ACTUAL_NOT_AT_REST'
  complete=True
  return dict(passed=True,functional_goal_passed=False,reason='PROSPECTIVE_REFUSED_CURRENT_STOP_EXECUTED',entry_native=start,native=v.count-start,maximum_response_error=maximum,final_packet=final)
 finally:
  save(dict(complete=complete,entry_native=start,native=v.count-start,current=proofs[0],rejected_prospective=proofs[1],maximum_response_error=maximum,origin_packet=origin_packet,final_packet=packet_fn(v)),np.asarray(actual),expected,journal)
