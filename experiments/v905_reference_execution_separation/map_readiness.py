"""Require an actual complete known global master before native ARM; no model."""
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def required_static_mask():
    payload=(R/'experiments/v881_timing_accounting_continuation/field.pgm').read_bytes()
    magic,shape,maximum,data=payload.split(b'\n',3)
    assert magic==b'P5'and shape==b'1000 1000'and maximum==b'255'
    return np.flipud(np.frombuffer(data,np.uint8).reshape(1000,1000))==0
STATIC=required_static_mask()
def inspect_map(message):
    meta=message.metadata;data=np.asarray(message.data,np.uint8)
    shape_ok=meta.size_x==1000 and meta.size_y==1000 and len(data)==1000000
    frame_ok=message.header.frame_id=='map'
    metric_ok=abs(meta.resolution-.01)<1e-8 and abs(meta.origin.position.x+5.)<1e-8 and abs(meta.origin.position.y+5.)<1e-8
    unknown=int(np.sum(data==255))
    missing=int(np.sum(data.reshape(1000,1000)[STATIC]!=254))if shape_ok else None
    return dict(passed=bool(shape_ok and frame_ok and metric_ok and unknown==0 and missing==0),size_x=meta.size_x,size_y=meta.size_y,resolution=meta.resolution,origin=[meta.origin.position.x,meta.origin.position.y],frame=message.header.frame_id,cells=len(data),unknown_cells=unknown,required_static_cells=int(np.sum(STATIC)),missing_static_cells=missing,all_unknown=unknown==len(data),models=0)
