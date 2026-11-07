"""Isolated zero-integration native model and driver interface qualification."""
import fcntl,hashlib,json,os,sys,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified/model_preflight';OUT.mkdir(exist_ok=False);OLD=R/'runs/v856_nav2_foundation/entry01/vehicle_qualification01';sys.path.insert(0,str(R/'experiments/v855_renewal_worker'));sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
import mujoco as mj
import numpy as np
from model_patch import make_xml,transplant,verify_excludes
from vehicle_control import Adapter
result=dict(passed=False,integrations=0,model_loads=0,model_compiles=0)
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
 old=mj.MjModel.from_binary_path(str(OLD/'scene_model.mjb'));result['model_loads']+=1;xml=make_xml(OLD/'paired/assets/isolated_indoor.xml',OUT/'PATCHED_MODEL.xml',R/'runtime/mk-mini/training/assets/mkmini_real/meshes_fixed');new=mj.MjModel.from_xml_path(str(xml));result['model_compiles']+=1;result['preservation']=transplant(old,new);result['exclude_signatures']=verify_excludes(new,mj);adapter=Adapter(new,mj,.01);result['driver_ids']=adapter.commands.ids
 state=np.load(OLD/'INITIAL_STATE.npz')['state'];d=mj.MjData(new);mj.mj_setState(new,d,state,mj.mjtState.mjSTATE_INTEGRATION);mj.mj_forward(new,d);assert d.time==0.;mj.mj_saveModel(new,str(OUT/'PATCHED_MODEL.mjb'),None);result.update(passed=True,model_sha256=hashlib.sha256((OUT/'PATCHED_MODEL.mjb').read_bytes()).hexdigest())
except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
finally:(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='preservation'}),flush=True)
sys.exit(0 if result['passed']else 1)
