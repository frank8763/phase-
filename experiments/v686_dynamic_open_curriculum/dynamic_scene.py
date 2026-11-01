"""Scene/evaluation only. Its motion parameters never enter an online field."""
import math
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from task_planner import search
from task_preflight import certify
from exact_footprint import build,pose_values
from scene_sensors import synchronize_sensor_arrays

RADIUS=.10
AMPLITUDE=.25
SPEED=.08

def point_clearance(points,rect,circ):
    p=np.asarray(points);value=np.min(5.-abs(p),axis=1)
    for x,y,hx,hy in rect:value=np.minimum(value,np.linalg.norm(np.maximum(abs(p-[x,y])-[hx,hy],0),axis=1))
    for x,y,r in circ:value=np.minimum(value,np.linalg.norm(p-[x,y],axis=1)-r)
    return value

class Motion:
    def __init__(self,config):self.config=config
    def xy(self,t):
        c=self.config
        return np.asarray(c['anchor_xy'])+np.asarray(c['axis_xy'])*c['amplitude_m']*math.sin(c['omega_rad_s']*t+c['phase_rad'])
    def apply(self,m,d):
        d.mocap_pos[self.config['mocap_id']]=[*self.xy(float(d.time)),0.]
        d.mocap_quat[self.config['mocap_id']]=[1.,0.,0.,0.]

class Actor(Motion):
    def __init__(self,config,env,rect,circ,mj):
        super().__init__(config);self.env=env;self.rect=rect;self.circ=circ;self.mj=mj
        self.maximum_displacement=0.;self.last_xy=None;self.observed_ticks=0
    def synchronize(self,m,d):
        self.apply(m,d);self.mj.mj_kinematics(m,d);self.mj.mj_collision(m,d)
        xy=self.xy(float(d.time))
        synchronize_sensor_arrays(self.env,self.rect,self.circ,[[*xy,RADIUS]])
        if self.last_xy is not None:
            delta=float(np.linalg.norm(xy-self.last_xy));self.maximum_displacement=max(self.maximum_displacement,delta)
            assert delta<=SPEED*float(m.opt.timestep)+1e-8,'ACTOR_DISPLACEMENT_BOUND_BREACH'
        self.last_xy=xy.copy();self.observed_ticks+=1
        assert np.linalg.norm(xy-self.config['anchor_xy'])<=AMPLITUDE+1e-10
    def true_clearance(self,geometry,m,d):
        bounds=geometry.actual(m,d)
        q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,
            rectangles=np.asarray(self.rect).reshape(-1,4),circles=np.asarray([*self.circ,[*self.xy(d.time),RADIUS]]).reshape(-1,3),
            sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
        return float(pose_values(field,[[q[0],q[1],yaw]])[0])

