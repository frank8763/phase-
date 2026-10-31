"""Scene construction only: synchronize sensor geometry with the physical world.
Not imported by the planner or predictor; the hidden circle reaches them only as ranges.
"""
import numpy as np

def synchronize_sensor_arrays(env,rect,circ,event):
    physical_circles=np.vstack((np.asarray(circ).reshape(-1,3),np.asarray(event).reshape(1,3))).astype(np.float32)
    physical_rects=np.asarray(rect,dtype=np.float32).reshape(-1,4)
    owners=[]
    for obj in env._phase19_object_chain():
        local=object.__getattribute__(obj,'__dict__');record={'owner_type':type(obj).__module__+'.'+type(obj).__name__}
        changed=False
        for key,expected in [('circle_obstacles',physical_circles),('rect_obstacles',physical_rects)]:
            if key not in local:continue
            before=np.asarray(local[key]).copy();record[key+'_before']=before.tolist();record[key+'_after']=expected.tolist()
            local[key]=expected.copy();changed=True
        if changed:owners.append(record)
    assert owners,'NO_SENSOR_GEOMETRY_OWNERS'
    return {'scope':'scene generator and sensor backend only; not a planner truth input','owners':owners}
