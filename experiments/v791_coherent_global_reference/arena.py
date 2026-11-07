"""Declared field construction before the first physical step; no known walls removed."""
import json,math,os
from pathlib import Path
import numpy as np

def prepare(context,mj):
    env=context['env'];B=context['B'];m=env.model;d=env.data
    own=Path(__file__).parent
    cases=json.loads((own/'SCENE_CASES.json').read_text())
    case=next(c for c in cases if c['id']==os.environ['PHASE_FIELD_CASE'])
    registered=json.loads((own/'KNOWN_FIELD.json').read_text())
    rect,circ=B.clean_map(env)
    assert np.array_equal(np.asarray(rect),registered['known_rectangles']),'ORIGINAL_KNOWN_RECTANGLES_CHANGED'
    assert np.array_equal(np.asarray(circ),registered['known_circles']),'ORIGINAL_KNOWN_CIRCLES_CHANGED'
    assert len(rect)==10 and len(circ)==9
    known=[]
    for gid in range(m.ngeom):
        name=mj.mj_id2name(m,mj.mjtObj.mjOBJ_GEOM,gid) or ''
        if int(m.geom_bodyid[gid])==0 and name.startswith(('real_rect_obs_','real_circle_obs_')) and name not in env.HIDDEN_GEOM_NAMES:
            known.append({'name':name,'pos':m.geom_pos[gid].tolist(),'size':m.geom_size[gid].tolist(),'contype':int(m.geom_contype[gid]),'conaffinity':int(m.geom_conaffinity[gid])})
    assert len(known)==19 and all(x['contype'] or x['conaffinity'] for x in known),'KNOWN_FIELD_COLLISION_GEOMETRY_INCOMPLETE'
    start=np.asarray(case['start_xy']);goal=np.asarray(case['goal_xy']);yaw=case['yaw']
    route=np.c_[np.linspace(start[0],goal[0],161),np.linspace(start[1],goal[1],161)]
    before=d.qpos.copy();d.qpos[:2]=start;d.qpos[3:7]=[math.cos(yaw/2),0.,0.,math.sin(yaw/2)];d.qvel[:]=0.;d.ctrl[:]=0.
    changed=[]
    for obj in env._phase19_object_chain():
        local=vars(obj)
        for key,value in [('robot_xy',start.astype(np.float32)),('goal_xy',goal.astype(np.float32)),('robot_yaw',yaw),('dense_path',route.copy()),('path_world',route.copy())]:
            if key in local:local[key]=value;changed.append([type(obj).__name__,key])
        for key,value in [('wp_index',2),('path_index',0),('prev_goal_dist',float(np.linalg.norm(goal-start))),('prev_wp_dist',float(np.linalg.norm(goal-start))/160)]:
            if key in local:local[key]=value
    # This initial polyline is legacy observation metadata, not an admitted route.
    from unseen_prior import set_public_origin
    set_public_origin(start)
    mj.mj_forward(m,d)
    assert np.array_equal(d.qpos[:2],start) and float(d.time)==0.
    record={'task':'V706_ORIGINAL_FIELD_RANGE_ENTRY','case':case,'known_static_geometries_preserved':known,'known_rectangles':np.asarray(rect).tolist(),'known_circles':np.asarray(circ).tolist(),'removed_known_static_geometries':[],'changed_initial_attributes':changed,'initial_root_qpos_before':before[:7].tolist(),'initial_root_qpos_after':d.qpos[:7].tolist(),'construction_before_first_physics_step':True,'root_reset_during_navigation':False,'empty_course':False,'bootstrap_known_layout_seed':95000011,'training_updates':0,'public_prior_origin_source':'initial robot state only, no actor truth'}
    (Path(context['out'])/'ARENA_CONSTRUCTION.json').write_text(json.dumps(record,indent=2)+'\n')
