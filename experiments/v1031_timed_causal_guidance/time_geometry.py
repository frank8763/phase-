"""Analytic extrema of every causal coefficient vertex over native intervals."""
import math
import numpy as np
def interval_support(vertices,starts,ends):
    starts=np.asarray(starts,float);ends=np.asarray(ends,float);result=[]
    for v in vertices:
        p=np.asarray(v,float);a=p[:,1];b=p[:,2];phase=np.arctan2(a,b);radius=np.hypot(a,b)
        left=p[:,0]+np.sin(.32*starts[:,None])*a+np.cos(.32*starts[:,None])*b
        right=p[:,0]+np.sin(.32*ends[:,None])*a+np.cos(.32*ends[:,None])*b
        upper=np.maximum(left,right);lower=np.minimum(left,right)
        for offset,ismax in [(0.,True),(math.pi,False)]:
            k=np.ceil((.32*starts[:,None]-phase-offset)/(2*math.pi));at=(phase+offset+2*math.pi*k)/.32
            mask=at<=ends[:,None]+1e-12;extreme=p[:,0]+(radius if ismax else-radius)
            if ismax:upper=np.where(mask,np.maximum(upper,extreme),upper)
            else:lower=np.where(mask,np.minimum(lower,extreme),lower)
        result.append((upper.max(axis=1)+2e-7,-lower.min(axis=1)+2e-7))
    return np.column_stack([x[0]for x in result]+[x[1]for x in result])
