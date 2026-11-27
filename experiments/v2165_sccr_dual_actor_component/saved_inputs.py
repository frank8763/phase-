"""Read saved fixtures and original pure AST; never creates a model/renderer."""
from common import R,read,sha,load
from types import SimpleNamespace
import ast
OLD=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual'
def packet(np,index):
 assert index in [0,1,2];k=5*index;u=load('measured_union_exact',R/'experiments/v2164_sccr_measured_union_sensor/union.py')
 source=R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py';extract=u.functions(source,['_get_depth_features'],np)._get_depth_features
 origin=OLD/f'cycle_{index:06d}_origin.json';receipt=read(origin)['receipt'];p=receipt['packet'];assert p['native_tick']==k
 with np.load(OLD/f'SCCR_DEPTH_{k:06d}.npz')as z:raw=z['depth'].copy()
 class SavedRenderer:
  def update_scene(self,*a,**kw):pass
  def enable_depth_rendering(self):pass
  def render(self):return raw.copy()
  def disable_depth_rendering(self):pass
 depth=extract(SimpleNamespace(depth_camera_id=0,depth_feature_dim=24,depth_max_range=5.,renderer=SavedRenderer(),data=None,depth_camera_name='d435i_depth_camera'));assert depth.tolist()==read(OLD/f'SCCR_DEPTH_{k:06d}.json')['packet']['depth24']
 known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
 with np.load(OLD/'FULL_STATE_NPLUS1.npz')as z:actor=z['mocap_pos'][k,0,:2].copy()
 current=dict(native=k,sim_time=p['sim_time'],body=p['body']);world=dict(native=k,sim_time=p['sim_time'],bounds=[-5.,5.],rectangles=known['known_rectangles'],circles=known['known_circles']+[[float(actor[0]),float(actor[1]),.1]])
 return u.collect_saved_fixture(np,current,world,depth,dict(goal_xy=[4.,-2.],path_world=[[-4.,-2.],[-3.,-2.],[4.,-2.]],wp_index=1),[0.,0.],proof=dict(saved_measured_fixture=True,receipt_sha256=sha(origin),no_live_sensor=True,previous_actuator_units_steer_rad_wheel_rad_s=True))
def observation(np,p,provider):
 m=load('original_186_assembly_for_component',R/'experiments/v2155_sccr_full_observation_assembly/assemble.py');return m.build(np,p,provider,developer_fixture=True)
