"""Three same-budget merge ablations, diagnostics only."""
import os
import time
from common import *
from common import _array


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    target=O/'MERGE_ABLATION.json';assert not target.exists()
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes();begin=time.monotonic()
    lib=ctypes.CDLL(str(O/'libmerge_probe.so'));f=lib.plan_merge_probe
    f.argtypes=ARGUMENTS+[ctypes.c_int,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int)];f.restype=ctypes.c_int
    cases=[]
    for mode in range(3):
        req,args=inputs();output=np.empty((4096,7));stats=np.zeros(16);count=ctypes.c_int()
        collisions=np.zeros((32,12));n=ctypes.c_int()
        code=f(*args,output,len(output),ctypes.byref(count),stats,mode,collisions,len(collisions),ctypes.byref(n))
        row=dict(mode=mode,pose_bins=['original10cm5deg','diagnostic2cm1deg','diagnostic1e-9pose'][mode],
                 code=code,stats=stats.tolist(),path=None if code else output[:count.value].tolist(),
                 collisions=collisions[:n.value].tolist())
        cases.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['path','collisions']}),flush=True)
    result=dict(cases=cases,source_sha256=sha(C/'merge_probe.cpp'),library_sha256=sha(O/'libmerge_probe.so'),
                same22000and1p5s_bounds=True,maximum_saved_unique_collision_states=32,
                models=0,physical_native=0,automatic_physics=False,wall_s=time.monotonic()-begin,
                review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert result['review_pending_unchanged'] and result['current_pointer_unchanged']
    dump(target,result)


if __name__=='__main__':main()
