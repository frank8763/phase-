"""Candidate rollouts in a robot-and-floor model, with no environment obstacles."""
import math
import numpy as np

class RobotPredictor:
    def __init__(self,env,root,mj,native):
        self.mj,self.native=mj,native
        self.model=mj.MjModel.from_xml_path(str(root/'training/assets/mkmini_real/mkmini_mobile_manipulator_v1.xml'))
        self.data=mj.MjData(self.model)
        assert (self.model.nq,self.model.nv,self.model.nu)==(env.model.nq,env.model.nv,env.model.nu)
        for name in ('dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange'):
            getattr(self.model,name)[:]=getattr(env.model,name)
        self.model.opt.timestep=env.model.opt.timestep
        for name in ('body_mass','body_inertia','body_ipos','body_iquat'):
            getattr(self.model,name)[:]=getattr(env.model,name)
        ours=[i for i in range(self.model.ngeom) if self.model.geom_bodyid[i]>0]
        theirs=[i for i in range(env.model.ngeom) if env.model.geom_bodyid[i]>0]
        assert len(ours)==len(theirs)
        for oi,ri in zip(ours,theirs):
            assert self.model.geom_bodyid[oi]==env.model.geom_bodyid[ri] and self.model.geom_type[oi]==env.model.geom_type[ri]
            for name in ('geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_size','geom_pos','geom_quat'):
                getattr(self.model,name)[oi]=getattr(env.model,name)[ri]
        for oi in range(self.model.ngeom):
            if self.model.geom_bodyid[oi]==0:
                ri=mj.mj_name2id(env.model,mj.mjtObj.mjOBJ_GEOM,mj.mj_id2name(self.model,mj.mjtObj.mjOBJ_GEOM,oi))
                self.model.geom_friction[oi]=env.model.geom_friction[ri]
        for name in ('integrator','solver','iterations','tolerance','cone','jacobian'):
            setattr(self.model.opt,name,getattr(env.model.opt,name))
        self.prediction_steps=0
        # This XML has only the robot, its support floor, and visual support geoms.
        for gid in range(self.model.ngeom):
            if int(self.model.geom_bodyid[gid])==0:
                assert int(self.model.geom_type[gid])==int(mj.mjtGeom.mjGEOM_PLANE),'WORLD_OBSTACLE_IN_PREDICTION_MODEL'
    def predict(self,real,target_command,ids,last_command,horizon=80):
        d=self.data;m=self.model
        self.mj.mj_resetData(m,d)
        for name in ('qpos','qvel','act','qacc_warmstart'):
            getattr(d,name)[:]=getattr(real,name)
        d.time=float(real.time);d.ctrl[:]=0.
        command=last_command.copy()
        self.mj.mj_forward(m,d)
        poses=[]
        for tick in range(horizon):
            if tick%8==0:
                command[:2]=np.clip(target_command[:2],command[:2]-.10,command[:2]+.10)
                command[2:]=np.clip(target_command[2:],command[2:]-.70,command[2:]+.70)
                for aid,value in zip(ids,command):d.ctrl[aid]=value
            self.native(m,d);self.prediction_steps+=1
            q=d.qpos;poses.append([q[0],q[1],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))])
        return np.asarray(poses)
    def select(self,env,field,path,index,current,steer,speed,last_command):
        radius=float(env.inner.wheel_radius);wheel_base=float(env.inner.wheel_base)
        actual_speed=float(env.data.qvel[0]*math.cos(current[2])+env.data.qvel[1]*math.sin(current[2]))
        wheel_ref=float(np.clip((speed+1.3*(speed-actual_speed))/radius,-12.,12.))
        ids=[env.inner.id_lf_steer,env.inner.id_rf_steer,env.inner.id_lr_wheel,env.inner.id_rr_wheel]
        # Never score progress across a forward/reverse cusp: that rewards stopping
        # near an overlapping later segment instead of completing the active gear.
        gear=int(path[min(index+1,len(path)-1),3])
        end=index+1
        while end<len(path)-1 and int(path[end+1,3])==gear:end+=1
        candidates=[];segments=path[index:min(end+1,index+40),:3]
        target=segments[min(len(segments)-1,12),:2];start_dist=float(np.linalg.norm(current[:2]-target))
        alignment_error=abs((float(current[2]-segments[min(len(segments)-1,12),2])+np.pi)%(2*np.pi)-np.pi)
        progress_weight=8.*math.exp(-(alignment_error/.35)**2)
        horizon=160 if alignment_error>.25 else 80
        for delta in np.unique(np.clip([steer,steer-.18,steer+.18,-env.inner.max_steer,0.,env.inner.max_steer],-env.inner.max_steer,env.inner.max_steer)):
            for wheel in (wheel_ref,.45*wheel_ref,0.):
                target_command=np.asarray(env.inner._ackermann_from_steer_speed(float(delta),float(wheel)),float)
                command=target_command.copy()
                command[:2]=np.clip(command[:2],last_command[:2]-.10,last_command[:2]+.10)
                command[2:]=np.clip(command[2:],last_command[2:]-.70,last_command[2:]+.70)
                trajectory=self.predict(env.data,target_command,ids,last_command,horizon=horizon)
                clearance=float(np.min(field.pose_values(trajectory)))
                if clearance<.155:continue
                dist=np.linalg.norm(segments[:,:2]-trajectory[-1,:2],axis=1);nearest=int(np.argmin(dist))
                heading=abs((float(trajectory[-1,2]-segments[min(len(segments)-1,12),2])+np.pi)%(2*np.pi)-np.pi)
                progress=start_dist-float(np.linalg.norm(trajectory[-1,:2]-target))
                score=progress_weight*progress-5*float(dist[nearest])-5.*heading+.15*min(clearance,.30)-.0005*float(np.linalg.norm(command-last_command))
                candidates.append((score,command,trajectory,clearance))
        if not candidates:return None,{'status':'NO_MODEL_SAFE_COMMAND','candidate_prediction_steps':self.prediction_steps}
        score,command,trajectory,clearance=max(candidates,key=lambda x:x[0])
        return command,{'status':'MODEL_SAFE_COMMAND','predicted_minimum_clearance_m':clearance,'predicted_end_pose':trajectory[-1].tolist(),'predicted_next_pose':trajectory[7].tolist(),'score':score,'candidate_count_safe':len(candidates),'prediction_steps_total':self.prediction_steps,'hidden_world_geometry_used':False,'active_gear':gear,'segment_end_index':end,'scoring_target':target.tolist(),'target_wheel_sign_matches_plan':True,'alignment_error_rad':alignment_error,'progress_weight':progress_weight,'prediction_horizon_steps':horizon}
