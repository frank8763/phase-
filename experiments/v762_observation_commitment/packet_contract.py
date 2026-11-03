"""Exact original sensor fields, with separately reconstructed derived rays."""
import math
import numpy as np
FIELDS={'step','time','xy','yaw','lidar','depth','lidar_max_range','depth_max_range'}
def derived_rays(p):
    rows=[]
    for name,b,sigma in [('lidar',.06,.02),('depth',.09,.03)]:
        z=np.clip(np.asarray(p[name],float),0.,1.)*p[name+'_max_range'];R=p[name+'_max_range']
        angles=(np.arange(len(z))*2*np.pi/len(z)if name=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(z)))+p['yaw'];keep=(z>.05)&(z<R-b-1e-5)
        rows.extend([[*p['xy'],np.cos(a),np.sin(a),v,b,sigma]for a,v in zip(angles[keep],z[keep])])
    return np.asarray(rows,dtype=float).reshape(-1,7)
def number(x):
    return type(x)in(int,float)and math.isfinite(x)
def raw_packet(p):
    assert type(p)is dict and set(p)in(FIELDS,FIELDS|{'rays'}),'PACKET_FIELDS_CHANGED'
    assert type(p['step'])is int and p['step']>=0
    assert all(number(p[k])for k in ['time','yaw','lidar_max_range','depth_max_range'])and p['time']>=0
    assert p['lidar_max_range']==3. and p['depth_max_range']==3.
    for key,size in [('xy',2),('lidar',32),('depth',15)]:
        assert type(p[key])is list and len(p[key])==size and all(number(x)for x in p[key]),'PACKET_VECTOR_CHANGED'
    assert all(0.<=x<=1. for key in ['lidar','depth']for x in p[key])
    if 'rays'in p:
        rows=p['rays'];assert type(rows)is list
        assert all(type(row)is list and len(row)==7 and all(number(x)for x in row)for row in rows),'RAYS_SCHEMA_CHANGED'
        observed=np.asarray(rows,float).reshape(-1,7);assert np.array_equal(observed,derived_rays(p)),'DERIVED_RAYS_CHANGED'
    return {key:p[key]for key in FIELDS}
def packet_equal(a,b):
    try:return raw_packet(a)==raw_packet(b)
    except (AssertionError,TypeError,ValueError,OverflowError):return False
