"""Independent finite stdlib-only interface work; never a numerical method run."""
from pathlib import Path
import ast,copy,hashlib,json,math,os,resource,struct,sys,time,traceback,zlib
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
CPUS={'PSF':0,'SCCR':1,'PRIEST':3};METHODS=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF']
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def allocated(p):return sum(x.stat().st_blocks*512 for x in p.rglob('*')if x.is_file()and not x.is_symlink())
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<256*1024 and allocated(S)+len(raw)<1024**2
 assert not p.exists();p.write_bytes(raw)
pins={}
def read_bytes(p):
 b=p.read_bytes();pins[str(p.relative_to(R))]=sha(b);return b
def read(p):return json.loads(read_bytes(p))

def pack(rows):
 raw=bytearray()
 for n,b in rows:
  name=n.encode();assert '/'not in n and n.endswith('.json')and len(name)<=128 and len(b)<=1024**2
  raw.extend(struct.pack('!HI',len(name),len(b)));raw.extend(name);raw.extend(b)
 return zlib.compress(bytes(raw),3)
def unpack(blob):
 d=zlib.decompressobj();raw=d.decompress(blob,32*1024**2+1);assert len(raw)<=32*1024**2 and d.eof and not d.unused_data
 i=0;out=[]
 while i<len(raw):
  assert i+6<=len(raw);a,b=struct.unpack('!HI',raw[i:i+6]);i+=6;assert 0<a<=128 and b<=1024**2 and i+a+b<=len(raw)
  name=raw[i:i+a].decode();i+=a;assert '/'not in name and name.endswith('.json');out.append((name,raw[i:i+b]));i+=b
 assert len({n for n,_ in out})==len(out);return out
