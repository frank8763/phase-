"""Exact local CMake wheel intake and one non-model version probe."""
import fcntl,hashlib,json,os,signal,stat,subprocess,time,traceback,urllib.parse,urllib.request,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def put(p,x):
 data=json.dumps(x,indent=2,allow_nan=False).encode()+b'\n';assert len(data)<=4*1024**2
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(data);t.replace(p)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'ONCE_CLAIM.json').exists()and not(O/'RESULT.json').exists()and not(O/'OWNED_CHILD.json').exists()
 P=R/'runs/v1696_teb_author_build';barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 current=read(R/'CURRENT_EXPERIMENT.json');assert not current['models_now_authorized']and current['active_round']is None
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(128+32+32+512)*1024**2<15*1024**3
 wall=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 def guard(limit=5400):assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<wall+limit and time.monotonic()<mono+limit,'TOOLCHAIN_DUAL_CLOCK'
 put(O/'ONCE_CLAIM.json',dict(unix=wall,monotonic=mono,boot_id=boot,owner_pid=os.getpid(),owner_sha256=sha(C/'owner.py'),protocol_sha256=sha(C/'PROTOCOL.md'),allruns_bytes=used,models_authorized=False))
 result=dict(passed=False,closed=False,models=0,optimizer_calls=0,optimizer_constructors=0,physical_native=0,replay_native=0,system_install=False,method_outcome=None,first_error=None)
 child=None;identity=None
 try:
  request=urllib.request.Request('https://pypi.org/pypi/cmake/3.31.6/json',headers={'User-Agent':'Phase-exact-build-tool/1'})
  with urllib.request.urlopen(request,timeout=20)as stream:raw=stream.read(1024**2+1)
  assert len(raw)<=1024**2;metadata=json.loads(raw);assert metadata['info']['version']=='3.31.6';(O/'PYPI_METADATA.json').write_bytes(raw)
  filename='cmake-3.31.6-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl';rows=[x for x in metadata['urls']if x['filename']==filename];assert len(rows)==1;row=rows[0]
  assert row['size']<=32*1024**2 and row['packagetype']=='bdist_wheel'and urllib.parse.urlparse(row['url']).scheme=='https'and urllib.parse.urlparse(row['url']).hostname=='files.pythonhosted.org'
  pin=dict(version='3.31.6',filename=filename,url=row['url'],bytes=row['size'],sha256=row['digests']['sha256'],metadata_sha256=sha(O/'PYPI_METADATA.json'));put(O/'DOWNLOAD_PIN.json',pin)
  target=O/filename;total=0
  with urllib.request.urlopen(row['url'],timeout=20)as stream,target.open('xb')as f:
   assert urllib.parse.urlparse(stream.geturl()).hostname=='files.pythonhosted.org'
   while True:
    guard(600);block=stream.read(65536)
    if not block:break
    total+=len(block);assert total<=row['size']<=32*1024**2;f.write(block)
  assert total==row['size']and sha(target)==pin['sha256'],'WHEEL_SIZE_SHA'
  prefix=O/'prefix';prefix.mkdir();members=[];unpacked=0
  with zipfile.ZipFile(target)as archive:
   for item in archive.infolist():
    guard(600);name=item.filename;path=Path(name);assert not path.is_absolute()and '..'not in path.parts and '\\'not in name
    mode=item.external_attr>>16;assert not stat.S_ISLNK(mode),'WHEEL_SYMLINK_REFUSED'
    if item.is_dir():continue
    unpacked+=item.file_size;assert unpacked<=128*1024**2
    output=prefix/path;output.parent.mkdir(parents=True,exist_ok=True)
    with archive.open(item)as src,output.open('xb')as dest:
     for block in iter(lambda:src.read(65536),b''):dest.write(block)
    output.chmod(0o755 if mode&0o111 else 0o644);assert output.stat().st_size==item.file_size
    members.append(dict(path=str(output.relative_to(R)),bytes=item.file_size,sha256=sha(output),wheel_crc=item.CRC))
  binary=prefix/'cmake/data/bin/cmake';assert binary.is_file()and os.access(binary,os.X_OK)
  put(O/'UNPACK_MANIFEST.json',dict(wheel_path=str(target.relative_to(R)),wheel_sha256=pin['sha256'],files=members,unpacked_bytes=unpacked,binary=str(binary.relative_to(R)),models=0))
  env=os.environ.copy()
  for name in ['LD_LIBRARY_PATH','PYTHONPATH','CMAKE_PREFIX_PATH','ROS_PACKAGE_PATH','AMENT_PREFIX_PATH','COLCON_PREFIX_PATH']:env.pop(name,None)
  env.update(PATH='/usr/bin:/bin',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
  command=['taskset','-c','4','nice','-n','19','ionice','-c','3',str(binary),'--version'];put(O/'VERSION_COMMAND.json',dict(argv=command,owner_sha256=sha(C/'owner.py'),binary_sha256=sha(binary),cpu=4,maximum_s=10))
  child=subprocess.Popen(command,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19];identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=ticks,boot_id=boot,nonmodel_version_probe=True);put(O/'OWNED_CHILD.json',identity)
  text,_=child.communicate(timeout=10);assert len(text)<=65536;(O/'version.console').write_bytes(text);guard()
  assert child.returncode==0 and text.decode().splitlines()[0]=='cmake version 3.31.6','FIXED_TOOL_VERSION_MISMATCH'
  assert all(sha(R/x['path'])==x['sha256']for x in members)
  result.update(passed=True,version='3.31.6',binary_path=str(binary.relative_to(R)),binary_sha256=sha(binary),wheel_path=str(target.relative_to(R)),wheel_bytes=total,wheel_sha256=pin['sha256'],unpack_members=len(members),unpacked_bytes=unpacked,all_member_SHA_verified=True,version_probe_returncode=child.returncode,tool_only_not_TEB_configure=True)
 except BaseException as e:result['first_error']=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19];assert ticks==identity['start_ticks']and os.getpgid(child.pid)==identity['pgid'];os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=3)
  result.update(closed=True,wall_s=time.monotonic()-mono,version_child_exited=child is None or child.poll()is not None,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66')
  put(O/'RESULT.json',result)
 print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
