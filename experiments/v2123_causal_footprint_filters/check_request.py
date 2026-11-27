"""CPU6 real receipt whitelist and finite current-source refusal checks."""
import copy,os,json,traceback
from common import R,C,S,read,put
from request import build,digest

def main():
 from common import deny_models
 deny_models()
 assert os.sched_getaffinity(0)=={6};result=dict(passed=False,models=0,solvers=0,physics=0,replay=0)
 try:
  pin=read(S/'INPUTS_LOCKED.json');receipt=read(R/pin['saved_receipt'])['receipt'];known=read(R/pin['public_known']);answer=build(receipt,known,[.08,.02],1);assert answer['pose']==[-4.,-2.,0.]and not answer['physical_authority']
  negatives=[]
  def reject(label,fn):
   try:fn()
   except(AssertionError,ValueError,KeyError):negatives.append(label)
   else:raise RuntimeError('BAD_INPUT_ACCEPTED:'+label)
  bad=copy.deepcopy(receipt);bad['packet']['body'][0]+=.1;reject('packet_digest_tamper',lambda:build(bad,known,[.08,.02],1))
  bad2=copy.deepcopy(receipt);bad2['packet']['actor_truth']=[0.,0.];bad2['packet_sha256']=digest(bad2['packet']);reject('actor_truth_field',lambda:build(bad2,known,[.08,.02],1))
  bad3=copy.deepcopy(receipt);bad3['packet']['dynamic_discovered']=True;bad3['packet_sha256']=digest(bad3['packet']);reject('missing_current_dynamic_source',lambda:build(bad3,known,[.08,.02],1))
  reject('public_map_truth_field',lambda:build(receipt,dict(known,actor=[1.,2.]),[.08,.02],1))
  reject('future_source',lambda:build(receipt,known,[.08,.02],1,dict(source_native_tick=1,source_sim_time=.01,periodic={})))
  reject('stale_source',lambda:build(receipt,known,[.08,.02],1,dict(source_native_tick=0,source_sim_time=-.06,periodic={})))
  reject('nonfinite_nominal',lambda:build(receipt,known,[float('nan'),.02],1))
  result.update(passed=True,negative_cases=negatives,request=answer,old_receipt_used_only_offline=True,fullstate_or_actor_not_transmitted=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result['closed']=True;put(S/'REQUEST_SOFTWARE_RESULT.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
