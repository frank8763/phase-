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
    import json
    repo=Path(__file__).resolve().parents[2]
    qualification=repo/'runs/v709_joint_reference_certificate'
    audit=json.loads((qualification/'INDEPENDENT_GEOMETRY_AUDIT.json').read_text())
    assert audit['status']=='ALL_THREE_JOINT_GEOMETRY_INDEPENDENTLY_VERIFIED' and all(audit['checks'].values())
    case_id=__import__('os').environ['PHASE_FIELD_CASE']
    qualified=json.loads((qualification/case_id/'RESULT.json').read_text())
    assert qualified['eligible']
    selection=qualified['selection'];anchor=np.asarray(selection['anchor_xy'],float);axis=np.asarray(selection['axis_xy'],float)
    assert abs(float(env.inner.wheel_base)-.6)<1e-12 and abs(max_steer-.42722137342572125)<1e-12
    assert np.linalg.norm(axis)>1.-1e-12 and np.linalg.norm(axis)<1.+1e-12
    clearance=point_clearance([anchor],rect,circ);i=0
    from_start=np.asarray([np.linalg.norm(anchor-np.asarray(start[:2]))])
    protected_distance=np.asarray([np.linalg.norm(np.maximum(abs(anchor)-.8,0))])
    assert clearance[0]>=.90 and from_start[0]>=3.60 and protected_distance[0]>=.40
    assert np.linalg.norm(anchor-np.asarray(env.goal_xy))>=1.4
    assert from_start[0]-RADIUS-AMPLITUDE>3.
    (Path(context['out'])/'KNOWN_PRIOR_REFERENCE.json').write_text(json.dumps({'qualification_version':'V709','reference':selection['certificate'],'construction_only':True,'actor_truth_input_to_online':False},indent=2))
    (Path(context['out'])/'ACTOR_PATCH_SELECTION.json').write_text(json.dumps({'qualification_version':'V709','case_id':case_id,'selection':selection,'qualification_sha256':__import__('hashlib').sha256((qualification/case_id/'RESULT.json').read_bytes()).hexdigest(),'no_navigation_outcome_used':True,'north_south_nearby_observation_scope':case_id=='NORTH_SOUTH'},indent=2))
    swept_world=dict(world);swept_world['circles']=[*world['circles'],[*anchor,RADIUS+AMPLITUDE]]
    swept=build(F,swept_world);initial=float(swept.pose_values([start])[0])
    certificate=certify(swept_world,start,env.goal_xy,float(env.inner.wheel_base),max_steer,F,initial)
    (Path(context['out'])/'MOTION_ENVELOPE_CHECK.json').write_text(json.dumps({'anchor':anchor.tolist(),'start':start,'initial_margin':initial,'certificate':certificate,'offline_v709_certificate':selection['certificate']},default=lambda x:x.tolist()if hasattr(x,'tolist')else x,indent=2))
    assert certificate['eligible'],'FROZEN_JOINT_SCENE_SWEEP_REFERENCE_NOT_REPRODUCED'
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
            'omega_rad_s':SPEED/AMPLITUDE,'phase_rad':float(__import__('os').environ.get('PHASE_COURSE_PHASE','0')),'maximum_speed_m_s':SPEED,'mocap_id':mocap_id,
            'actor_geom_id':gid,'protected_junction_box':[-.8,-.8,.8,.8],
            'known_obstacle_clearance_of_swept_envelope_m':float(clearance[i]-RADIUS-AMPLITUDE),
            'protected_junction_clearance_of_sweep_m':float(protected_distance[i]-RADIUS-AMPLITUDE),
            'swept_envelope_reference':certificate,'construction_only_not_online_input':True,'initial_encounter_distance_m':float(from_start[i]),'new_course_id':'V706_ORIGINAL_FIELD_RANGE_ENTRY','scene_qualification_version':'V709_JOINT_GEOMETRY','north_south_nearby_observation_scope':case_id=='NORTH_SOUTH','case_id':__import__('os').environ['PHASE_FIELD_CASE'],'public_initial_origin_xy':start[:2]}
    actor=Actor(config,env,rect,circ,mj);actor.apply(model,data);mj.mj_forward(model,data)
    synchronize_sensor_arrays(env,rect,circ,[[*actor.xy(data.time),RADIUS]])
    return actor
