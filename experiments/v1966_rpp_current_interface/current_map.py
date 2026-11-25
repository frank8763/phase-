"""Causal public-map/current-ray frontend for unchanged original RPP CABI."""
import math,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
PUBLIC=R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json'
PARAMS=R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def rear(body):
 assert len(body)==5 and all(math.isfinite(v)for v in body)
 x,y,yaw,v,w=body;return [x-.3*math.cos(yaw),y-.3*math.sin(yaw),yaw,v,w]
def inscribed_radius(foot):
 values=[]
 for a,b in zip(foot,foot[1:]+foot[:1]):
  dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy;assert den>0
  t=max(0.,min(1.,-(a[0]*dx+a[1]*dy)/den));values.append(math.hypot(a[0]+t*dx,a[1]+t*dy))
 return min(values)
def cost(distance_cells,res,inscribed,scale=4.):
 if distance_cells==0:return 254
 if distance_cells*res<=inscribed:return 253
 return int(252*math.exp(-scale*(distance_cells*res-inscribed)))
def inflate(np,raw,res,inscribed,radius=.85,scale=4.):
 assert raw.dtype==np.uint8 and raw.ndim==2
 h,w=raw.shape;lethal=raw==254;minimum=np.full((h,w),10**9,dtype=np.int32);cap=math.ceil(radius/res)
 for dy in range(-cap,cap+1):
  for dx in range(-cap,cap+1):
   sq=dx*dx+dy*dy
   if sq>cap*cap:continue
   ys=max(0,-dy);ye=min(h,h-dy);xs=max(0,-dx);xe=min(w,w-dx)
   source=lethal[ys:ye,xs:xe];target=minimum[ys+dy:ye+dy,xs+dx:xe+dx];np.minimum(target,np.where(source,sq,10**9),out=target)
 lut=np.array([cost(math.sqrt(i),res,inscribed,scale)for i in range(cap*cap+1)],dtype=np.uint8)
 valid=minimum<=cap*cap;out=raw.copy();computed=lut[np.minimum(minimum,cap*cap)]
 # Nav2 preserves no-information unless lethal/inscribed inflation reaches it.
 update=valid&((raw!=255)|(computed>=253));out[update]=np.maximum(np.where(raw[update]==255,0,raw[update]),computed[update]);return out
class Frontend:
 def __init__(self,np,*,public_sha256,parameter_sha256):
  assert sha(PUBLIC)==public_sha256 and sha(PARAMS)==parameter_sha256,'RPP_FRONTEND_SOURCE_CHANGED'
  self.np=np;self.public=json.loads(PUBLIC.read_text());self.params=json.loads(PARAMS.read_text());self.config=self.params['local_costmap']['local_costmap']['ros__parameters'];self.foot=json.loads(self.config['footprint']);self.radius=inscribed_radius(self.foot)
  assert len(self.foot)==36 and self.config['resolution']==.05 and self.config['width']==self.config['height']==6 and self.config['footprint_padding']==0.
  assert self.config['inflation_layer']['inflation_radius']==.85 and self.config['inflation_layer']['cost_scaling_factor']==4.
  self.last=-1;self.used=set()
 def build(self,request):
  np=self.np;allowed={'schema','run_id','method','native_tick','sim_time','body','steering','controller_memory','scan','goal_xy','public_route','measurement_source_packet_sha256','motion_class_prior_only','physical_authority'}
  assert set(request)==allowed and request['schema']=='PHASE_CURRENT_SOLVER_INPUT_V1'and request['method']=='RPP'and request['physical_authority']is False,'RPP_FRONTEND_UNDECLARED_INPUT'
  tick=request['native_tick'];assert type(tick)is int and tick>=0 and tick>self.last,'RPP_FRONTEND_ORIGIN_ONCE'
  assert abs(request['sim_time']-.01*tick)<=1e-8;scan=request['scan'];assert set(scan)=={'native_tick','time','xy','yaw','ranges'}and 0<=tick-scan['native_tick']<=5 and abs(scan['time']-.01*scan['native_tick'])<=1e-8,'RPP_FRONTEND_SCAN_CLOCK'
  assert len(scan['ranges'])==32 and len(scan['xy'])==2 and all(math.isfinite(v)and 0<=v<=3 for v in scan['ranges'])
  body=request['body'];p=rear(body);res=.05;grid=self.public;origin=[grid['origin'][i]+math.floor((p[i]-3-grid['origin'][i])/res)*res for i in range(2)];x=origin[0]+(np.arange(120)+.5)*res;y=origin[1]+(np.arange(120)+.5)*res;gx=np.floor((x-grid['origin'][0])/res).astype(int);gy=np.floor((y-grid['origin'][1])/res).astype(int);inside=(gy[:,None]>=0)&(gy[:,None]<grid['height'])&(gx[None,:]>=0)&(gx[None,:]<grid['width']);public=np.asarray(grid['data'],dtype=np.int16).reshape(grid['height'],grid['width']);raw=np.full((120,120),255,dtype=np.uint8);values=public[np.clip(gy,0,grid['height']-1)[:,None],np.clip(gx,0,grid['width']-1)[None,:]];raw[inside]=np.where(values[inside]==100,254,np.where(values[inside]==-1,255,0))
  hits=[]
  for i,value in enumerate(scan['ranges']):
   if .05<=value<=2.99:
    a=scan['yaw']+i*math.tau/32;hx=scan['xy'][0]+value*math.cos(a);hy=scan['xy'][1]+value*math.sin(a);cx=math.floor((hx-origin[0])/res);cy=math.floor((hy-origin[1])/res)
    if 0<=cx<120 and 0<=cy<120:raw[cy,cx]=254;hits.append([cx,cy])
  result=inflate(np,raw,res,self.radius);self.last=tick
  return dict(schema='RPP_CURRENT_CAUSAL_COSTMAP_V1',origin=origin,width=120,height=120,resolution=res,raw_cells=raw.ravel().tolist(),cells=result.ravel().tolist(),rear_pose_speed=p,footprint_xy=self.foot,source_request_sha256=digest(request),source_receipt_packet_sha256=request['measurement_source_packet_sha256'],native_tick=tick,scan_native_tick=scan['native_tick'],scan_marked_cells=hits,inscribed_radius_m=self.radius,public_map_sha256=sha(PUBLIC),parameter_sha256=sha(PARAMS),inflation_radius=.85,inflation_scale=4.,engineering_adaptation='SYNCHRONOUS_PUBLIC_GRID_ALIGNED_WINDOW_PLUS_CURRENT_32RAY',native_original_controller_parameters_unchanged=True)
