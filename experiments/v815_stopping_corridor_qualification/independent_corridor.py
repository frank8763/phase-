"""Independent numerical reconstruction of the declared stopping corridor."""
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values

def independent_world(protocol,state):
    boxes=np.asarray(state['outer_state_cells'],float);h=3.28
    pl,pu,vl,vu=boxes[:,0],boxes[:,1],boxes[:,2],boxes[:,3]
    a=np.minimum(pl,np.maximum(pl+h*vl-.02*h*h,pl-.12*h))
    b=np.maximum(pu,np.minimum(pu+h*vu+.02*h*h,pu+.12*h))
    # Unpruned boxes are deliberately used; redundant containment removal
    # cannot change the distance to the union of occupied rectangles.
    return dict(rectangles=[*protocol['known_rectangles'],state['current_outer_rectangle'],*np.c_[(a+b)/2,(b-a)/2+.10].tolist()],
                circles=protocol['known_circles'],sensor_points=[],footprint_bounds=[-.44,-.375,.44,.375],goal=protocol['goal_xy'],start=protocol['start_qpos'][:2])

def independent_field(protocol,state):
    w=independent_world(protocol,state)
    return SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(w['rectangles']).reshape(-1,4),
        circles=np.asarray(w['circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))

def containment(state,corridor_world,known_count):
    cells=np.asarray(state['outer_state_cells']);t=np.arange(1313).reshape(-1,1,1)*(.01/4)
    lo=np.maximum(cells[None,:,0]+t*cells[None,:,2]-.02*t*t,cells[None,:,0]-.12*t)
    hi=np.minimum(cells[None,:,1]+t*cells[None,:,3]+.02*t*t,cells[None,:,1]+.12*t)
    rect=np.asarray(corridor_world['rectangles'][known_count+1:]);lower=rect[:,:2]-rect[:,2:]+.10;upper=rect[:,:2]+rect[:,2:]-.10
    maximum=-np.inf
    for i in range(cells.shape[0]):
        # A single original cell's whole continuous hull is contained in one
        # retained box (possibly a larger box from another cell).
        excess=np.maximum((lower[None]-lo[:,i,None,:]).max(axis=2),(hi[:,i,None,:]-upper[None]).max(axis=2))
        maximum=max(maximum,float(excess.min(axis=1).max()))
    return maximum,len(t)*len(cells)
