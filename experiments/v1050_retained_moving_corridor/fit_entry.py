"""Bounded deterministic shooting on qualified actuator dynamics, no MuJoCo.

The geometric route is guidance only. Every gear reversal receives a complete
200-native hold; predicted wheel/integrator memory is never reset.
"""
import importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1050_retained_moving_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1047_day_relay'))
from kernel import Expander,initial,PARAMETERS,CAP,REQUIRED,ref,predict
def main():
 begun=time.monotonic();x=json.loads((R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json').read_text());proposal=json.loads((O/'TOPOLOGY_STRAIGHT_ENTRY.json').read_text());assert proposal['proposal_found'];aa=proposal['actions']+[dict(length=.18,curvature=0.)];ell=proposal['rear_offset_m'];q=np.array(proposal['start_actual_pose']);q[:2]-=ell*np.array([math.cos(q[2]),math.sin(q[2])]);desired=[]
 for a in aa:
  d=a['length'];k=a['curvature'];yaw=q[2]+d*k
  if abs(k)>1e-12:q[:2]+=[(math.sin(yaw)-math.sin(q[2]))/k,-(math.cos(yaw)-math.cos(q[2]))/k]
  else:q[:2]+=d*np.array([math.cos(q[2]),math.sin(q[2])])
  q[2]=yaw;desired.append(np.r_[q[:2]+ell*np.array([math.cos(yaw),math.sin(yaw)]),yaw])
 desired=np.array(desired);m=len(aa);gears=np.array([1 if a['length']>0 else -1 for a in aa]);z=np.r_[[abs(a['length'])/(.08 if a['length']>0 else .03)/.01 for a in aa],[math.atan(.6*a['curvature']/PARAMETERS['gain_a']) for a in aa]];origin=initial(x['packet']);engine=Expander(x['setup']);geo=ref._old.Geometry(x['setup']['known'],x['source']['periodic']);history=[]
 def run(z,keep=False):
  s=np.array(origin['state']);mem=np.r_[origin['last_ctrl'],origin['integral']];endpoints=[];sampled=[];actions=[];allstates=[s.copy()];last=0
  def part(n,delta,speed):
   nonlocal s,mem
   states=[]
   while n:
    step=min(n,334);p,u,mm=engine.expand(s,mem,np.array([delta]),step,np.array([speed]));s=p[0,-1].copy();mem=mm[0].copy();states.extend(p[0]);n-=step
   states=np.array(states)
   if keep:allstates.extend(states)
   sampled.extend(states[np.linspace(0,len(states)-1,17).astype(int),:3])
  for i,a in enumerate(aa):
   if last and gears[i]!=last:part(200,0.,0.);actions.append(dict(kind='wait',gear=0,target=0.,ticks=200))
   n=max(20,int(round(z[i])));delta=float(np.clip(z[m+i],-CAP,CAP));v=.08 if gears[i]>0 else-.03;part(n,delta,v);actions.append(dict(kind='move',gear=int(gears[i]),target=delta,ticks=n));endpoints.append(s[:3].copy());last=gears[i]
  part(200,0.,0.);actions.append(dict(kind='wait',gear=0,target=0.,ticks=200));endpoints[-1]=s[:3].copy();error=np.array(endpoints)-desired;error[:,2]=np.arctan2(np.sin(error[:,2]),np.cos(error[:,2]));error[:,2]*=.8;error[-1]*=8.;a,b=geo.clearances(np.array(sampled));low=np.minimum(a,b);penalty=10*np.minimum(low-REQUIRED-.001,0.);residual=np.r_[error.ravel(),penalty,s[6]*2.,s[7]*.5]
  return residual,dict(actions=actions,minimum_sampled_raw_m=float(low.min()),endpoint=s.tolist(),endpoints=np.array(endpoints).tolist(),states=np.array(allstates)if keep else None)
 best_r,best=run(z);cost=float(best_r@best_r)
 for it in range(35):
  if time.monotonic()-begun>180:break
  jac=[]
  for j in range(2*m):
   zz=z.copy();h=5. if j<m else .003;zz[j]+=h;rr,_=run(zz);jac.append((rr-best_r)/h)
  jac=np.array(jac).T;scale=np.r_[np.full(m,100.),np.full(m,.02)];a=jac*scale;step=np.linalg.lstsq(np.vstack([a,.04*np.eye(2*m)]),np.r_[-best_r,np.zeros(2*m)],rcond=1e-8)[0];step=np.clip(step,-1.5,1.5)*scale;accepted=False
  for alpha in [1.,.5,.25,.125]:
   zz=z+alpha*step;zz[:m]=np.clip(zz[:m],20,8000);zz[m:]=np.clip(zz[m:],-CAP,CAP);zz[-1]=0.;rr,row=run(zz);newcost=float(rr@rr)
   if newcost<cost-1e-12:z=zz;best_r=rr;best=row;cost=newcost;accepted=True;break
  history.append(dict(iteration=it,cost=cost,minimum_sampled_raw_m=best['minimum_sampled_raw_m'],endpoint=best['endpoint'],accepted=accepted));(O/'FIT_PARTIAL.json').write_text(json.dumps(history[-1])+'\n')
  if not accepted or cost<1e-7:break
 rr,best=run(z,True);ss=best.pop('states');a,b=geo.clearances(ss[:,:3]);minimum=float(np.minimum(a,b).min());python_s,uu,requests,mm=predict(x['setup'],x['packet'],best['actions'],tail=False);difference=float(np.max(abs(ss-python_s)));error=np.asarray(best['endpoint'])[:3]-np.array([2.0000000476837156,-1.92146568250937,0.]);passed=bool(minimum>=REQUIRED and np.linalg.norm(error[:2])<.008 and abs(error[2])<.008 and abs(ss[-50:,3:6]).max()<=.03 and abs(ss[-1,6])<.002 and difference<=1e-10)
 result=dict(best,prefix_qualified=passed,minimum_all_native_full_cycle_raw_m=minimum,cpp_python_maximum_error=difference,terminal_error=error.tolist(),iterations=history,wall_s=time.monotonic()-begun,models=0,integrations=0,physical_ready=False)
 (O/'FIT_ENTRY.json').write_text(json.dumps(result,indent=2)+'\n');np.savez_compressed(O/'ENTRY_PREDICTION.npz',states=ss,controls=uu,requests=requests,memories=mm);print(json.dumps({k:v for k,v in result.items()if k not in ['actions','endpoints','iterations']}))
if __name__=='__main__':main()