def codec():
 o=R/'runs/v2137_psf_progress_control';assert read(o/'DISPATCH_RESULT.json')['finite_queue_completed']and read(o/'components/PSF/POST_COMPONENT_STORAGE_BARRIER.json')['passed'];a=o/'components/PSF/actual'
 rows=[]
 for i in range(32):
  names=[f'FILTER_QUERY_{i:03d}_{x}.json'for x in ['INPUT','WIRE','RESULT','ROUTE','PROPOSAL']]+[f'cycle_{i:06d}_{x}.json'for x in ['origin','shadow','admission_0']]
  for n in names:rows.append((n,read_bytes(a/n)))
 blob=pack(rows);assert len(blob)<=512*1024;decoded=unpack(blob);assert decoded==rows
 rejects=[]
 for name,b in [('truncated',blob[:-1]),('corrupted',blob[:len(blob)//2]+bytes([blob[len(blob)//2]^1])+blob[len(blob)//2+1:])]:
  try:unpack(b)
  except(AssertionError,zlib.error):rejects.append(name)
  else:raise AssertionError('CODEC_NEGATIVE_ACCEPTED:'+name)
 try:pack([('../foreign.json',b'{}')])
 except AssertionError:rejects.append('foreign_path')
 else:raise AssertionError('CODEC_PATH_ACCEPTED')
 p=S/'PSF'/'metadata_32cycles.zlib';assert not p.exists()and allocated(S)+len(blob)<1024**2;p.write_bytes(blob)
 actual=allocated(a);component_logical=sum(x.stat().st_size for x in a.rglob('*')if x.is_file());original_blocks=sum((a/n).stat().st_blocks*512 for n,_ in rows)
 return dict(passed=True,scope='LOSSLESS_METADATA_CODEC_ONLY_NOT_PRODUCTION_ADMISSION',saved_cycles=32,original_members=len(rows),logical_bytes=sum(len(b)for _,b in rows),allocated_original_member_bytes=original_blocks,packed_bytes=len(blob),every_member_original_bytes_exact=True,negative_cases=rejects,actual_component_allocated_bytes=actual,actual_component_logical_bytes=component_logical,naive_2500query_allocated_projection_bytes=actual*10,original_task_cap_bytes=224*1024**2,naive_linear_projection_fits_original_task=actual*10<=224*1024**2,linear_projection_not_peak_or_admission=True,physical_writer_audit_and_recovery_integration_qualified=False,codec_sha256=sha(blob))

BLOCKS={'rendered_depth24':24,'phase6_camera_goal':5,'phase7_depth_summary':20,'phase17_camera_goal':5,'phase17_depth_summary':20}
class Consumer:
 def __init__(self,method,producer):assert method in METHODS;self.last=-1;self.producer=producer
 def receive(self,z,expected):
  assert set(z)=={'schema','software_fixture','physical_authority','native','sim_time','producer_sha256','scans','camera_depth','rendered_depth_available','packet_sha256'}
  assert z['schema']=='EQUAL_FULL_SENSOR_DRAFT_V1'and z['software_fixture']and not z['physical_authority']and z['rendered_depth_available']is True
  assert type(z['native'])is int and z['native']==expected>self.last and abs(z['sim_time']-.01*expected)<=1e-8 and z['producer_sha256']==self.producer
  clean=dict(z);assert clean.pop('packet_sha256')==digest(clean)
  assert {k:len(v)for k,v in z['camera_depth'].items()}==BLOCKS and {k:len(v)for k,v in z['scans'].items()}=={'core36':36,'phase6_32':32,'phase17_32':32}
  assert all(type(v)in(int,float)and math.isfinite(v)for group in [z['scans'],z['camera_depth']]for a in group.values()for v in a)
  self.last=expected;return copy.deepcopy((z['scans'],z['camera_depth']))
def sensors():
 inventory=read(R/'runs/v2138_sccr_complete_sensor_inventory/RESULT.json');binding=read(R/'runs/v2138_sccr_complete_sensor_inventory/CAMERA_BINDING_SUPPLEMENT.json');assert inventory['passed']and inventory['total_direct_camera_depth_feature_dims']==74 and binding['new_candidate_is_not_admitted']
 producer=digest(inventory['source_SHA256']);consumers=[Consumer(m,producer)for m in METHODS];rows=[];first=None
 for i in range(20):
  z=dict(schema='EQUAL_FULL_SENSOR_DRAFT_V1',software_fixture=True,physical_authority=False,native=5*i,sim_time=.05*i,producer_sha256=producer,scans={k:[1. if i==0 else (j+i)%31/31 for j in range(n)]for k,n in [('core36',36),('phase6_32',32),('phase17_32',32)]},camera_depth={k:[1. if i==0 else(j+i)%19/19 for j in range(n)]for k,n in BLOCKS.items()},rendered_depth_available=True);z['packet_sha256']=digest(z)
  got=[c.receive(z,5*i)for c in consumers];assert all(x==got[0]for x in got);rows.append(dict(native=5*i,packet_sha256=z['packet_sha256'],all10_equal_access=True));first=first or z
 rejects=[]
 cases=[];z=dict(first,rendered_depth_available=False);z['packet_sha256']=digest({k:v for k,v in z.items()if k!='packet_sha256'});cases.append(('missing_render_not_real_clear_range',z,0))
 z=dict(first,actor_xy=[0.,0.]);cases.append(('truth_field',z,0));z=copy.deepcopy(first);z['camera_depth']['rendered_depth24'].pop();z['packet_sha256']=digest({k:v for k,v in z.items()if k!='packet_sha256'});cases.append(('missing_rendered_feature',z,0));cases.append(('future_or_stale_tick',first,5))
 for label,z,k in cases:
  try:Consumer('SCCR',producer).receive(z,k)
  except(AssertionError,KeyError,ValueError):rejects.append(label)
  else:raise AssertionError('SENSOR_NEGATIVE_ACCEPTED:'+label)
 return dict(passed=True,scope='FULL_SENSOR_PACKET_SEAM_SOFTWARE_ONLY',synthetic_packets=20,consumers=10,camera_depth_dimensions=74,scan_dimensions=[36,32,32],all_equal_access=True,legitimate_all_ones_accepted_with_availability=True,negative_cases=rejects,rows=rows,actual_sensor_acquisitions=0,original186_builder_qualified=False,frozen_policy_inferences=0,actual_camera_binding_qualified=False)

def priest():
 a=R/'runs/v2122_priest_quiescent_handoff/vehicle/actual';request=read(a/'PRIEST_OPTIMIZER_REQUEST.json');receipt=read(a/'cycle_000000_origin.json')['receipt']['packet'];p=R/'experiments/v2137_psf_progress_control/geometry.py';tree=ast.parse(read_bytes(p));assigns=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in {'HX','HY','RHO','SPATIAL','REQUIRED'}for t in n.targets)];space=dict(math=math);exec(compile(ast.Module(body=assigns,type_ignores=[]),str(p),'exec'),space);required=space['REQUIRED']
 radius=math.hypot(.11,.375);guard=required+.05/math.sqrt(2);offsets=[-.33,-.11,.11,.33];body=receipt['body'];points=request['static_points_world'];assert len(points)==50
 worst=0.
 for i in range(512):
  yaw=2*math.pi*i/512;c,s=math.cos(yaw),math.sin(yaw)
  for centre in offsets:
   for dx in [-.11,.11]:
    for y in [-.375,.375]:
     x=centre+dx;px=x*c-y*s;py=x*s+y*c;cx=centre*c;cy=centre*s;worst=max(worst,math.hypot(px-cx,py-cy)-radius)
 assert worst<=1e-14
 yaw=body[2];c,s=math.cos(yaw),math.sin(yaw);centres=[[body[0]+x*c,body[1]+x*s]for x in offsets];margins=[math.dist(center,point)-(radius+guard)for center in centres for point in points];violations=sum(x<0 for x in margins)
 return dict(passed=True,scope='FOUR_DISC_GEOMETRIC_INITIAL_ADMISSION_DIAGNOSIS_ONLY',disc_count=4,body_half_extents_m=[.44,.375],disc_offsets_body_x_m=offsets,unexpanded_disc_radius_m=radius,original_required_clearance_m=required,original_grid_cell_uncertainty_m=.05/math.sqrt(2),expanded_radius_m=radius+guard,heading_enclosure_cases=512,maximum_enclosure_error_m=worst,initial_constraints=len(margins),initial_violations=violations,minimum_initial_margin_m=min(margins),initial_geometry_feasible=violations==0,old_single_circle_failure_not_overwritten=True,author_optimizer_yaw_coupling_qualified=False,optimizer_calls=0,vehicle_qualified=False,no_disc_count_or_radius_search=True)

def main():
 method=sys.argv[1];assert method in CPUS and os.sched_getaffinity(0)=={CPUS[method]};resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(110,120));o=S/method;o.mkdir(exist_ok=False);put(o/'ONCE.json',dict(pid=os.getpid(),CPU=CPUS[method],unix=time.time(),models=0,optimizer_calls=0));start=time.monotonic()
 result=dict(passed=False,closed=False,method=method,models=0,policy_inferences=0,renderers=0,optimizer_calls=0,physics=0,replay=0,formal_tasks=0)
 try:
  result.update({'PSF':codec,'SCCR':sensors,'PRIEST':priest}[method]());assert all(sha((R/n).read_bytes())==h for n,h in pins.items());result['all_inputs_unchanged']=True
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 result.update(closed=True,wall_s=time.monotonic()-start,input_SHA256=pins,source_SHA256={str(p.relative_to(R)):sha(p.read_bytes())for p in C.iterdir()if p.is_file()});put(o/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['input_SHA256','source_SHA256','rows','traceback']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
