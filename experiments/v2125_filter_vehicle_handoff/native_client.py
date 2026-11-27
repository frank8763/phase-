"""Sole evidence writer, charged input file, readonly CPU6 optimizer peer."""
import hashlib,json,os,selectors,subprocess,time
from context import R,C,O,read,load,put,remaining

def solve(frame,save):
 out=__import__('pathlib').Path(read(O/'PILOT_TASK.json')['output']);w=read(O/'PILOT_WINDOW.json');now=time.time();mono=time.monotonic();request=frame['request'];current=frame['current']
 authority=dict(scope='FILTER_OPTIMIZER_ONLY',models_authorized=False,input_sha256=current['input_sha256'],request_sha256=request['request_sha256'],method=current['method'],absolute_deadline_unix=min(now+600,w['normal_end_unix']),hard_stop_monotonic=min(mono+600,w['hard_stop_monotonic']-1200))
 save('FILTER_OPTIMIZER_ADMISSION.json',authority)
 ns=load('FILTER_readonly_cpu6_namespace',C/'native_namespace.py');env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',JAX_PLATFORMS='cpu',JAX_ENABLE_X64='true',XLA_FLAGS='--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1 --xla_force_host_platform_device_count=1',MPLCONFIGDIR='/tmp/phase_priest_matplotlib')
 cmd=['taskset','-c','6','nice','-n','19','ionice','-c','3',*ns.command(C/'native_worker.py',out)]
 launch=load('FILTER_charged_regular_stdin',C/'input_frame.py');p,stream=launch.launch(cmd,frame,input_path=out/'FILTER_CURRENT_INPUT_WIRE.json',cwd=R,env=env);identity=dict(pid=p.pid,start_ticks=__import__('pathlib').Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],CPU=6,all_repo_runs_readonly=True);save('FILTER_NATIVE_PEER_IDENTITY.json',identity)
 sel=selectors.DefaultSelector();buffers={};reply=None;error=None;closed=None;log=bytearray();start=time.monotonic()
 for pipe in [p.stdout,p.stderr]:sel.register(pipe,selectors.EVENT_READ);buffers[pipe.fileno()]=bytearray()
 try:
  while sel.get_map():
   assert time.monotonic()-start<620 and remaining(w)>1200,'FILTER_REPLY_TIME_CAP'
   for key,_ in sel.select(.1):
    data=os.read(key.fileobj.fileno(),16384);buf=buffers[key.fileobj.fileno()]
    if not data:
     if buf:log.extend(buf);buf.clear()
     sel.unregister(key.fileobj);continue
    buf.extend(data);assert len(buf)<=1024**2
    while b'\n'in buf:
     line,_,rest=buf.partition(b'\n');buf[:]=rest;log.extend(line+b'\n');assert len(log)<=1024**2,'FILTER_NATIVE_CONSOLE_CAP'
     if line.startswith(b'FILTER_REPLY '):assert reply is None;reply=json.loads(line[13:])
     if line.startswith(b'FILTER_ERROR '):error=json.loads(line[13:])
     if line.startswith(b'FILTER_CLOSED '):closed=json.loads(line[14:])
  p.wait(timeout=5);save('FILTER_NATIVE_CONSOLE.json',dict(bytes=len(log),sha256=hashlib.sha256(log).hexdigest(),text=log.decode(errors='strict'),returncode=p.returncode));save('FILTER_NATIVE_CLOSED.json',dict(accounting=closed,error=error,returncode=p.returncode))
  assert p.returncode==0 and error is None and reply is not None and reply['passed'],'FILTER_NATIVE_SOLVE_REFUSED'
  raw=json.dumps(frame,allow_nan=False).encode()+b'\n';assert reply['input_bytes']==len(raw)and reply['input_byte_sha256']==hashlib.sha256(raw).hexdigest()
  save('FILTER_NATIVE_RESULT.json',reply);assert reply['answer'].get('proposal')is not None,'FILTER_CURRENT_NUMERICAL_OR_HARD_GEOMETRY_REFUSED';return reply['answer']
 finally:
  if p.poll()is None:p.terminate();p.wait(timeout=5)
  stream.close();sel.close()
