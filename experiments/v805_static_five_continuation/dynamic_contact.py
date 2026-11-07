"""Static scene contact catalog; explicit zero-actor construction only."""
from contact_contract import GeometryCatalog as StaticCatalog,ContactRecorder
class GeometryCatalog(StaticCatalog):
 def __init__(self,m,mj,xml):
  assert m.nmocap==0 and mj.mj_name2id(m,mj.mjtObj.mjOBJ_BODY,'phase_dynamic_actor')==-1
  gid=mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,'real_circle_obs_10');assert gid>=0 and int(m.geom_contype[gid])==int(m.geom_conaffinity[gid])==0
  super().__init__(m,mj,xml)
