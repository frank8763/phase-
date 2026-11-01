"""Evaluator scene construction ONLY, before the physical audit and first step."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

def prepare(context,mj):
    env=context['env']; B=context['B']; m=env.model; d=env.data
    xml=Path(context['xml']);tree=ET.parse(xml);removed=[]
    for geom in tree.getroot().find('worldbody').findall('geom'):
        name=geom.get('name','')
        if not name.startswith(('real_rect_obs_','real_circle_obs_')) or name=='real_circle_obs_10':continue
        gid=mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,name);assert gid>=0
        geom.set('contype','0');geom.set('conaffinity','0');geom.set('pos','0 0 -10');geom.set('rgba','0 0 0 0')
        m.geom_contype[gid]=0;m.geom_conaffinity[gid]=0;m.geom_pos[gid]=[0,0,-10];m.geom_rgba[gid,3]=0
        removed.append(name)
    assert len(removed)==20
    tree.write(xml,encoding='unicode')
    start=np.array([-3.,-2.]);goal=np.array([1.,-2.]);route=np.c_[np.linspace(-3.,1.,81),np.full(81,-2.)]
    before=d.qpos.copy();d.qpos[:2]=start;d.qpos[3:7]=[1.,0.,0.,0.];d.qvel[:]=0.;d.ctrl[:]=0.
    changed=[]
    for obj in env._phase19_object_chain():
        local=vars(obj)
        for key,value in [('robot_xy',start.astype(np.float32)),('goal_xy',goal.astype(np.float32)),('robot_yaw',0.),('dense_path',route.copy()),('path_world',route.copy())]:
            if key in local:local[key]=value;changed.append([type(obj).__name__,key])
        for key,value in [('wp_index',2),('path_index',0),('prev_goal_dist',4.),('prev_wp_dist',.1)]:
            if key in local:local[key]=value
    B.clean_map=lambda self:([],[])
    from scene_sensors import synchronize_sensor_arrays
    synchronize_sensor_arrays(env,[],[],[])
    mj.mj_forward(m,d)
    assert np.allclose(env.robot_xy,start) and np.allclose(env.goal_xy,goal)
    assert np.allclose(env.inner.dense_path[[0,-1]],np.array([start,goal]))
    (Path(context['out'])/'ARENA_CONSTRUCTION.json').write_text(json.dumps({'task':'OPEN_SINGLE_CROSSING_01','arena_bounds':[-5,-5,5,5], 'start_xy':start.tolist(),'start_yaw':0.,'goal_xy':goal.tolist(),'removed_static_geometries':removed,'changed_scene_attributes':changed,'initial_root_qpos_before':before[:7].tolist(),'initial_root_qpos_after':d.qpos[:7].tolist(),'construction_before_first_physics_step':True,'root_reset_during_navigation':False,'same_as_old_field':False,'training_updates':0},indent=2))
