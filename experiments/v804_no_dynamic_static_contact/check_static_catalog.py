"""Bounded model-load-only static contact adapter check; no integration."""
import os,sys,json,hashlib,signal,fcntl
from pathlib import Path
import mujoco,mujoco.rollout
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from dynamic_contact import GeometryCatalog
calls=0
def forbidden(*a,**kw):
 global calls
 calls+=1;raise AssertionError('NO_INTEGRATION_STATIC_CATALOG_CHECK')
for n in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,n,forbidden)
mujoco.rollout.rollout=forbidden
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('STATIC_CATALOG_60S')));signal.alarm(60)
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
old=repo/'runs/v803_no_dynamic_five/round01/paired';m=mujoco.MjModel.from_binary_path(str(old/'scene_model.mjb'));c=GeometryCatalog(m,mujoco,old/'assets/isolated_indoor.xml')
assert m.nmocap==0 and not calls
out=repo/'runs/v804_static_catalog_calibration.json';assert not out.exists();out.write_text(json.dumps(dict(status='PASS',new_model_loads=1,new_integrations=calls,source_model_sha256=hashlib.sha256((old/'scene_model.mjb').read_bytes()).hexdigest(),no_dynamic_actor=True,entries=len(c.entries)),indent=2)+'\n');print(out.read_text())
