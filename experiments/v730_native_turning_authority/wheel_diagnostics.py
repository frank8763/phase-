"""Read wheel/ground kinematics and forces from a separate zero-step data copy."""
import hashlib
import numpy as np

class WheelDiagnostics:
    def __init__(self,model,mj):
        self.model=model;self.mj=mj;self.copy=mj.MjData(model)
        self.metadata=[]
        for name in ['left_front_wheel','right_front_wheel','left_rear_wheel','right_rear_wheel']:
            body=mj.mj_name2id(model,mj.mjtObj.mjOBJ_BODY,name);joint=mj.mj_name2id(model,mj.mjtObj.mjOBJ_JOINT,name+'_joint');assert min(body,joint)>=0
            geoms=[int(i)for i in np.flatnonzero(model.geom_bodyid==body)if np.any(model.geom_contype[i])or np.any(model.geom_conaffinity[i])];assert len(geoms)==1
            gid=geoms[0];assert model.geom_type[gid]==mj.mjtGeom.mjGEOM_CYLINDER
            self.metadata.append(dict(name=name,body=body,joint=joint,qpos=int(model.jnt_qposadr[joint]),qvel=int(model.jnt_dofadr[joint]),geom=gid,radius=float(model.geom_size[gid,0]),friction=model.geom_friction[gid].tolist(),condim=int(model.geom_condim[gid])))
        self.floor=set(int(i)for i in np.flatnonzero(model.geom_type==mj.mjtGeom.mjGEOM_PLANE));assert self.floor
        self.jacp=np.zeros((3,model.nv));self.jacr=np.zeros((3,model.nv))
    def sample(self,real):
        m=self.model;mj=self.mj;d=self.copy
        before=hashlib.sha256(b''.join(np.asarray(getattr(real,n)).tobytes()for n in ['qpos','qvel','ctrl','qacc_warmstart'])).hexdigest()
        mj.mj_copyData(d,m,real);mj.mj_forward(m,d);rows=[];all_floor=[]
        for index,contact in enumerate(d.contact):
            if int(contact.geom1)not in self.floor and int(contact.geom2)not in self.floor:continue
            force=np.zeros(6);mj.mj_contactForce(m,d,index,force);other=int(contact.geom2)if int(contact.geom1)in self.floor else int(contact.geom1)
            all_floor.append(dict(index=index,geom=other,body=mj.mj_id2name(m,mj.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[other])),distance_m=float(contact.dist),dimension=int(contact.dim),normal_force_abs_n=abs(float(force[0])),tangential_force_norm_n=float(np.linalg.norm(force[1:3])),torsional_torque_abs_nm=abs(float(force[3])),rolling_torque_norm_nm=float(np.linalg.norm(force[4:6])),contact_force_torque=force.tolist(),friction=contact.friction.tolist()))
        for item in self.metadata:
            bid=item['body'];gid=item['geom'];axis=d.xmat[bid].reshape(3,3)@m.jnt_axis[item['joint']];forward=np.cross(axis,[0.,0.,1.]);forward[2]=0.;forward/=np.linalg.norm(forward);side=np.cross([0.,0.,1.],forward)
            mj.mj_jac(m,d,self.jacp,self.jacr,d.geom_xpos[gid],bid);center_velocity=self.jacp@d.qvel;omega=float(d.qvel[item['qvel']]);contacts=[]
            for entry in all_floor:
                if entry['geom']!=gid:continue
                contact=d.contact[entry['index']];mj.mj_jac(m,d,self.jacp,self.jacr,contact.pos,bid);point_velocity=self.jacp@d.qvel
                contacts.append(dict(**entry,point_velocity_world_m_s=point_velocity.tolist(),contact_longitudinal_slip_m_s=float(point_velocity@forward),contact_lateral_slip_m_s=float(point_velocity@side)))
            rows.append(dict(name=item['name'],wheel_joint_speed_rad_s=omega,center_longitudinal_velocity_m_s=float(center_velocity@forward),center_lateral_velocity_m_s=float(center_velocity@side),rolling_speed_reference_m_s=item['radius']*omega,rolling_mismatch_m_s=float(center_velocity@forward-item['radius']*omega),ground_contacts=contacts))
        after=hashlib.sha256(b''.join(np.asarray(getattr(real,n)).tobytes()for n in ['qpos','qvel','ctrl','qacc_warmstart'])).hexdigest();assert before==after,'DIAGNOSTIC_MUTATED_EXECUTED_STATE'
        return dict(time=float(real.time),wheels=rows,all_floor_contacts=all_floor,executed_state_unchanged=True,diagnostic_forward_integrations=0)
