"""One predeclared scalar fit on old samples; ten later samples held out."""
import json,math,sys,importlib.abc,importlib.util
from common import C,R,O,dump
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_FIT '+name)
sys.meta_path.insert(0,NoModel())
import numpy as np
def main():
 assert not(C/'COUPLING.json').exists(),'NO_REFIT'
 spec=importlib.util.spec_from_file_location('saved_virtual',R/'experiments/v1003_causal_recovery_execution/predictor.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 f=json.loads((C/'STATIC_T0_SOURCE_FIXTURE.json').read_text());setup=f['setup'];base=json.loads((R/'experiments/v1044_curvature_speed_prediction/PARAMETERS.json').read_text());pole=base['speed_discrete'][0]
 with np.load(O/'input/TRACE.npz')as z:q=z['qpos'].copy();vel=z['qvel'].copy();ctrl=z['ctrl'].copy()
 a=q[:,3:7];yaw=np.arctan2(2*(a[:,0]*a[:,3]+a[:,1]*a[:,2]),1-2*(a[:,2]**2+a[:,3]**2));speed=vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw)
 indices=np.arange(2200,2228);angle=np.array([m.virtual(row)for row in q[:,setup['steering_qpos_addresses']]]);rate=np.array([m.virtual_rate(qi,vi)for qi,vi in zip(q[:,setup['steering_qpos_addresses']],vel[:,setup['steering_qvel_addresses']])]);feature=np.sin((angle[indices]+angle[indices-1])/2)*rate[indices];target=speed[indices]-pole*speed[indices-1]
 assert (ctrl[indices[:,None],np.asarray(setup['actuator_ids'])[None,2:]]==0).all()
 train=18;coefficient=float(feature[:train]@target[:train]/(feature[:train]@feature[:train]));error=target-coefficient*feature
 assert -.1<coefficient<0. and float(abs(error[train:]).max())<=.001,'OLD_HELDOUT_LONGITUDINAL_FIT_REJECTED'
 result=dict(rear_zero_steering_gain=coefficient,feature='sin(mid_virtual_angle)*next_virtual_rate',speed_pole=pole,trained_old_native_indices=(indices[:train]+1).tolist(),heldout_old_native_indices=(indices[train:]+1).tolist(),heldout_one_step_speed_error_m_s=float(abs(error[train:]).max()),maximum_all_one_step_speed_error_m_s=float(abs(error).max()),samples=28,one_scalar_fit=True,first18_fit_last10_heldout=True,full_range_physical_qualification_pending=True,no_physical_model_or_integrations=True)
 dump(C/'COUPLING.json',result);dump(O/'FIT_RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