def setup(context,env,rect,circ,F,H,B,mj,max_steer):
    world=H.world_input(env,[]);world['footprint_bounds']=[-.44,-.375,.44,.375]
    start=[*env.data.qpos[:2],float(env.robot_yaw)]
    field=build(F,world);field.base_heuristic=F.base._heuristic_grid
    route,stats=search(field,start,env.goal_xy,float(env.inner.wheel_base),max_steer,guard=.155,
                       resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
    assert route is not None and stats['status']=='GLOBAL_GOAL_PATH','NO_KNOWN_MAP_REFERENCE_FOR_DYNAMIC_SCENE'
    # Preregistered new curriculum task; evaluator construction only.
    # It is deliberately placed on the obstacle-free direct route, not selected after navigation.
    import json
    (Path(context['out'])/'KNOWN_PRIOR_REFERENCE.json').write_text(json.dumps({'path':route.tolist(),'stats':stats,'prior_only':True,'actor_truth_input':False},indent=2))
    anchor=np.array([-1.,-2.]);axis=np.array([0.,1.])
    clearance=point_clearance(np.array([anchor]),rect,circ)
    protected_distance=np.linalg.norm(np.maximum(abs(np.array([anchor]))-.8,0),axis=1)
    i=0
    swept_world=dict(world);swept_world['circles']=[*world['circles'],[*anchor,RADIUS+AMPLITUDE]]
    swept=build(F,swept_world);initial=float(swept.pose_values([start])[0])
    certificate=certify(swept_world,start,env.goal_xy,float(env.inner.wheel_base),max_steer,F,initial)
    import json
    (Path(context['out'])/'MOTION_ENVELOPE_CHECK.json').write_text(json.dumps({'anchor':anchor.tolist(),'start':start,'initial_margin':initial,'certificate':certificate},default=lambda x:x.tolist()if hasattr(x,'tolist')else x,indent=2))
    assert certificate['eligible'],'SWEPT_MOTION_REFERENCE_NOT_CERTIFIED'
    xml=Path(context['xml']);tree=ET.parse(xml);body=tree.getroot().find('worldbody')
    geom=body.find("geom[@name='real_circle_obs_10']");assert geom is not None
    body.remove(geom);actor_body=ET.SubElement(body,'body',name='phase_dynamic_actor',mocap='true',pos=f'{anchor[0]} {anchor[1]} 0')
    geom.set('pos','0 0 .22');geom.set('size','.10 .20');geom.set('contype','1');geom.set('conaffinity','1');geom.set('rgba','.9 .25 .08 1');actor_body.append(geom)
    tree.write(xml,encoding='unicode')
    old,old_data=env.model,env.data;model=mj.MjModel.from_xml_path(str(xml));data=mj.MjData(model)
    assert (model.nq,model.nv,model.nu,model.ngeom)==(old.nq,old.nv,old.nu,old.ngeom)
    assert model.nbody==old.nbody+1 and model.nmocap==1
    for b in range(old.nbody):assert mj.mj_id2name(model,mj.mjtObj.mjOBJ_BODY,b)==mj.mj_id2name(old,mj.mjtObj.mjOBJ_BODY,b)
    old_gid=mj.mj_name2id(old,mj.mjtObj.mjOBJ_GEOM,'real_circle_obs_10');gid=mj.mj_name2id(model,mj.mjtObj.mjOBJ_GEOM,'real_circle_obs_10')
    old_ids=[j for j in range(old.ngeom)if j!=old_gid];new_ids=[j for j in range(model.ngeom)if j!=gid]
    for a,b in zip(old_ids,new_ids):
        assert old.geom_bodyid[a]==model.geom_bodyid[b] and old.geom_type[a]==model.geom_type[b]
        assert mj.mj_id2name(old,mj.mjtObj.mjOBJ_GEOM,a)==mj.mj_id2name(model,mj.mjtObj.mjOBJ_GEOM,b)
    for name in ['geom_pos','geom_quat','geom_size','geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_contype','geom_conaffinity','geom_rgba']:
        getattr(model,name)[new_ids]=getattr(old,name)[old_ids]
    for name in ['body_pos','body_quat','body_mass','body_inertia','body_ipos','body_iquat']:
        getattr(model,name)[:old.nbody]=getattr(old,name)
    for name in ['qpos0','dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange','jnt_range','jnt_limited']:
        getattr(model,name)[:]=getattr(old,name)
    for name in ['timestep','integrator','solver','iterations','tolerance','cone','jacobian','gravity']:
        setattr(model.opt,name,getattr(old.opt,name))
    for name in ['qpos','qvel','ctrl','act','qacc_warmstart']:getattr(data,name)[:]=getattr(old_data,name)
    data.time=old_data.time
    for obj in env._phase19_object_chain():
        for key,value in list(vars(obj).items()):
            if value is old:setattr(obj,key,model)
            elif value is old_data:setattr(obj,key,data)
    assert env.model is model and env.data is data
    mocap_id=int(model.body_mocapid[mj.mj_name2id(model,mj.mjtObj.mjOBJ_BODY,'phase_dynamic_actor')])
    config={'anchor_xy':anchor.tolist(),'axis_xy':axis.tolist(),'radius_m':RADIUS,'amplitude_m':AMPLITUDE,
            'omega_rad_s':SPEED/AMPLITUDE,'phase_rad':0.,'maximum_speed_m_s':SPEED,'mocap_id':mocap_id,
            'actor_geom_id':gid,'protected_junction_box':[-.8,-.8,.8,.8],
            'known_obstacle_clearance_of_swept_envelope_m':float(clearance[i]-RADIUS-AMPLITUDE),
            'protected_junction_clearance_of_sweep_m':float(protected_distance[i]-RADIUS-AMPLITUDE),
            'swept_envelope_reference':certificate,'construction_only_not_online_input':True}
    actor=Actor(config,env,rect,circ,mj);actor.apply(model,data);mj.mj_forward(model,data)
    synchronize_sensor_arrays(env,rect,circ,[[*actor.xy(data.time),RADIUS]])
    return actor
