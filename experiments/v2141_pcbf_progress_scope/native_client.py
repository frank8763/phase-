"""One persistent readonly CPU6 SciPy peer; CPU2 retains sole evidence writes."""
import hashlib,json,os,selectors,subprocess,time
from pathlib import Path
from context import R,C,O,read,load,remaining
class Client:
 def __init__(self,save,frame):
  self.save=save;self.closed=False;self.calls=0;self.failed=False;self.log=bytearray();self.messages=[];self.buffers={};self.pending=None;self.p=None
  self.out=Path(read(O/'PILOT_TASK.json')['output']);self.w=read(O/'PILOT_WINDOW.json');now=time.time();mono=time.monotonic()
  save('FILTER_OPTIMIZER_ADMISSION.json',dict(scope='FILTER_OPTIMIZER_ONLY',models_authorized=False,method=frame['current']['method'],run_id=frame['current']['run_id'],maximum_queries=250,first_input_sha256=frame['current']['input_sha256'],absolute_deadline_unix=min(now+3600,self.w['normal_end_unix']),hard_stop_monotonic=min(mono+3600,self.w['hard_stop_monotonic']-1200)))
  channel=load('FILTER_owned_bounded_stream',C/'channel.py');self.channel=channel.FrameChannel(maximum_frames=250)
  ns=load('FILTER_readonly_cpu6_namespace',C/'native_namespace.py');env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
  cmd=['taskset','-c','6','nice','-n','19','ionice','-c','3',*ns.command(C/'native_worker.py',self.out)]
  try:
   self.p=subprocess.Popen(cmd,cwd=R,env=env,stdin=self.channel.child.fileno(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.channel.detach_child_endpoint();self.sel=selectors.DefaultSelector()
   for stream in[self.p.stdout,self.p.stderr]:self.sel.register(stream,selectors.EVENT_READ);self.buffers[stream.fileno()]=bytearray()
   self.identity=dict(pid=self.p.pid,start_ticks=Path('/proc',str(self.p.pid),'stat').read_text().split(') ',1)[1].split()[19],CPU=6,all_repo_runs_readonly=True);save('FILTER_NATIVE_PEER_IDENTITY.json',self.identity);self.send(frame)
  except BaseException:
   self.channel.close()
   if self.p is not None and self.p.poll()is None:self.p.terminate();self.p.wait(timeout=5)
   raise
 def send(self,frame):
  assert self.pending is None
  self.pending=self.channel.send(frame)
  raw=json.dumps(frame,allow_nan=False).encode()+b'\n'
  self.save(f'FILTER_QUERY_{self.calls:03d}_WIRE.json',dict(text=raw.decode(),**self.pending))
 def wait(self,prefix,seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   for i,(kind,msg)in enumerate(self.messages):
    if kind==prefix:self.messages.pop(i);return msg
    if kind=='FILTER_ERROR ':self.messages.pop(i);raise AssertionError('FILTER_NATIVE_PEER_ERROR:'+json.dumps(msg))
   assert self.sel.get_map(),'FILTER_NATIVE_EOF_BEFORE_REPLY'
   assert remaining(self.w)>1200,'FILTER_NORMAL_WINDOW_EXHAUSTED'
   for key,_ in self.sel.select(.1):
    data=os.read(key.fileobj.fileno(),16384)
    if not data:self.sel.unregister(key.fileobj);continue
    self.log.extend(data);assert len(self.log)<=4*1024**2,'FILTER_NATIVE_CONSOLE_CAP';buf=self.buffers[key.fileobj.fileno()];buf.extend(data)
    while b'\n'in buf:
     line,_,rest=buf.partition(b'\n');buf[:]=rest
     for label in['FILTER_REPLY ','FILTER_ERROR ','FILTER_CLOSED ']:
      if line.startswith(label.encode()):self.messages.append((label,json.loads(line[len(label):])))
  raise TimeoutError('FILTER_NATIVE_REPLY_TIME_LIMIT')
 def query(self,frame=None):
  assert not self.closed and not self.failed and self.calls<250,'FILTER_CLIENT_CLOSED_POISONED_OR_COUNT'
  self.failed=True
  if self.calls:assert frame is not None;self.send(frame)
  else:assert frame is None and self.pending is not None
  reply=self.wait('FILTER_REPLY ',600);assert reply['transport_ack']==self.pending and reply['passed'],'FILTER_CURRENT_TRANSPORT_ACK'
  self.channel.acknowledge(reply['transport_ack']);self.pending=None;self.save(f'FILTER_QUERY_{self.calls:03d}_RESULT.json',reply);self.calls+=1;self.failed=False;return reply['answer']
 def close(self):
  if self.closed:return
  self.closed=True
  try:
   if self.channel.pending is None and not self.channel.poisoned:self.channel.finish_input()
   else:self.channel.close()
   answer=self.wait('FILTER_CLOSED ',30);self.save('FILTER_NATIVE_CLOSED.json',answer);self.p.wait(timeout=5)
   assert self.p.returncode==0 and answer['optimizer_calls']==self.calls and answer['all_source_SHA_after'],'FILTER_PEER_CLOSE_ACCOUNTING'
  finally:
   if self.p.poll()is None:self.p.terminate();self.p.wait(timeout=5)
   self.channel.close();self.sel.close();raw=bytes(self.log);self.save('FILTER_NATIVE_CONSOLE.json',dict(text=raw.decode(errors='strict'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),returncode=self.p.returncode,queries=self.calls,identity=self.identity))
