"""Scoped memoization of identical, pure confidence-domain extrema.

Only complete byte-identical inputs share results; absolute clock isn't an
argument to interval_support, only the later lookup. Cache lifetime is a single
selection and original global binding is restored even on error.
"""
from contextlib import contextmanager
from collections import OrderedDict
import numpy as np

@contextmanager
def interval_cache(q):
 timed=q.Geometry.__init__.__globals__['OriginalTimed']
 env=timed.__init__.__globals__;original=env['interval_support'];cache=OrderedDict();stats=dict(hits=0,misses=0,pose_hits=0,pose_misses=0,distance_hits=0,distance_misses=0)
 def cached(vertices,starts,ends):
  arrays=[np.asarray(a)for a in [*vertices,starts,ends]]
  key=tuple((a.dtype.str,a.shape,np.ascontiguousarray(a).tobytes())for a in arrays)
  if key in cache:stats['hits']+=1;cache.move_to_end(key);return cache[key]
  stats['misses']+=1;value=original(vertices,starts,ends);value.setflags(write=False);cache[key]=value
  if len(cache)>8:cache.popitem(last=False)
  return value
 geom=q.Geometry.__init__.__globals__['ref']._old.Geometry
 genv=geom.clearances.__globals__;pose_original=genv['pose_values'];distance_original=genv['distances'];pcache=OrderedDict();dcache=OrderedDict()
 def arraykey(a):
  a=np.asarray(a);return a.dtype.str,a.shape,np.ascontiguousarray(a).tobytes()
 def pose_cached(field,poses):
  key=(tuple(arraykey(getattr(field,k))for k in ['half','center_local','rectangles','circles','sensor_points']),float(field.sensor_extra),float(field.config.lower),float(field.config.upper),arraykey(poses))
  if key in pcache:stats['pose_hits']+=1;pcache.move_to_end(key);return pcache[key]
  stats['pose_misses']+=1;value=pose_original(field,poses);value.setflags(write=False);pcache[key]=value
  if len(pcache)>32:pcache.popitem(last=False)
  return value
 def distance_cached(poses,polygon):
  key=(arraykey(poses),arraykey(polygon))
  if key in dcache:stats['distance_hits']+=1;dcache.move_to_end(key);return dcache[key]
  stats['distance_misses']+=1;value=distance_original(poses,polygon);value.setflags(write=False);dcache[key]=value
  if len(dcache)>32:dcache.popitem(last=False)
  return value
 pg=q.Geometry.__init__.__globals__['pg'];pg_original=pg.distances
 env['interval_support']=cached;genv['pose_values']=pose_cached;genv['distances']=distance_cached
 try:yield stats
 finally:
  assert env['interval_support']is cached,'INTERVAL_CACHE_BINDING_CHANGED'
  env['interval_support']=original;genv['pose_values']=pose_original;genv['distances']=distance_original
