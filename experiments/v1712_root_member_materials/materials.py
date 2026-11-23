"""Static package selection, exact payload reader and bounded filesystem writes."""
import hashlib,io,json,os,posixpath,stat,tarfile
from pathlib import Path,PurePosixPath

BATCHES=['01_boost_headers','02_development_python','03_runtime_base','04_image_runtime']
HOST_PACKAGES=['libc6','libc6-dev','libc-dev-bin','libgcc-s1','libstdc++6','libstdc++-13-dev','pkg-config','perl','dpkg','tar','sed','debconf','tzdata']
EXTRA_ROOTS=['libglu1-mesa','libopengl0','libpocofoundation62','libboost-program-options1.71.0','libboost-python1.71.0','libssl1.1','libgpgme11','libpython3.8','libopencv-core4.2','libopencv-features2d4.2','libopencv-highgui4.2','libopencv-imgcodecs4.2','libopencv-imgproc4.2','libopencv-video4.2']
GUI_PREFIXES=('libopencv','libqt','libx11','libxau','libxcb','libxdm','libxext','libxfix','libxren','libxrand','libxrender','libxi6','libxt6','libxtst','libice','libsm6','libfont','libfreetype','libav','libsw','libgst','libgtk','libgdk','libcairo','libpango','libharfbuzz','libwebp','libjpeg','libpng','libtiff','libopenexr','libilmbase','libdc','libraw','libv4l','libgl','libdrm','libwayland','libxkbcommon','libgbm','libvisual','liborc','libtheora','libvorbis','libogg','libvpx','libx264','libx265','libaom','libshine','libsnappy','libsoxr','libspeex','libtwolame','libva','libvdpau','libshine','libmp3','libopus','libflac','libasound','libpulse','libasyncns','libsndfile','libopenjp','libjbig','libgphoto','libgudev','libudev')
def batch(name):
 if name=='libboost1.71-dev':return BATCHES[0]
 if name.endswith('-dev')or name.startswith(('python3','libpython'))or name in ['docutils-common','icu-devtools']:return BATCHES[1]
 return BATCHES[3]if name.startswith(GUI_PREFIXES)else BATCHES[2]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def ar_data(blob):
 assert blob.startswith(b'!<arch>\n');at=8;members={}
 while at<len(blob):
  head=blob[at:at+60];assert len(head)==60 and head[-2:]==b'`\n';name=head[:16].decode().strip().rstrip('/');size=int(head[48:58]);at+=60
  assert name not in members and 0<=size<=32*1024**2 and at+size<=len(blob);members[name]=blob[at:at+size];at+=size+size%2
 assert at==len(blob)and members.pop('debian-binary')==b'2.0\n'
 payload=[x for x in members if x in ['data.tar.xz','data.tar.gz','data.tar']];control=[x for x in members if x in ['control.tar.xz','control.tar.gz','control.tar']]
 assert len(payload)==len(control)==1 and len(members)==2;return members[payload[0]]
def safe_name(name):
 while name.startswith('./'):name=name[2:]
 name=name.rstrip('/')
 if name in ['', '.']:return None
 p=PurePosixPath(name);assert not p.is_absolute()and '..'not in p.parts and '\\'not in name and str(p)==name
 assert p.parts[0]in ['usr','lib','lib64','bin','sbin','etc'],'NATIVE_DATA_NAMESPACE';return name
def selected(name):
 p=PurePosixPath(name)
 return not(name.endswith('.a')or name.startswith(('usr/share/doc/','usr/share/man/','usr/share/locale/','usr/share/lintian/','usr/lib/debug/'))or name in ['usr/share/doc','usr/share/man','usr/share/locale','usr/share/lintian','usr/lib/debug'])
def safe_link(name,target):
 assert target and '\0'not in target and '\\'not in target
 normalized=posixpath.normpath(target if target.startswith('/')else '/'+posixpath.dirname(name)+'/'+target)
 assert normalized.split('/')[1]in ['usr','lib','lib64','bin','sbin','etc'],'LINK_LOGICAL_NAMESPACE'

