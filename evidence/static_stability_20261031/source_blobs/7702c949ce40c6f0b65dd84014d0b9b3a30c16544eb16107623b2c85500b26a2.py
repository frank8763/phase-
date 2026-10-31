"""Native prediction plus every-tick robot self-geometry admission.
Pose sensors observe the robot-only prediction model; they expose no world truth.
Sensor poses from before each integration plus the final kinematic reconstruction
cover all forecast state boundaries. Joint limits match the live physical model.
"""
import numpy as np
from robot_predictor import RobotPredictor as CppPredictor
from self_geometry import SelfGeometry,quaternion_matrices,containment_margin
SELF_DOMAIN=np.array([-.44,-.375,.44,.375])
class RobotPredictor(CppPredictor):
    def __init__(self,env,root,mj,native):
        super().__init__(env,root,mj,native);old=self.model
        spec=mj.MjSpec.from_file(str(root/'training/assets/mkmini_real/mkmini_mobile_manipulator_v1.xml'))
        for i,g in enumerate(spec.geoms):
            if not g.name:g.name=f'phase_prediction_geom_{i}'
        compiled=spec.compile();self_ids=SelfGeometry(compiled,mj).ids
        spec.add_sensor(name='phase_root_pos',type=mj.mjtSensor.mjSENS_FRAMEPOS,objtype=mj.mjtObj.mjOBJ_BODY,objname='mkmini_base')
        spec.add_sensor(name='phase_root_quat',type=mj.mjtSensor.mjSENS_FRAMEQUAT,objtype=mj.mjtObj.mjOBJ_BODY,objname='mkmini_base')
        for gid in self_ids:
            name=mj.mj_id2name(compiled,mj.mjtObj.mjOBJ_GEOM,int(gid))
            spec.add_sensor(name=f'phase_g{gid}_pos',type=mj.mjtSensor.mjSENS_FRAMEPOS,objtype=mj.mjtObj.mjOBJ_GEOM,objname=name)
            spec.add_sensor(name=f'phase_g{gid}_quat',type=mj.mjtSensor.mjSENS_FRAMEQUAT,objtype=mj.mjtObj.mjOBJ_GEOM,objname=name)
        self.model=spec.compile();self.data=mj.MjData(self.model)
        assert (self.model.nq,self.model.nv,self.model.nu,self.model.ngeom)==(old.nq,old.nv,old.nu,old.ngeom)
        for name in ('dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange','body_mass','body_inertia','body_ipos','body_iquat','geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_size','geom_pos','geom_quat'):
            getattr(self.model,name)[:]=getattr(old,name)
        for name in ('timestep','integrator','solver','iterations','tolerance','cone','jacobian'):setattr(self.model.opt,name,getattr(old.opt,name))
        for name in ('jnt_range','jnt_limited'):getattr(self.model,name)[:]=getattr(env.model,name)
        self.self_geometry=SelfGeometry(self.model,mj);self.domain=SELF_DOMAIN.copy()
    def predict(self,real,target_command,ids,last_command,horizon=240,brake_after=None):
        import mujoco.rollout
        m=self.model;d=self.data;self.mj.mj_resetData(m,d)
        for name in ('qpos','qvel','act','qacc_warmstart'):getattr(d,name)[:]=getattr(real,name)
        d.time=float(real.time);d.ctrl[:]=0.;self.mj.mj_forward(m,d)
        state_spec=self.mj.mjtState.mjSTATE_FULLPHYSICS;initial=np.empty(self.mj.mj_stateSize(m,state_spec));self.mj.mj_getState(m,d,initial,state_spec)
        controls=np.zeros((1,horizon,m.nu));command=last_command.copy()
        for tick in range(0,horizon,8):
            target=target_command.copy()
            if brake_after is not None and tick>=brake_after:target[2:]=0.
            command[:2]=np.clip(target[:2],command[:2]-.10,command[:2]+.10);command[2:]=np.clip(target[2:],command[2:]-.70,command[2:]+.70)
            controls[0,tick:tick+8,ids]=command[:,None]
        states,sensors=mujoco.rollout.rollout(m,d,initial,controls,initial_warmstart=real.qacc_warmstart.copy(),persistent_pool=True)
        self.prediction_steps+=horizon;q=states[0,:,1:1+m.nq];v=states[0,-1,1+m.nq:1+m.nq+m.nv];packet=sensors[0]
        geoms=packet[:,7:].reshape(horizon,-1,7);bounds=self.self_geometry.bounds(geoms[:,:,:3],quaternion_matrices(geoms[:,:,3:]),packet[:,:3],packet[:,3:7])
        self.last_root_sensors=packet[:,:7].copy();self.first_geom_sensors=geoms[0].copy()
        d.qpos[:]=q[-1];d.qvel[:]=v;self.mj.mj_kinematics(m,d);terminal_bounds=self.self_geometry.actual(m,d)
        self.last_self_bounds=np.vstack((bounds,terminal_bounds));self.last_forecast_qpos=q.copy()
        self.prediction_self_margin=float(min(containment_margin(bounds,self.domain).min(),containment_margin(terminal_bounds,self.domain)))
        self.prediction_self_contained=self.prediction_self_margin>=.002
        self.terminal_speed=float(np.linalg.norm(v[:2]));yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        return np.c_[q[:,:2],yaw]
