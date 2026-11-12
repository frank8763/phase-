"""One shared physical fixture, exact history recovery, state-neutral owner bind."""
import json,gzip,math
from pathlib import Path
import numpy as np
from kernel import load,law
from plans import R,ARCH

def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def factory(output):
 f=load('execution_core_canonical_factory',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');f.O=Path(output);return f

def bind(v,klass,mj):
 before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};previous=v.adapter
 v.adapter=klass(v.m,mj,v.dt,encoders=v.steering_sample);v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral;v.adapter.virtual_rate=.6
 assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items())

def restore(v,count,out):
 archive=np.load(ARCH/'physics/NATIVE_TRACE.npz');old={k:archive[k]for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};archive.close();cmd=np.asarray(json.loads((ARCH/'physics/BODY_COMMANDS.json').read_text()));assert len(old['qpos'])==count;assert np.array_equal(v.initial,np.load(ARCH/'physics/INITIAL_STATE.npz')['state'])
 with gzip.open(ARCH/'physics/CONTACTS.json.gz','rt')as f:contacts=json.load(f)
 with gzip.open(ARCH/'physics/SENSORS.json.gz','rt')as f:sensors={x['native_tick']:x for x in json.load(f)}
 error=0.;range_error=0.
 def scan():
  nonlocal range_error
  s=v.scan();range_error=max(range_error,float(abs(np.asarray(s['ranges'])-sensors[v.count]['ranges']).max()));assert range_error<=1e-6
 scan()
 for i in range(count):
  v.step(*cmd[i,[1,2,5]])
  for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
   a=np.asarray(getattr(v.d,k));error=max(error,float(abs(a-old[k][i]).max())if a.size else 0.)
  assert error<=1e-8,'HISTORY_STATE_MISMATCH';aa=v.contacts[-1];bb=contacts[i+1];assert len(aa)==len(bb)and all(list(a[:3])==list(b[:3])and abs(a[3]-b[3])<=1e-8 for a,b in zip(aa,bb)),'HISTORY_CONTACT_MISMATCH'
  if v.count%5==0:scan()
  if v.count%1000==0:dump(out/'PARTIAL.json',dict(stage='historical_replay',native=v.count))
 dump(out/'HISTORICAL_REPLAY_PROOF.json',dict(passed=True,native=count,maximum_state_ctrl_mocap_error=error,range_error=range_error,contact_mismatched_ticks=0,no_external_state_restore=True))
