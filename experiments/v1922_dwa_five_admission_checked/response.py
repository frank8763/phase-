"""Original response/geometry gates; selected DWA command is never rescued."""
import sys

def prove(q,setup,packet,requests,goal,causal_source):
 np=q.np;kernel=sys.modules['kernel'];origin=dict(q.initial(packet),steering_load_episode=False)
 predictor=q.model.Predictor(setup,origin);ss=[predictor.state.copy()];uu=[];mm=[np.r_[predictor.adapter.last,predictor.adapter.integral]]
 for vr,wr,stale in requests:
  s,u=predictor.step(vr,wr,stale);ss.append(s.copy());uu.append(u.copy());mm.append(np.r_[predictor.adapter.last,predictor.adapter.integral])
 ss,uu,mm=map(np.asarray,[ss,uu,mm]);static=kernel.ref._old.Geometry(setup['known'],None)
 minimum=float(static.clearances(ss[:,:3])[0].min());terminal=float(static.clearances(ss[-1:,:3])[0].min())
 if causal_source is not None:
  assert 0<=causal_source['source_age_s']<=.05000001 and causal_source['source_native_tick']<=packet['native_tick'],'CURRENT_CAUSAL_SOURCE_AGE'
  prior=causal_source['periodic'];assert prior['omega']==.32 and prior['amplitude']==.25
  timed=kernel.Geometry(setup['known'],prior,packet['sim_time'])
  minimum=min(minimum,float(timed.clearances(ss[:,:3],np.arange(len(ss)),.005).min()))
  sa,da=kernel.ref._old.Geometry(setup['known'],prior).clearances(ss[-1:,:3]);terminal=float(min(sa[0],da[0]))
 original,upper=q.helper.checks(ss,uu,np.asarray(requests,float),packet,setup,np.asarray(goal),minimum,kernel.REQUIRED)
 checks={k:bool(v)for k,v in original.items()if k!='goal_upper'}
 checks.update(full2200=bool(len(requests)>=2200 and np.array_equal(np.asarray(requests[-2200:],float),np.zeros((2200,3)))),terminal_body_rest=bool(abs(ss[-50:,3:6]).max()<=.003),terminal_steering_rest=bool(abs(ss[-50:,7]).max()<=.015),memory_shape=mm.shape==(len(ss),5),terminal_full_cycle_hold=terminal>=kernel.REQUIRED)
 proof=dict(passed=all(checks.values()),checks=checks,original_whole_checks={k:bool(v)for k,v in original.items()},original_goal_upper_m=float(upper),minimum_raw_m=minimum,terminal_full_cycle_raw_m=terminal,required_raw_m=float(kernel.REQUIRED),origin_packet=packet,causal_source=causal_source,native=len(requests))
 return proof,ss,uu,mm
