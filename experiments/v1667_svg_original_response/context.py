"""Fixed author-core qualification scope; no physical or benchmark authority."""
from pathlib import Path
import hashlib,importlib.util,json,math,os,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
REVIEW_SHA='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 p=Path(p);data=(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 assert len(data)<=1024**2,'METADATA_ONE_MIB_CAP'
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(data);t.replace(p)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def usage():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def validate(a,*,wall,mono,boot,freeze_sha,input_sha):
 assert a['scope']=='PHASE_ORIGINAL_RESPONSE_STATIC_SAVED_CANDIDATE'and a['numerical_authorized']is True
 assert a['physical_authorized']is False and a['benchmark_authorized']is False
 assert a['boot_id']==boot and a['source_freeze_sha256']==freeze_sha and a['input_sha256']==input_sha
 assert a['constructor_limit']==1 and a['solve_limit']==0 and a['step_limit']==2270
 assert a['start_wall']<=wall<a['normal_stop_wall']<=a['root_stop_wall']<=a['start_wall']+300
 assert a['start_mono']<=mono<a['normal_stop_mono']<=a['root_stop_mono']<=a['start_mono']+300
 assert a['normal_stop_wall']<=a['start_wall']+180 and a['normal_stop_mono']<=a['start_mono']+180
 return True

def fixed_input():
 inp=read(O/'INPUT.json');assert inp['scope']=='SAVED_AUTHOR_CANDIDATE_ORIGINAL_STATIC_RESPONSE_ONLY'
 for row in inp['bound_inputs']:
  assert sha(R/row['path'])==row['sha256'],'BOUND_INPUT_CHANGED'
  assert sha(R/row['archive_index_path'])==row['archive_index_sha256'],'BOUND_RECOVERY_INDEX_CHANGED'
  members={m['path']:m for m in read(R/row['archive_index_path'])['files']}
  assert members[row['path']]['sha256']==row['sha256'],'INPUT_NOT_REMOTE_INDEX_MEMBER'
 old=read(R/'runs/v1661_svg_binding_namespace/INPUT.json');answer=read(R/'runs/v1661_svg_binding_namespace/numeric/RESULT.json');setup=read(R/old['source_setup_path'])
 assert answer['passed']and answer['solve_returns']==1 and answer['constructor_returns']==1
 assert inp['source_packet']==old['original_packet']and inp['raw_author_controls']==answer['controls']
 assert len(inp['raw_author_controls'])==14 and all(type(v)in (int,float)and math.isfinite(v)and abs(v)<=.42722137342572125 for v in inp['raw_author_controls'])
 assert inp['external_speed']==.08 and inp['native_per_control']==5 and inp['stop_native']==2200
 assert inp['public_goal']==old['public_goal']and inp['source_packet']['native_tick']==0 and inp['source_packet']['sim_time']==0.
 public=dict(known={k:setup['known'][k]for k in ['known_rectangles','known_circles']},limits=setup['limits'],slew_per_second=setup['slew_per_second'],dt=setup['dt'])
 assert inp['public_setup']==public and inp['physical_authorized']is False
 return inp
