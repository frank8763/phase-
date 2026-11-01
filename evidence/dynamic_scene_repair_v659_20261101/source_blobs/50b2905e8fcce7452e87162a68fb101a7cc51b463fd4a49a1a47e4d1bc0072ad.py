"""Serial-equivalent prediction using MuJoCo C++ rollout, one calling thread."""
import numpy as np
from serial_predictor import RobotPredictor as SerialRobotPredictor

class RobotPredictor(SerialRobotPredictor):
    def predict(self,real,target_command,ids,last_command,horizon=240,brake_after=None):
        import mujoco.rollout
        m=self.model;d=self.data
        self.mj.mj_resetData(m,d)
        for name in ('qpos','qvel','act','qacc_warmstart'):getattr(d,name)[:]=getattr(real,name)
        d.time=float(real.time);d.ctrl[:]=0.
        self.mj.mj_forward(m,d)
        spec=self.mj.mjtState.mjSTATE_FULLPHYSICS
        initial=np.empty(self.mj.mj_stateSize(m,spec));self.mj.mj_getState(m,d,initial,spec)
        controls=np.zeros((1,horizon,m.nu));command=last_command.copy()
        for tick in range(0,horizon,8):
            target=target_command.copy()
            if brake_after is not None and tick>=brake_after:target[2:]=0.
            command[:2]=np.clip(target[:2],command[:2]-.10,command[:2]+.10)
            command[2:]=np.clip(target[2:],command[2:]-.70,command[2:]+.70)
            controls[0,tick:min(tick+8,horizon),ids]=command[:,None]
        state,_=mujoco.rollout.rollout(m,d,initial,controls,initial_warmstart=real.qacc_warmstart.copy(),persistent_pool=True)
        self.prediction_steps+=horizon
        q=state[0,:,1:1+m.nq];v=state[0,-1,1+m.nq:1+m.nq+m.nv]
        yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        self.terminal_speed=float(np.linalg.norm(v[:2]));return np.column_stack((q[:,:2],yaw))
