"""Catch incomplete actual stop tails and forged encoders/actor metadata."""
import copy,json
from pathlib import Path
import numpy as np
from component_contract import final_half_second,actual_packet,sensor_actor
def main():
    velocity=np.zeros((60,8));body=np.zeros((60,5));qpos=np.zeros((60,9));ids=[6,7]
    checks={'full_actual_stop_tail_positive':final_half_second(velocity,body,ids,0)}
    v=velocity.copy();v[-25,0]=.0301
    checks['earlier_translation_above_limit_red_despite_final_zero']=not final_half_second(v,body,ids,0)
    b=body.copy();b[-20,4]=.0301
    checks['earlier_yaw_above_limit_red_despite_final_zero']=not final_half_second(velocity,b,ids,0)
    v=velocity.copy();v[-10,6]=.0301
    checks['earlier_steering_motion_red_despite_final_zero']=not final_half_second(v,body,ids,0)
    checks['short_tail_red']=not final_half_second(velocity,body,ids,11)
    setup=dict(steering_qpos_addresses=[7,8],steering_qvel_addresses=ids)
    packet=dict(native_tick=60,body=[0.]*5,steering=dict(position=[0.,0.],velocity=[0.,0.]))
    checks['actual_encoder_packet_positive']=actual_packet(packet,body,qpos,velocity,setup)
    p=copy.deepcopy(packet);p['steering']['position'][0]=1e-6
    checks['forged_encoder_red']=not actual_packet(p,body,qpos,velocity,setup)
    p=copy.deepcopy(packet);p['native_tick']=61
    checks['unrecorded_native_packet_red']=not actual_packet(p,body,qpos,velocity,setup)
    setup.update(dynamic=True,actor=dict(phase_rad=.6573753567727383,maximum_speed_m_s=.08,amplitude_m=.25,radius_m=.1))
    task=dict(phase=.6573753567727383);sensor=dict(passed=True)
    checks['unchanged_actor_positive']=sensor_actor(sensor,setup,task)
    bad=copy.deepcopy(setup);bad['actor']['phase_rad']+=.001
    checks['changed_actor_phase_red']=not sensor_actor(sensor,bad,task)
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,synthetic_arrays_not_physical_trace=True)
    root=Path(__file__).resolve().parents[2];(root/'runs/v982_precise_recovery_gate/COMPONENT_CONTRACT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
