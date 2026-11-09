"""Necessary center connectivity under original margins; geometric outer cover only."""
import gzip,json,math,sys
from collections import deque
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v936_rpccr_corridor_search';sys.path.insert(0,str(C));from corridor_search import Geometry,SPATIAL,RES
S=O/'saved';rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((S/'SETUP.json').read_text())['known'];task=json.loads((S/'TASK.json').read_text());row=[x for x in rows if x['packet']['native_tick']<=7000][-1];start=np.array(row['packet']['body'][:2]);goal=np.array(task['goal_xy']);axis=np.arange(-5+RES/2,5,RES);xx,yy=np.meshgrid(axis,axis);q=np.c_[xx.ravel(),yy.ravel()];radius=RES/math.sqrt(2);reports=[]
for dynamic in[False,True]:
 geom=Geometry(known,row['source']['periodic']if dynamic else None);static=np.minimum(5-abs(q[:,0]),5-abs(q[:,1]))
 for x,y,hx,hy in known['known_rectangles']:
  a=abs(q-[x,y])-[hx,hy];distance=np.where(a.max(axis=1)<=0,a.max(axis=1),np.linalg.norm(np.maximum(a,0),axis=1));static=np.minimum(static,distance)
 for x,y,r in known['known_circles']:static=np.minimum(static,np.linalg.norm(q-[x,y],axis=1)-r)
 distance=static.copy()
 if dynamic:
  poly=geom.center_polygon;edge=np.roll(poly,-1,axis=0)-poly;delta=q[:,None,:]-poly;t=np.clip((delta*edge).sum(axis=2)/(edge*edge).sum(axis=1),0,1);d=np.linalg.norm(delta-t[:,:,None]*edge,axis=2).min(axis=1);cross=edge[None,:,0]*delta[:,:,1]-edge[None,:,1]*delta[:,:,0];d[((cross>=-1e-12).all(axis=1)|(cross<=1e-12).all(axis=1))]=0;distance=np.minimum(distance,d-.1)
 for residual in[.02,.04]:
  reserve=SPATIAL-(.04-residual);required=.375+.155+reserve
  possible=(distance+radius>=required).reshape(xx.shape);seen=np.zeros_like(possible);queue=deque();seeds=possible&(np.hypot(xx-goal[0],yy-goal[1])<=.2+radius)
  for y,x in np.argwhere(seeds):seen[y,x]=True;queue.append((int(y),int(x)))
  while queue:
   y,x=queue.popleft()
   for dy in[-1,0,1]:
    for dx in[-1,0,1]:
     ny,nx=y+dy,x+dx
     if 0<=ny<len(axis)and 0<=nx<len(axis)and possible[ny,nx]and not seen[ny,nx]:seen[ny,nx]=True;queue.append((ny,nx))
  sx,sy=np.floor((start+5)/RES).astype(int);connected=bool(seen[sy,sx]);reports.append(dict(dynamic_whole_cycle=dynamic,original_residual_class_m=residual,center_clearance_necessary_m=required,outer_cover_cell_radius_m=radius,start_in_goal_outer_component=connected,goal_outer_component_cells=int(seen.sum()),statement='Disconnected outer cover excludes continuous center path only under this exact footprint inscribed radius and fixed maximum margin; connected does not prove SE2 or executable path.'))
result=dict(models=0,integrations=0,source_tick=row['packet']['native_tick'],cases=reports);(O/'TOPOLOGY_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
