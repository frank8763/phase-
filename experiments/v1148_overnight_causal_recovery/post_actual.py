"""Rebuild only actual final-packet observations, then certify coupled support."""
from night_tools import *
import gzip,types,signal
import numpy as np
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from refresh import causal_packets

def main():
 root=R/'runs/v858_nav2_verified/v1148/component_main';assert json.loads((root/'RESULT.json').read_text())['passed']and json.loads((root/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed']
 out=O/'actual_source';out.mkdir(exist_ok=False);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ACTUAL_SOURCE300')));signal.alarm(min(300,max(1,int(remaining()-60))))
 p=json.loads((root/'ACTUAL_FINAL_PACKET.json').read_text());setup=json.loads((root/'physics/SETUP.json').read_text());packets=json.loads(gzip.open(root/'physics/SENSORS.json.gz','rt').read());clean,duplicates=causal_packets(packets,p)
 causal=load('night_actual_measurement_estimator',R/'experiments/v1024_full_route_execution/causal.py');norm=load('night_original_periodic_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');e=causal.Evidence(setup['known']);e.periodic=norm.PeriodicSupport()
 for row in clean:e.update(row)
 source=e.source(types.SimpleNamespace(d=types.SimpleNamespace(time=p['sim_time'])));assert 0<=source['source_age_s']<=.051
 sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from joint_domain import Domain,NORMALS
 d=Domain(source['periodic']['vertices']);centers=(np.arange(256)+.5)*(2*np.pi/.32/256);upper,dual,_=d.table(centers);directions=np.array([[[nx,nx*np.sin(.32*t),nx*np.cos(.32*t),ny,ny*np.sin(.32*t),ny*np.cos(.32*t)]for nx,ny in NORMALS]for t in centers]);res=directions-np.einsum('tnj,jk->tnk',dual,d.A);verified=np.einsum('tnj,j->tn',dual,d.b)+np.where(res>=0,res*d.upper,res*d.lower).sum(axis=2)+1e-8;assert np.all(dual>=0)and abs(verified-upper).max()<=1e-9
 bounds=upper+.08*((2*np.pi/.32/256)/2+.075)+2e-7;np.savez_compressed(out/'JOINT_TABLE.npz',bounds=bounds,centers=centers,dual=dual,residual=res,A=d.A,b=d.b,lower=d.lower,upper_box=d.upper)
 dump(out/'FRESH_INPUT.json',dict(setup=setup,packet=p,source=source,goal=[4.,-2.],safe_terminal_pose=[4.,-1.85,0.]));dump(out/'RESULT.json',dict(passed=True,actual_unique_packets=len(clean),duplicates=duplicates,source_native=source['source_native_tick'],decision_native=p['native_tick'],source_age_s=source['source_age_s'],relative_to_saved_physical_time_not_live_robot=True,no_future_or_actor_truth=True,LP_calls=d.calls,models=0,physical_native=0));signal.alarm(0)

if __name__=='__main__':main()
