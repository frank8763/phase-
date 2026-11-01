"""Explicit diagnosis boundary: evaluator discloses only position/velocity NOW."""
import math,json
import numpy as np
ROLE='ORACLE_CURRENT_STATE_ONLY'

def evaluator_current_packet(actor,now):
    # Privileged diagnostic only. Never query another time or return config.
    config=actor.config
    position=actor.xy(float(now))
    velocity=np.cos(float(now)*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy'])
    return {'time':float(now),'position':position.tolist(),'velocity':velocity.tolist()}

def state_from_packet(packet):
    assert set(packet)=={'time','position','velocity'},'UNDECLARED_ORACLE_INFORMATION'
    p=np.asarray(packet['position'],float);v=np.asarray(packet['velocity'],float)
    assert p.shape==v.shape==(2,) and np.isfinite(np.r_[p,v,packet['time']]).all()
    return {'time':float(packet['time']),'center':p.tolist(),'velocity':v.tolist(),
        'position_lower':p.tolist(),'position_upper':p.tolist(),'velocity_lower':v.tolist(),'velocity_upper':v.tolist(),
        'outer_state_cells':[[p.tolist(),p.tolist(),v.tolist(),v.tolist()]],'current_outer_rectangle':[*p,.10,.10],
        'age_s':0.,'observed_this_frame':False,'privileged_state_received_this_frame':True,'certified_unknown_rays':0,
        'information_role':ROLE,'hidden_world_geometry_used':True,'scope':'privileged exact current position/velocity only; unchanged bounded-motion future, no future observations or sweep parameters'}

def marked(record):
    result=json.loads(json.dumps(record,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item()))
    def visit(value):
        if isinstance(value,dict):
            if 'hidden_world_geometry_used'in value:value['hidden_world_geometry_used']=True
            for child in value.values():visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    visit(result);result.update(information_role=ROLE,hidden_world_geometry_used=True)
    return result
