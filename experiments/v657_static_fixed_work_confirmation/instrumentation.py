import hashlib,json,time
from pathlib import Path
import numpy as np

class PhysicalMutation(RuntimeError):pass

def dump(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    def cv(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,Path):return str(x)
        if isinstance(x,dict):return {str(k):cv(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [cv(v) for v in x]
        return x
    path.write_text(json.dumps(cv(value),indent=2,allow_nan=False))

class Audit:
    def __init__(self):self.previous=None;self.searches=0;self.native_count=0
    def begin(self,env,cell,branch):
        self.env,self.cell,self.branch=env,Path(cell),branch
        self.previous=None;self.native_count=0
        dump(self.cell/'v648_environment.json',{'inner_type':str(type(env.inner)),'mro':[str(c) for c in type(env.inner).__mro__], 'goal_threshold_m':float(env.inner.goal_threshold)})
    def before_native(self,m,d):
        if self.previous is not None:
            self.check(d,'between_physics_steps')
    def after_native(self,m,d):
        self.native_count+=1
        self.previous=(d.qpos[:7].copy(),d.qvel[:6].copy(),float(d.time))
    def check(self,d,where):
        if self.previous is None:return
        q,v,t=self.previous
        dq=float(np.max(np.abs(d.qpos[:7]-q)));dv=float(np.max(np.abs(d.qvel[:6]-v)))
        if dq>1e-10 or dv>1e-10:
            dump(self.cell/'v648_nonphysical_mutation.json',{'where':where,'physics_count':self.native_count,'qpos_max_change':dq,'qvel_max_change':dv,'native_time':t,'current_time':float(d.time),'qpos_before':q,'qpos_after':d.qpos[:7],'qvel_before':v,'qvel_after':d.qvel[:6]})
            raise PhysicalMutation('ROOT_STATE_CHANGED_OUTSIDE_MJSTEP:'+where)
    def before_search(self,world,step):
        self.searches+=1;self.search_dir=self.cell/f'v648_search_{step:04d}'
        dump(self.search_dir/'causal_input.json',world)
        self.search_start=time.monotonic()
    def after_search(self,path,stats,field):
        dump(self.search_dir/'output.json',{'path':path,'stats':stats,'elapsed_s':time.monotonic()-self.search_start,'minimum_clearance':None if path is None else float(np.min(field.pose_values(path)))})
    def after_public(self,env,step):
        self.check(env.data,'after_public_step')
        row={'step':int(step),'time':float(env.data.time),'qpos':env.data.qpos[:7].tolist(),'qvel':env.data.qvel[:6].tolist(),'qpos_full':env.data.qpos.tolist(),'qvel_full':env.data.qvel.tolist(),'ctrl':env.data.ctrl.tolist(),'xy':np.asarray(env.robot_xy).tolist()}
        with (self.cell/'v648_execution.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')

def install_physical_contract(env):
    """Experiment-only: disable post-integration kinematic pose/velocity assistance."""
    from types import MethodType
    seen=set();queue=[env];changed=[]
    def sync_from_physics(self):
        q=self.data.qpos
        self.robot_xy[:]=q[:2]
        self.robot_yaw=float(np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)))
    def no_assist(self):pass
    while queue:
        obj=queue.pop(0)
        if id(obj) in seen:continue
        seen.add(id(obj))
        for key in ('inner','env','base_env'):
            child=vars(obj).get(key)
            if child is not None and hasattr(child,'__dict__'):queue.append(child)
        for name in ('_h3_kinematic_yaw_sync','_h3_velocity_direction_sync','_phase14_apply_bicycle_yaw_sync'):
            if callable(getattr(obj,name,None)):
                setattr(obj,name,MethodType(no_assist,obj));changed.append([str(type(obj)),name])
        if callable(getattr(obj,'_sync_mujoco',None)):
            obj._sync_mujoco=MethodType(sync_from_physics,obj);changed.append([str(type(obj)),'_sync_mujoco:read_physics_only'])
    return changed
