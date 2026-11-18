"""Fixed saved failed state, zero MuJoCo; reproduce both original stop proofs."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('DIAGNOSIS_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import json,time,hashlib,fcntl
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
import stop_certificates as stops
q=stops.q;np=q.np;old=stops.original
read=lambda p:json.loads(p.read_text())
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert (R/'REVIEW_PENDING').exists();raw=R/'runs/v858_nav2_verified/v1218/main_slot03';x=read(raw/'LIVE_OBSERVER_INPUT.json');chosen=read(raw/'LIVE_OBSERVER_SELECTION.json');last=read(raw/'LIVE_OBSERVER_CERTIFICATES.json')[-1]
 with np.load(raw/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 with np.load(raw/'LIVE_OBSERVER_REFERENCE.npz')as z:states=z['states'].copy();memory=z['memory'].copy()
 assert last['current']['passed']and not last['prospective']['passed']and read(raw/'RESULT.json')['error']['error']=="AssertionError('LIVE_COMPLETE_STOP_CERTIFICATE_REFUSED')"
 p=last['packet'];org=dict(q.initial(p),steering_load_episode=last['steering_load_episode']);block=old.front(old.remaining_rows(chosen['rows'],last['offset']),last['prefix']);g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);proofs,pred=stops.prove(engine,g,x,p,org,block)
 for got,saved in zip(proofs,[last['current'],last['prospective']]):assert got['passed']==saved['passed'] and abs(got['minimum_raw_m']-saved['minimum_raw_m'])<=1e-10
 nominal=stops.certify_reference(x,table,chosen['rows'],states,memory,time.monotonic()+180)
 np.savez_compressed(O/'FAILED_STATE_STOP_PREDICTIONS.npz',current=pred[0],prospective=pred[1])
 actual=org['state'];diff=actual-states[last['offset']]
 answer=dict(passed=True,old_failure_reproduced=True,current_stop=proofs[0],after_block_stop=proofs[1],actual_nominal_error=dict(position=float(np.linalg.norm(diff[:2])),yaw=float(abs(np.arctan2(np.sin(diff[2]),np.cos(diff[2])))),steering=float(abs(diff[6]))),nominal_reference_complete_stop=nominal,required=q.REQUIRED,analytical_cpp_native=engine.native+nominal['analytical_cpp_native'],models=0,new_mujoco_native=0)
 q.dump(O/'DIAGNOSIS.json',answer);print(json.dumps({k:v for k,v in answer.items()if k not in['nominal_reference_complete_stop','current_stop','after_block_stop']}));print('nominal',nominal['passed'],nominal.get('failed_offset'),len(nominal['records']))
if __name__=='__main__':main()
