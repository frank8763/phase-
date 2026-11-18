"""Same causal data/motion class; coupled six-coefficient confidence polytope."""
import sys,json,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1128_timed_terminal_source'));from timed_source import Timed as OriginalTimed,final_gate as original_gate,ref,REQUIRED,NORMALS
from exact_timed import pg
from cycle_backup import cycle_upper
import numpy as np
class Geometry:
 def __init__(self,x,table):
  self.x=x;self.table=table;self.original=OriginalTimed(x);self.period=self.original.period;self.bounds=table['bounds'];self.centers=table['centers'];self.width=self.period/len(self.centers);self.static=self.original.static;self.cycle_bounds=np.minimum(cycle_upper(x['source']['periodic'])+1e-6,self.bounds.max(axis=0));self.cycle_polygon=pg.polygon(self.cycle_bounds);self.polygons=[pg.polygon(b)for b in self.bounds]
 def upper(self,ticks):
  time=(self.original.start+.01*np.asarray(ticks))%self.period;j=np.minimum((time/self.width).astype(int),len(self.centers)-1);i=np.minimum((time/self.original.width).astype(int),len(self.original.edges)-1);return np.minimum(self.bounds[j],self.original.bounds[i])
 def components(self,poses,ticks):
  p=np.asarray(poses);b=self.upper(ticks);yaw=p[:,2,None];low=p[:,:2]@NORMALS.T-.44*abs(np.cos(yaw)*NORMALS[:,0]+np.sin(yaw)*NORMALS[:,1])-.375*abs(-np.sin(yaw)*NORMALS[:,0]+np.cos(yaw)*NORMALS[:,1]);return self.static.clearances(p)[0],(low-b-.1).max(axis=1)
 def cycle(self,poses):
  p=np.asarray(poses);return np.minimum(self.static.clearances(p)[0],pg.distances(p,self.cycle_polygon)-.1-2e-6)
 def final(self,x,ss,uu,rows):
  if x['packet']['sim_time']!=self.x['packet']['sim_time']:
   import copy
   clone=copy.copy(self);clone.x=x;clone.original=copy.copy(self.original);clone.original.start=float(x['packet']['sim_time']);return clone.final(x,ss,uu,rows)
  proof,rr=original_gate(x,ss,uu,rows);a,b=self.components(ss[:,:3],np.arange(len(ss)));low=float(np.minimum(a,b).min());proof.update(minimum_raw_m=low,minimum_timed_raw_m=low,minimum_static_m=float(a.min()),minimum_timed_dynamic_m=float(b.min()),terminal_full_cycle_raw_m=float(self.cycle(ss[-1:,:3])[0]),coupled_coefficient_domain=True);proof['checks']['full_raw_geometry']=low>=REQUIRED;proof['checks']['terminal_full_cycle_hold']=self.cycle(ss[-1:,:3])[0]>=REQUIRED;cursor=0;envelopes=[];okay=True
  for target,speed,ticks,mode in rows:
   ticks=int(ticks)
   if mode:
    anchor=ss[cursor,:3];lower=float(self.cycle(anchor[None,:])[0])-.02-np.hypot(.44,.375)*.1;phase=ss[cursor:cursor+ticks+1];inside=np.linalg.norm(phase[:,:2]-anchor[:2],axis=1).max()<=.02 and abs(np.arctan2(np.sin(phase[:,2]-anchor[2]),np.cos(phase[:,2]-anchor[2]))).max()<=.1 and abs(phase[:,3]).max()+.002<=.01;one=bool(lower>=REQUIRED and inside);okay&=one;envelopes.append({'native':cursor,'raw_envelope_lower':lower,'passed':one})
   cursor+=ticks
  proof['checks']['coupled_mode_envelopes']=okay;proof['mode_envelopes']=envelopes;proof['passed']=bool(all(proof['checks'].values()));return proof,rr
