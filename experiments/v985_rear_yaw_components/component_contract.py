"""Offline actual terminal/encoder and actor contracts, no model imports."""
import numpy as np

def final_half_second(velocity,body,steering_ids,origin):
    count=len(body)
    return bool(count-origin>=50 and np.linalg.norm(velocity[-50:,:2],axis=1).max()<=.03 and abs(body[-50:,4]).max()<=.03 and abs(velocity[-50:,steering_ids]).max()<=.03)

def actual_packet(packet,body,qpos,qvel,setup):
    i=packet['native_tick']-1
    return bool(0<=i<len(body)and np.max(abs(np.asarray(packet['body'])-body[i]))<=1e-8 and np.max(abs(np.asarray(packet['steering']['position'])-qpos[i,setup['steering_qpos_addresses']]))<=1e-8 and np.max(abs(np.asarray(packet['steering']['velocity'])-qvel[i,setup['steering_qvel_addresses']]))<=1e-8)

def sensor_actor(sensor,setup,task):
    return bool(sensor['passed']and setup['dynamic']and setup['actor']['phase_rad']==task['phase']and setup['actor']['maximum_speed_m_s']==.08 and setup['actor']['amplitude_m']==.25 and setup['actor']['radius_m']==.1)
