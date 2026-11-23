"""Fixed author-core qualification scope; no physical or benchmark authority."""
from pathlib import Path
import hashlib,importlib.util,json,math,os,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
REVIEW_SHA='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 p=Path(p);data=(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 assert len(data)<=1024**2,'METADATA_ONE_MIB_CAP'
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(data);t.replace(p)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def usage():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def validate(a,*,wall,mono,boot,freeze_sha,input_sha):
 assert a['scope']=='SVG_AUTHOR_CORE_ONCE_STATIC_SAVED_INPUT'and a['numerical_authorized']is True,'NUMERIC_SCOPE'
 assert a['physical_authorized']is False and a['benchmark_authorized']is False,'PHYSICAL_OR_BENCHMARK_AUTHORITY'
 assert a['boot_id']==boot,'NUMERIC_BOOT'
 assert a['source_freeze_sha256']==freeze_sha and a['input_sha256']==input_sha,'NUMERIC_SOURCE_OR_INPUT'
 assert a['constructor_limit']==a['solve_limit']==1,'NUMERIC_CALL_LIMIT'
 assert a['start_wall']<=wall<a['normal_stop_wall']<=a['root_stop_wall']<=a['start_wall']+180,'NUMERIC_WALL'
 assert a['start_mono']<=mono<a['normal_stop_mono']<=a['root_stop_mono']<=a['start_mono']+180,'NUMERIC_MONO'
 assert a['normal_stop_wall']<=a['start_wall']+60 and a['normal_stop_mono']<=a['start_mono']+60,'NUMERIC_NORMAL_CAP'
 return True

def fixed_input():
 inp=read(O/'INPUT.json');config=read(O/'CONFIG.json');maps=read(O/'MAPS.json')
 assert inp['maps_sha256']==sha(O/'MAPS.json')and inp['config_sha256']==sha(O/'CONFIG.json')
 assert inp['scope']=='SAVED_EXPOSED_STATIC_T0_AUTHOR_CORE_MATH_ONLY'
 assert not inp['actor_truth_or_phase_supplied']and not inp['historical_controls_supplied']
 assert maps['point_occupancy_only_not_footprint_certificate']and config['qualification_only']and config['not_benchmark_parameters']
 assert config['integers']==[15,32,1,8,2,1,1]and config['outer_constructor_limit']==config['solve_limit']==config['thread_count']==1
 assert maps['nx']==maps['ny']==100 and maps['resolution']==.1 and maps['center']==[0.,0.]
 for name in ['collision_layer','distance_field','angle_field','speed_field']:
  assert len(maps[name])==10000 and all(math.isfinite(v)for v in maps[name]),'INVALID_MAP'
 assert len(inp['state'])==5 and all(math.isfinite(v)for v in inp['state'])and inp['state'][-1]==0.
 for key in ['packet','setup']:assert sha(R/inp['source_'+key+'_path'])==inp['source_'+key+'_sha256']
 return inp,config,maps
