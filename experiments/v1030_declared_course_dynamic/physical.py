"""One declared actor-anchor change BEFORE t0; all 19 static bodies retained.

Robot qpos/qvel/ctrl are never rewritten. Actual initialization only through the
original Phase-isolated factory, after new campaign authority validation.
"""
import hashlib,importlib.util,json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1030_original_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def create_vehicle(out,task):
    out=Path(out);v=base.create_vehicle(out,task);import mujoco as mj
    assert task['dynamic']and v.actor is not None and v.count==0 and v.d.time==0.,'NEW_COURSE_PATCH_AFTER_T0'
    scene=json.loads((R/'experiments/v1029_declared_course_source/SCENE.json').read_text());qualification=json.loads((R/'runs/v1029_declared_course_source/PREVIEW.json').read_text());assert qualification['plan']['passed'],'NEW_COURSE_SOURCE_NOT_QUALIFIED'
    original=json.loads((out/'SETUP.json').read_text());(out/'ORIGINAL_SCENE_CONSTRUCTION.json').write_text(json.dumps(original,indent=2)+'\n')
    before={name:np.asarray(getattr(v.d,name)).copy()for name in ['qpos','qvel','ctrl']};static={name:np.asarray(getattr(v.m,name)).copy()for name in ['geom_pos','geom_quat','geom_size','geom_contype','geom_conaffinity']}
    anchor=np.asarray(scene['actor_anchor_xy']);axis=np.asarray(scene['actor_axis_xy']);assert np.linalg.norm(axis)-1<1e-10 and abs(np.linalg.norm(axis)-1)<1e-10
    assert v.actor.config['axis_xy']==axis.tolist()and v.actor.config['phase_rad']==scene['actor_phase_rad']and v.actor.config['amplitude_m']==.25 and v.actor.config['maximum_speed_m_s']==.08
    clearance=5.-float(abs(anchor).max())
    for x,y,hx,hy in original['known']['known_rectangles']:
        offset=abs(anchor-[x,y])-[hx,hy];clearance=min(clearance,float(np.linalg.norm(np.maximum(offset,0)))if offset.max()>0 else float(offset.max()))
    for x,y,radius in original['known']['known_circles']:clearance=min(clearance,float(np.linalg.norm(anchor-[x,y]))-radius)
    protected=float(np.linalg.norm(np.maximum(abs(anchor)-.8,0)))
    assert clearance>=.9 and np.linalg.norm(anchor-np.asarray(scene['start_xy']))>=3.6 and protected>=.4 and np.linalg.norm(anchor-np.asarray(scene['goal_xy']))>=1.4,'DECLARED_SCENE_PRIOR_GEOMETRY_NOT_QUALIFIED'
    config=v.actor.config;config.update(anchor_xy=anchor.tolist(),new_course_id=scene['scene_id'],scene_qualification_version='V1029_DECLARED_EASIER_DEVELOPMENT',north_south_nearby_observation_scope=False,
        known_obstacle_clearance_of_swept_envelope_m=clearance-.35,protected_junction_clearance_of_sweep_m=protected-.35,initial_encounter_distance_m=float(np.linalg.norm(anchor-np.asarray(scene['start_xy']))),public_initial_origin_xy=scene['start_xy'],construction_only_not_online_input=True,
        swept_envelope_reference=dict(eligible=True,status='ZERO_MODEL_PREVIEW_ONLY_NOT_ACTUAL_ROUTE',search=dict(status='COMPLETE_PREDICTED_INPUT_ROUTE'),qualification_sha256=hashlib.sha256((R/'runs/v1029_declared_course_source/PREVIEW.json').read_bytes()).hexdigest()))
    # Existing mocap body is compiled already; construction anchor metadata and
    # its t0 mocap state are updated together, before any mj_step/native call.
    actor_body=int(v.m.geom_bodyid[config['actor_geom_id']]);v.m.body_pos[actor_body,:2]=anchor;v.actor.apply(v.m,v.d);mj.mj_forward(v.m,v.d)
    assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items()),'ROBOT_INITIAL_STATE_CHANGED'
    assert all(np.array_equal(a,np.asarray(getattr(v.m,k)))for k,a in static.items()),'KNOWN_STATIC_GEOMETRY_CHANGED'
    tree=ET.parse(v.context['xml']);body=tree.getroot().find("worldbody/body[@name='phase_dynamic_actor']");assert body is not None;body.set('pos',f'{anchor[0]} {anchor[1]} 0');xml=out/'DECLARED_COURSE_ASSEMBLY.xml';tree.write(xml,encoding='unicode');v.context['xml']=xml
    v.initial=np.zeros(mj.mj_stateSize(v.m,v.spec));mj.mj_getState(v.m,v.d,v.initial,v.spec);np.savez_compressed(out/'INITIAL_STATE.npz',state=v.initial);mj.mj_saveModel(v.m,str(out/'scene_model.mjb'),None)
    # Restart only the t0 bookkeeping, never physical state or model time.
    v.contacts=[];v.sensor_rows=[];v.first_detection=None;v.min_clear=1e6;v.min_self=1e6;v.bad=0;v.check()
    setup=dict(original,actor=config,model_sha256=hashlib.sha256((out/'scene_model.mjb').read_bytes()).hexdigest(),declared_new_course=scene['scene_id'],original_task_acceptance_claim=False)
    (out/'SETUP.json').write_text(json.dumps(setup,indent=2)+'\n');(out/'DECLARED_SCENE_BINDING.json').write_text(json.dumps(dict(passed=True,patch_native_tick=0,robot_initial_qpos_qvel_ctrl_exact=True,all_original_19_static_geometry_exact=True,only_actor_anchor_changed=True,new_scene=scene['scene_id'],models_at_patch=1,integrations_at_patch=0,not_old_acceptance=True),indent=2)+'\n')
    assert v.count==0 and v.d.time==0. and v.first_detection is None
    return v
replay=base.replay
