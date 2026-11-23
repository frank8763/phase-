"""Static transitive candidate paths for the new library, no ldd or dlopen."""
import hashlib,importlib.util,json,os,posixpath
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1728_teb_final_link_build'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(O/'TRANSITIVE_LIBRARY_CANDIDATE.json').exists();result=read(O/'RESULT.json');assert result['passed']and result['compiler_exited']and result['source_SHA_unchanged']
 helper=R/'experiments/v1708_focal_dependency_resolution/elf.py';assert sha(helper)=='dfb7c14cae45ab34e86a10891762d879cd98aa8dd55f5cd894b7767c6a5a3bd7';s=importlib.util.spec_from_file_location('existing_exact_ELF_data_reader',helper);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 inputs=read(O/'INPUT_BINDING.json');native={}
 for name in inputs['native_manifests']:
  manifest=read(R/name)
  for row in manifest['entries'].values():
   logical='/'+row['path'];logical='/usr'+logical if logical.startswith('/lib/')else logical;native[logical]=(R/manifest['prefix']/row['path'],row)
 ros=R/inputs['ros_root'];old=read(R/'runs/v1708_focal_dependency_resolution/ELF_DEPENDENCIES.json');cached={str(R/x['path']):x for x in old['files']}
 def locate(path,seen=()):
  path=posixpath.normpath(path);path='/usr'+path if path.startswith('/lib/')else path
  assert path.startswith(('/usr/lib/','/lib64/','/etc/alternatives/','/opt/ros/noetic/lib/')),'OUTSIDE_APPROVED_LIBRARY_NAMESPACE'
  if path in seen or len(seen)>32:return None
  if path in native:
   p,row=native[path]
   if row['type']=='symlink':return locate(row['target']if row['target'].startswith('/')else posixpath.join(posixpath.dirname(path),row['target']),seen+(path,))
   if row['type']in ['regular','hardlink']:assert sha(p)==row['sha256'];return p,'EXACT_RECOVERED_NATIVE'
   return None
  if path.startswith('/opt/ros/noetic/lib/'):
   p=ros/path[len('/opt/ros/noetic/'):]
   if p.is_symlink():
    target=p.resolve();assert target.is_relative_to(ros);return(target,'EXACT_RECOVERED_ROS')if target.is_file()else None
   return(p,'EXACT_RECOVERED_ROS')if p.is_file()else None
  p=Path(path)
  if p.is_symlink():
   target=os.readlink(p);return locate(target if target.startswith('/')else posixpath.join(posixpath.dirname(path),target),seen+(path,))
  return(p,'EXPLICIT_HOST_FALLBACK_CANDIDATE')if p.is_file()else None
 def resolve(name):
  assert '/'not in name
  for folder in ['/opt/ros/noetic/lib','/usr/lib/x86_64-linux-gnu','/usr/lib','/lib64']:
   answer=locate(folder+'/'+name)
   if answer:return answer
  return None
 root=R/result['library_path'];assert sha(root)==result['library_sha256'];pending=[(root,'NEW_ORIGINAL_AUTHOR_BUILD')];nodes={};missing=set();edges=[];cached_reused=0
 while pending:
  p,origin=pending.pop();key=str(p)
  if key in nodes:continue
  digest=sha(p)
  if key in cached:
   row=dict(cached[key]);assert row['sha256']==digest;cached_reused+=1
  else:row=m.dynamic_metadata(p)
  row.update(path=str(p.relative_to(R))if p.is_relative_to(R)else str(p),origin=origin);nodes[key]=row
  for name in row['needed']:
   answer=resolve(name);edges.append(dict(parent=row['path'],needed=name,resolved_path=(str(answer[0].relative_to(R))if answer[0].is_relative_to(R)else str(answer[0]))if answer else None))
   if answer:pending.append(answer)
   else:missing.add(name)
 proof=dict(scope='STATIC_TRANSITIVE_EXISTENCE_AND_EXACT_BYTES_CANDIDATE_ONLY',all_needed_files_located=not missing,missing_SONAMEs=sorted(missing),nodes=list(nodes.values()),edges=edges,old_ROS_metadata_exact_SHA_reused=cached_reused,root_library_sha256=result['library_sha256'],host_fallback_explicit=True,symbol_versions_or_ABI_or_load_tested=False,empty_runpath_components_require_controlled_future_cwd=True,optimizer_calls=0,library_loaded=False,models=0,helper_late_to_source_Git=True)
 (O/'TRANSITIVE_LIBRARY_CANDIDATE.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(dict(all_needed_files_located=not missing,nodes=len(nodes),missing_SONAMEs=sorted(missing),cached_ROS_reused=cached_reused,models=0)))
if __name__=='__main__':main()