class Meter:
 """Track only owner-created paths, reconcile after every package."""
 def __init__(self,root):
  self.root=root;self.cap=224*1024**2;self.close=8*1024**2;self.values={};self.reconcile()
 def reconcile(self):
  self.values={str(p):p.lstat().st_blocks*512 for p in [self.root,*self.root.rglob('*')]};assert self.total<self.cap;return self.total
 @property
 def total(self):return sum(self.values.values())
 def refresh(self,path):
  for p in [path,path.parent]:
   if p==self.root or self.root in p.parents:
    if p.exists()or p.is_symlink():self.values[str(p)]=p.lstat().st_blocks*512
    else:self.values.pop(str(p),None)
  assert self.total<self.cap,'NATIVE_TASK_ACTUAL_CAP'
 def permit(self,amount,closing=False):assert self.total+amount+(0 if closing else self.close)<self.cap,'NATIVE_TASK_PRECHARGE_CAP'
 def mkdir(self,path,mode=0o755):
  assert path==self.root or self.root in path.parents
  if path.exists():assert path.is_dir()and not path.is_symlink();return
  self.mkdir(path.parent);self.permit(16384);path.mkdir(mode=mode);self.refresh(path)
 def write(self,path,data,closing=False):
  assert not path.exists()and not path.is_symlink();self.mkdir(path.parent);self.permit(((len(data)+4095)//4096)*4096+16384,closing)
  with path.open('xb')as f:f.write(data)
  self.refresh(path)
 def put(self,path,value,closing=False):
  data=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';temp=path.with_suffix(path.suffix+'.tmp');self.write(temp,data,closing);temp.replace(path);self.values.pop(str(temp),None);self.refresh(path)

def extract(path,prefix,meter,package,entries,excluded):
 raw=ar_data(path.read_bytes());deferred=[];count=0;expanded=0
 def destination(name):
  p=prefix/name
  for a in p.parents:
   if a==prefix:break
   assert not a.is_symlink(),'SYMLINK_ANCESTOR_WRITE'
  return p
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')as archive:
  members=archive.getmembers();assert len(members)<=30000 and sum(v.size for v in members if v.isfile())<=192*1024**2
  for member in members:
   name=safe_name(member.name)
   if name is None:
    assert member.isdir(),'ROOT_MEMBER_NOT_DIRECTORY';continue
   if not selected(name):excluded.append(dict(package=package,path=name,type=member.type.decode(errors='replace'),bytes=member.size,reason='STATIC_ARCHIVE_OR_DOCUMENTATION_NOT_SHARED_TEB_BUILD_INPUT'));continue
   assert not(member.mode&0o7000);p=destination(name);row=dict(path=name,mode=member.mode&0o777,uid=member.uid,gid=member.gid)
   if member.isdir():row['type']='directory'
   elif member.isfile():
    stream=archive.extractfile(member);data=stream.read(member.size+1);assert len(data)==member.size;row.update(type='regular',bytes=member.size,sha256=hashlib.sha256(data).hexdigest())
   elif member.issym():safe_link(name,member.linkname);row.update(type='symlink',target=member.linkname)
   elif member.islnk():row.update(type='hardlink',target=safe_name(member.linkname));deferred.append((name,row));continue
   else:raise AssertionError(('UNSUPPORTED_SPECIAL_MEMBER',member.name))
   if name in entries:
    existing=entries[name];assert {k:v for k,v in row.items()if k not in ['uid','gid']}=={k:v for k,v in existing.items()if k not in ['uid','gid','owners']},('DIFFERENT_NATIVE_COLLISION',name)
    if package not in existing['owners']:existing['owners'].append(package)
    continue
   row['owners']=[package];entries[name]=row
   if member.isdir():meter.mkdir(p,row['mode']);p.chmod(row['mode']);meter.refresh(p)
   elif member.isfile():meter.write(p,data);p.chmod(row['mode']);meter.refresh(p);expanded+=len(data)
   elif member.issym():meter.mkdir(p.parent);meter.permit(16384);assert not p.exists()and not p.is_symlink();p.symlink_to(member.linkname);meter.refresh(p)
   count+=1
  for name,row in deferred:
   p=destination(name);q=destination(row['target']);assert q.is_file()and not q.is_symlink();row.update(type='hardlink',bytes=q.stat().st_size,sha256=sha(q),owners=[package]);assert name not in entries
   meter.mkdir(p.parent);meter.permit(16384);os.link(q,p);meter.refresh(p);entries[name]=row;count+=1
 return dict(selected_new_entries=count,selected_regular_bytes=expanded)
