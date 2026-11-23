"""Transparent readonly original-file view; never execute restored code here."""
import hashlib,json,os
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def union(destination,host,natives,records,logical):
 """Merge shared directories; preserve exact package links, proxy other leaves."""
 live=[p for p in natives if p.exists()or p.is_symlink()]
 if not live:
  assert host.exists()or host.is_symlink();destination.symlink_to('/tmp/phase-host/'+str(host).lstrip('/'));records.append(dict(path=logical,kind='HOST_READONLY_PROXY',source=str(host)));return
 first=live[0]
 if first.is_symlink():
  target=os.readlink(first);assert all(p.is_symlink()and os.readlink(p)==target for p in live),'NATIVE_LINK_COLLISION'
  destination.symlink_to(target);records.append(dict(path=logical,kind='EXACT_NATIVE_SYMLINK',target=target,sources=[str(p.relative_to(R))for p in live]));return
 assert all(not p.is_symlink()for p in live),'NATIVE_TYPE_COLLISION'
 if first.is_file():
  digest=sha(first);assert all(p.is_file()and sha(p)==digest for p in live),'NATIVE_FILE_COLLISION'
  destination.symlink_to(first);records.append(dict(path=logical,kind='NATIVE_READONLY_PROXY',source=str(first.relative_to(R)),sha256=digest));return
 assert all(p.is_dir()for p in live),'NATIVE_DIRECTORY_COLLISION'
 # A single native subtree without host fallback can remain a whole exact tree.
 if len(live)==1 and not(host.exists()or host.is_symlink()):
  destination.symlink_to(first);records.append(dict(path=logical,kind='NATIVE_SUBTREE_PROXY',source=str(first.relative_to(R))));return
 assert not host.is_symlink(),'HOST_DIRECTORY_LINK_REQUIRES_EXPLICIT_MAPPING'
 destination.mkdir();names=set()
 if host.is_dir():names.update(p.name for p in host.iterdir())
 for p in live:names.update(q.name for q in p.iterdir())
 for name in sorted(names):union(destination/name,host/name,[p/name for p in live],records,logical+'/'+name)
def prepare_view(output,roots):
 view=output/'view';view.mkdir();usr=view/'usr';usr.mkdir();records=[]
 for name in ['include','lib','share','bin']:
  sources=[p/'usr'/name for p in roots]
  if name=='lib':sources.extend(p/'lib'for p in roots)
  union(usr/name,Path('/usr')/name,sources,records,'/usr/'+name)
 union(view/'etc',Path('/etc'),[p/'etc'for p in roots],records,'/etc')
 return view,records
def command(output,view,ros,argv):
 args=['/usr/bin/bwrap','--die-with-parent','--new-session','--unshare-all','--ro-bind','/','/','--tmpfs','/home','--tmpfs','/tmp','--tmpfs','/opt','--proc','/proc','--dev','/dev','--ro-bind','/usr','/tmp/phase-host/usr','--ro-bind','/etc','/tmp/phase-host/etc','--ro-bind',str(R),str(R),'--ro-bind',str(ros),'/opt/ros/noetic','--ro-bind',str(view/'etc'),'/etc']
 for name in ['include','lib','share','bin']:args+=['--ro-bind',str(view/'usr'/name),'/usr/'+name]
 for name in ['build','tmp']:args+=['--bind',str(output/name),str(output/name)]
 args+=['--chdir',str(output/'build'),'--setenv','HOME','/tmp','--setenv','TMPDIR',str(output/'tmp'),'--setenv','PATH','/usr/bin:/bin','--setenv','CMAKE_PREFIX_PATH','/opt/ros/noetic','--setenv','PYTHONPATH','/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages','--setenv','LD_LIBRARY_PATH','/opt/ros/noetic/lib:/usr/lib/x86_64-linux-gnu','--setenv','ROS_PYTHON_VERSION','3','--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','CUDA_VISIBLE_DEVICES','','--setenv','OMP_NUM_THREADS','1','--setenv','OPENBLAS_NUM_THREADS','1','--setenv','MKL_NUM_THREADS','1']
 return args+['--remount-ro','/tmp','--remount-ro','/opt','--remount-ro','/home']+argv
