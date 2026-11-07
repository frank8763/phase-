"""Serialization-neutral contact comparison for independent saved-data auditing."""
import math

def contact_equal(actual,expected,tolerance=1e-8):
    if len(actual)!=len(expected):return False
    for a,b in zip(actual,expected):
        if len(a)!=4 or len(b)!=4:return False
        if not isinstance(a[2],str)or not isinstance(b[2],str):return False
        if any(isinstance(v,bool)or not isinstance(v,int)for v in [a[0],a[1],b[0],b[1]]):return False
        if tuple(a[:3])!=tuple(b[:3]):return False
        if not math.isfinite(a[3])or not math.isfinite(b[3])or abs(a[3]-b[3])>tolerance:return False
    return True
