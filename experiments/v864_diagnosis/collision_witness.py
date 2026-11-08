"""Saved software collision witness using upstream1.3.13 footprint raster semantics, no vehicle/model."""
import gzip,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v864_diagnosis';P=R/'runs/v858_nav2_verified/v864_static/main_ns'
sys.path.insert(0,str(R/'experiments/v791_coherent_global_reference'));from exact_footprint import pose_values
from types import SimpleNamespace

def line(x,y,xx,yy):
 dx,dy=abs(xx-x),abs(yy-y);xi=1 if xx>=x else-1;yi=1 if yy>=y else-1
 if dx>=dy:den=dx;num=dx//2;add=dy;count=dx;x1,y1,x2,y2=0,yi,xi,0
 else:den=dy;num=dy//2;add=dx;count=dy;x1,y1,x2,y2=xi,0,0,yi
 for _ in range(count+1):
  yield x,y
  num+=add
  if num>=den:num-=den;x+=x1;y+=y1
  x+=x2;y+=y2

def footprint(pose,pad):
 x,y,yaw=pose;c,s=math.cos(yaw),math.sin(yaw);p=np.array([[.44+pad,.375+pad],[.44+pad,-.375-pad],[-.44-pad,-.375-pad],[-.44-pad,.375+pad]])
 return p@np.array([[c,s],[-s,c]])+np.array([x,y])
def cost(pose,pad,maprow):
 m=maprow['value'];g=np.asarray(m['data']).reshape(m['height'],m['width']);poly=footprint(pose,pad);grid=np.floor((poly-np.asarray(m['origin']))/m['resolution']).astype(int);cells=[]
 for aa,bb in zip(grid,np.roll(grid,-1,axis=0)):
  for x,y in line(*aa,*bb):
   if not(0<=x<m['width']and 0<=y<m['height']):return dict(cost=254,outside_map=True,cells=[])
   cells.append((int(g[y,x]),int(x),int(y)))
 maxcost=max(v[0]for v in cells);hits=[dict(cost=v,x=x,y=y,world=(np.asarray(m['origin'])+(np.array([x,y])+.5)*m['resolution']).tolist())for v,x,y in set(cells)if v==maxcost]
 return dict(cost=maxcost,cells=hits,outside_map=False)
def main():
 rows=json.loads(gzip.decompress((O/'pb02/TELEMETRY.json.gz').read_bytes()));arc=next(x for x in reversed(rows)if x['kind']=='lookahead_collision_arc');carrot=next(x for x in reversed(rows)if x['kind']=='lookahead_point');m=next(x for x in reversed(rows)if x['kind']=='costmap_raw'and x['at']<=arc['at']);a=np.load(P/'physics/NATIVE_TRACE.npz');tick=arc['tick'];q=a['qpos'][tick-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));xy=np.asarray(carrot['value']['xy']);curvature=float(2*xy[1]/(xy@xy));arcxy=np.asarray(arc['value']['path'][0][:2]);distance=float(np.linalg.norm(arcxy-q[:2]));projected=np.r_[arcxy,yaw+curvature*distance];current=np.r_[q[:2],yaw]
 setup=json.loads((P/'physics/SETUP.json').read_text());k=setup['known'];base=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(k['known_rectangles']),circles=np.asarray(k['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 per=[]
 for i,rect in enumerate(k['known_rectangles']):
  f=SimpleNamespace(**vars(base));f.rectangles=np.array([rect]);f.circles=np.empty((0,3));per.append((float(pose_values(f,[projected])[0]),i,rect))
 result=dict(passed_saved_collision_reproduction=True,models=0,model_integrations=0,software_replay_same_abort104=True,original_physical_run_not_modified=True,recorded_tick=tick,pose=current.tolist(),lookahead_carrot_base=xy.tolist(),curvature_per_m=curvature,first_published_collision_arc_xy=arcxy.tolist(),first_arc_displacement_m=distance,first_arc_orientation_reconstructed=yaw+curvature*distance,latest_received_full_map_tick=m['tick'],map_message_age_s=arc['at']-m['at'],local_map_updates_not_subscribed=True,exact_original_online_map_claim=False,current_padded_cost=cost(current,.15,m),first_projected_padded_cost=cost(projected,.15,m),first_projected_unpadded_cost=cost(projected,0,m),projected_full_unpadded_geometric_clearance_m=float(pose_values(base,[projected])[0]),nearest_known_rectangles=[dict(distance_m=x[0],index=x[1],rectangle=x[2])for x in sorted(per)[:2]],interpretation='RPP abort reproduced with real upstream software on frozen recorded sensing. Received collision arc reaches a padded-footprint lethal raster cell near the static lower central partition. This is a local-plan/curvature/footprint-raster consistency problem; no evidence of a motor failure or navigation wall-time shortage. This snapshot alone does not establish the unique source of every online occupied cell.')
 assert result['first_projected_padded_cost']['cost']>=254,'SAVED_COLLISION_NOT_REPRODUCED'
 (O/'COLLISION_WITNESS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 # Shareable static evidence figure, drawn from saved states/maps only.
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 from matplotlib.patches import Polygon,Rectangle
 fig,ax=plt.subplots(figsize=(7.6,5.8));local=m['value'];g=np.asarray(local['data']).reshape(local['height'],local['width']);y,x=np.where(g>=254);wx=local['origin'][0]+(x+.5)*local['resolution'];wy=local['origin'][1]+(y+.5)*local['resolution'];ax.scatter(wx,wy,s=5,c='0.7',label='Received lethal cells')
 for rect in k['known_rectangles']:ax.add_patch(Rectangle((rect[0]-rect[2],rect[1]-rect[3]),2*rect[2],2*rect[3],fill=False,edgecolor='black',linewidth=1))
 ax.plot(a['qpos'][:,:1],a['qpos'][:,1],color='tab:blue',linewidth=1.7,label='Actual vehicle path')
 plan=json.loads((P/'PLANS.json').read_text())[-1]['path'];plan=np.asarray(plan);ax.plot(plan[:,0],plan[:,1],'g--',label='Last global reference')
 for pose,pad,color,name in [(current,.15,'tab:blue','Current padded footprint'),(projected,.15,'tab:red','First projected padded footprint'),(projected,0,'tab:orange','Projected full body bound')]:ax.add_patch(Polygon(footprint(pose,pad),closed=True,fill=False,edgecolor=color,linewidth=1.8,label=name))
 ax.set(xlim=(-1.8,.8),ylim=(-2.1,.3),xlabel='x (m)',ylabel='y (m)',title='V864 NS: saved RPP collision witness\nPure software playback; no additional physics');ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower left');fig.tight_layout();fig.savefig(O/'COLLISION_WITNESS.png',dpi=170);plt.close(fig)
if __name__=='__main__':main()
