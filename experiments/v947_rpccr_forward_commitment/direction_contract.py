"""Ordinary navigation is forward only; reverse recovery has no implicit bypass."""
import math
import numpy as np


class DirectionError(ValueError):
    pass


def classify(path):
    poses=np.asarray(path,float)
    if poses.ndim!=2 or poses.shape[1]!=3 or len(poses)<2 or not np.isfinite(poses).all():
        raise DirectionError('INVALID_REFERENCE')
    delta=np.diff(poses[:,:2],axis=0)
    lengths=np.linalg.norm(delta,axis=1)
    projected=np.sum(delta*np.c_[np.cos(poses[:-1,2]),np.sin(poses[:-1,2])],axis=1)
    moving=lengths>1e-8
    reverse=moving & (projected< -1e-8)
    ambiguous=moving & (abs(projected)<=1e-8)
    return dict(forward_only=bool(not reverse.any()and not ambiguous.any()),
                reverse_segments=int(reverse.sum()),reverse_length_m=float(lengths[reverse].sum()),
                total_length_m=float(lengths.sum()),ambiguous_segments=int(ambiguous.sum()))


def require_forward_path(path):
    result=classify(path)
    if not result['forward_only']:
        raise DirectionError('NORMAL_REFERENCE_CONTAINS_REVERSE_OR_INVALID_GEAR')
    return result


def require_forward_request(v,w):
    if not math.isfinite(v)or not math.isfinite(w):raise DirectionError('NONFINITE_CONTROL')
    if v<0:raise DirectionError('NORMAL_REVERSE_REQUIRES_FORWARD_REPLAN')
    return v,w
