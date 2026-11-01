"""Preregistered obstacle-free route construction before the first integration."""
import json,hashlib,math
from pathlib import Path
from types import MethodType
import xml.etree.ElementTree as ET
import numpy as np

def prepare(context,mj,course,repo):
    env=context['env'];B=context['B'];m=env.model;d=env.data
    xml=Path(context['xml']);tree=ET.parse(xml);removed=[]
    for geom in tree.getroot().find('worldbody').findall('geom'):
        name=geom.get('name','')
        if not name.startswith(('real_rect_obs_','real_circle_obs_')):continue
        gid=mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,name);assert gid>=0
        geom.set('contype','0');geom.set('conaffinity','0');geom.set('pos','0 0 -10');geom.set('rgba','0 0 0 0')
        m.geom_contype[gid]=0;m.geom_conaffinity[gid]=0;m.geom_pos[gid]=[0,0,-10];m.geom_rgba[gid,3]=0
        removed.append(name)
    assert len(removed)==21
    tree.write(xml,encoding='unicode')
    source=None
    if course=='straight':
        route=np.c_[np.linspace(-3,1,101),np.full(101,-2.),np.zeros(101),np.ones(101)];goal=np.array([1.,-2.])
    elif course=='turn':
        angle=np.linspace(0,math.pi/2,121)
        route=np.c_[-3+2*np.sin(angle),-2+2*(1-np.cos(angle)),angle,np.ones(121)];goal=np.array([-1.,0.])
    else:
        file=repo/'runs/v686_dynamic_open_curriculum/open01/paired/geometry_memory/planning_0032.json'
        route=np.asarray(json.loads(file.read_text())['path']);goal=np.array([1.,-2.]);source={'path':str(file.relative_to(repo)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'original_role':'past causal geometric route; no actor truth supplied'}
    assert route.ndim==2 and route.shape[1]==4 and np.all(route[:,3]==1)
    start=np.array([-3.,-2.]);d.qpos[:2]=start;d.qpos[3:7]=[1,0,0,0];d.qvel[:]=0;d.ctrl[:]=0
    for obj in env._phase19_object_chain():
        local=vars(obj)
        for key,value in [('robot_xy',start.astype(np.float32)),('goal_xy',goal.astype(np.float32)),('robot_yaw',0.),('dense_path',route[:,:2].copy()),('path_world',route[:,:2].copy())]:
            if key in local:local[key]=value
        for key,value in [('wp_index',2),('path_index',0),('prev_goal_dist',float(np.linalg.norm(goal-start))),('prev_wp_dist',.1)]:
            if key in local:local[key]=value
    B.clean_map=lambda self:([],[])
    env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    from scene_sensors import synchronize_sensor_arrays
    synchronize_sensor_arrays(env,[],[],[]);mj.mj_forward(m,d)
    assert np.allclose(env.robot_xy,start)and np.allclose(env.goal_xy,goal)
    return route,{'course':course,'removed_static_geometries':removed,'active_obstacles':0,'actor_count':0,'initial_state_construction_only':True,'arena_bounds':[-5,-5,5,5],'goal_xy':goal.tolist(),'reference_source':source,'reference':route.tolist(),'same_as_v686_single_variable_ablation':False,'fixed_route_no_replanning':True,'backup_handover_disabled':True}
