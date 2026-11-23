"""Read original CMake link files as data, never load a dependency."""
import hashlib,json,os,posixpath,shlex
from pathlib import Path
def inventory(repository,build_root):
 R=Path(repository);P=Path(build_root);inputs=json.loads((P/'INPUT_BINDING.json').read_text());native={}
 for name in inputs['native_manifests']:
  for row in json.loads((R/name).read_text())['entries'].values():
   name='/'+row['path'];name='/usr'+name if name.startswith('/lib/')else name;native[name]=row
 ros=R/inputs['ros_root']
 def exists(path,seen=()):
  path=posixpath.normpath(path);path='/usr'+path if path.startswith('/lib/')else path
  if path in seen or len(seen)>32:return False
  row=native.get(path)
  if row:
   if row['type']=='symlink':return exists(row['target']if row['target'].startswith('/')else posixpath.join(posixpath.dirname(path),row['target']),seen+(path,))
   return row['type']in ['regular','hardlink']
  if path.startswith('/opt/ros/noetic/'):return(ros/path[len('/opt/ros/noetic/'):]).is_file()
  p=Path(path)
  if p.is_symlink():
   target=os.readlink(p);return exists(target if target.startswith('/')else posixpath.join(posixpath.dirname(path),target),seen+(path,))
  return p.is_file()
 link=P/'build/CMakeFiles/teb_local_planner.dir/link.txt';make=P/'build/CMakeFiles/teb_local_planner.dir/build.make';argv=shlex.split(link.read_text());assert all('$('not in x and '`'not in x for x in argv)
 explicit=[x for x in argv if x.startswith(('/usr/lib/','/opt/ros/noetic/lib/'))and'.so'in x];search=[x[2:]for x in argv if x.startswith('-l')];paths=['/usr/lib/x86_64-linux-gnu','/lib/x86_64-linux-gnu','/usr/lib','/opt/ros/noetic/lib']+[x[2:]for x in argv if x.startswith('-L')]
 resolutions={name:next((p+'/'+prefix+name+suffix for p in paths for prefix,suffix in [('lib','.so'),('lib','.a')]if exists(p+'/'+prefix+name+suffix)),None)for name in search}
 dependencies=[line.split(': ',1)[1]for line in make.read_text().splitlines()if line.startswith('devel/lib/libteb_local_planner.so: /usr/lib/')]
 return dict(scope='STATIC_ORIGINAL_LINK_FILE_EXISTENCE_ONLY',link_file_sha256=hashlib.sha256(link.read_bytes()).hexdigest(),makefile_sha256=hashlib.sha256(make.read_bytes()).hexdigest(),explicit_library_files=explicit,missing_explicit_files=[x for x in explicit+dependencies if not exists(x)],search_l_resolutions=resolutions,missing_search_l_names=[n for n,p in resolutions.items()if p is None],transitive_dependencies_or_ABI_verified=False,library_loaded=False,models=0)
