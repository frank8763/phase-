"""One CPU2-owned readonly CPU6 query; retain raw returns before any decision."""
from context import R,C,SOURCE,O,read,load,sha,digest,remaining
from pathlib import Path
import copy,hashlib,json,os,secrets,selectors,signal,subprocess,time,traceback
from handshake import bind,verify

def authority(task):
 assert os.sched_getaffinity(0)=={2}
 from context import admission
 a,w,files=admission(task);out=Path(task['output']);assert out==O/'actual'and task['maximum_current_native_queries']==1 and task['maximum_control_native']==120
 assert not(out/'PROJECTION_PEER_ONCE.json').exists()and not(out/'PROJECTION_OPTIMIZER_ADMISSION.json').exists(),'NO_SECOND_QUERY_OR_PEER'
 return w,sha(SOURCE/'SOURCE_FREEZE.json')
def worker_command():
 from peer_namespace import command
 return ['taskset','-c','6','nice','-n','19','ionice','-c','3',*command(C/'peer_entry.py')]

class Client:
 def __init__(self,save,receipt,task):
  self.w,self.source_sha=authority(task);self.save=save;self.task=task;self.out=Path(task['output']);self.closed=False;self.p=None;self.identity=None;self.channel=None;self.sel=None;self.replied=None;self.closed_reply=None;self.progress=None;self.raw_return=None;self.total_bytes=0;self.chunks=0;self.digest=hashlib.sha256();self.complete=False
  now=time.time();mono=time.monotonic();nonce=secrets.token_hex(24)
  auth=dict(scope='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY',models_authorized=False,maximum_queries=1,run_id=task['run_id'],query_nonce=nonce,source_freeze_sha256=self.source_sha,worker_sha256=sha(C/'peer_entry.py'),absolute_deadline_unix=min(now+150,self.w['normal_end_unix']),hard_stop_monotonic=min(mono+150,self.w['hard_stop_monotonic']-1200),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
  save('PROJECTION_OPTIMIZER_ADMISSION.json',auth)
  public=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'
  frame=dict(schema='FRESH_REST_ORIENTATION_PROJECTION_V1',episode_id=task['run_id'],query_sequence=0,query_nonce=nonce,source_freeze_sha256=self.source_sha,numerical_admission_sha256='',receipt=copy.deepcopy(receipt),public_known=read(public),public_known_sha256=sha(public),whole_goal_xy=task['goal_xy'])
  self.frame,self.claim=bind((self.out/'PROJECTION_OPTIMIZER_ADMISSION.json').read_bytes(),frame);verify((self.out/'PROJECTION_OPTIMIZER_ADMISSION.json').read_bytes(),self.claim,self.frame)
  save('PROJECTION_QUERY_FRAME.json',self.frame);save('PROJECTION_PEER_ONCE.json',self.claim)
  channel=load('CP_original_owned_one_frame',C/'channel.py');self.channel=channel.FrameChannel(maximum_frames=1);env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
  try:
   self.p=subprocess.Popen(worker_command(),cwd=R,env=env,stdin=self.channel.child.fileno(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
   self.identity=dict(pid=self.p.pid,pgid=os.getpgid(self.p.pid),start_ticks=Path('/proc',str(self.p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=auth['boot_id'],CPU=6,readonly_math_peer=True);save('PROJECTION_NATIVE_PEER_IDENTITY.json',self.identity);self.channel.detach_child_endpoint();self.expected_ack=self.channel.send(self.frame);self.sel=selectors.DefaultSelector();self.buffers={}
   for stream in [self.p.stdout,self.p.stderr]:self.sel.register(stream,selectors.EVENT_READ);self.buffers[stream.fileno()]=bytearray()
  except BaseException:self.close();raise
 def query(self):
  assert not self.closed and self.replied is None and not self.complete,'ONE_QUERY_ONLY';end=time.monotonic()+130
  try:
   while self.sel.get_map():
    assert time.monotonic()<end and remaining(self.w)>1200,'PROJECTION_CURRENT_PEER_FINITE_TIME'
    for key,_ in self.sel.select(.1):
     data=os.read(key.fileobj.fileno(),16384)
     if not data:self.sel.unregister(key.fileobj);continue
     self.total_bytes+=len(data);assert self.total_bytes<=128*1024,'PROJECTION_CONSOLE_128KiB_CAP';self.digest.update(data)
     self.save(f'PROJECTION_CONSOLE_CHUNK_{self.chunks:04d}.json',dict(stream='stdout'if key.fileobj is self.p.stdout else'stderr',hex=data.hex()));self.chunks+=1
     buf=self.buffers[key.fileobj.fileno()];buf.extend(data)
     while b'\n'in buf:
      line,_,rest=buf.partition(b'\n');buf[:]=rest
      if key.fileobj is not self.p.stdout:continue
      label,_,payload=line.partition(b' ');value=json.loads(payload)
      if label==b'PROJECTION_PROGRESS':assert self.progress is None;self.progress=value;self.save('PROJECTION_NATIVE_PROGRESS.json',value)
      elif label==b'PROJECTION_RAW_RETURN':assert self.raw_return is None;self.raw_return=value;self.save('PROJECTION_NATIVE_RAW_RETURN.json',value)
      elif label==b'PROJECTION_REPLY':
       assert self.replied is None;self.replied=value;self.save('PROJECTION_NATIVE_REPLY.json',value) # even a failed query is durable first
       assert value['transport_ack']==self.expected_ack and value['query_nonce']==self.frame['query_nonce']and value['query_sha256']==digest(self.frame),'PROJECTION_REPLY_CURRENT_BINDING'
       self.channel.acknowledge(value['transport_ack']);self.channel.finish_input()
      elif label==b'PROJECTION_CLOSED':assert self.closed_reply is None;self.closed_reply=value;self.save('PROJECTION_NATIVE_CLOSED.json',value)
      elif label==b'PROJECTION_ERROR':self.save('PROJECTION_NATIVE_ERROR.json',value);raise AssertionError('PROJECTION_NATIVE_EARLY_ERROR:'+str(value['error']))
      else:raise AssertionError('UNREGISTERED_PROJECTION_STDOUT_RECORD')
   self.p.wait(timeout=5);r=self.replied;c=self.closed_reply;assert r is not None and c is not None and self.progress is not None,'INCOMPLETE_CURRENT_QUERY_REPLY_OR_CLOSURE'
   assert r['NLP_attempted_calls']==c['NLP_attempted_calls']==1 and r['NLP_returns']==c['NLP_returns']and r['inflight_unknown']==c['inflight_unknown']and c['query_nonce']==self.frame['query_nonce']and r['all_source_SHA_after']and c['all_source_SHA_after'],'PROJECTION_NATIVE_CLOSED_ACCOUNTING'
   self.complete=True
   assert self.p.returncode==0 and r['passed']and c['math_passed']and r['NLP_returns']==1 and not r['inflight_unknown'],'PROJECTION_FRESH_OPTIMIZER_REFUSED'
   p=r['proposal'];assert p['query']['receipt_sha256']==digest(self.frame['receipt'])and p['query']['query_nonce']==self.frame['query_nonce']and p['query']['episode_id']==self.task['run_id'],'PROFILE_ORIGIN_NOT_THIS_FRESH_QUERY'
   return copy.deepcopy(p)
  finally:self.close()
 def close(self):
  if self.closed:return
  self.closed=True
  if self.p is not None and self.p.poll()is None:
   assert self.identity is not None and Path('/proc',str(self.p.pid),'stat').read_text().split(') ',1)[1].split()[19]==self.identity['start_ticks']
   os.killpg(self.identity['pgid'],signal.SIGTERM)
   try:self.p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(self.identity['pgid'],signal.SIGKILL);self.p.wait(timeout=5)
  if self.channel is not None:self.channel.close()
  if self.sel is not None:self.sel.close()
  r=self.replied or self.progress or{};self.save('PROJECTION_NATIVE_ACCOUNTING.json',dict(closed=True,complete_reply_and_peer_close=self.complete,NLP_attempted_calls=r.get('NLP_attempted_calls'),NLP_returns=r.get('NLP_returns'),inflight_unknown=r.get('inflight_unknown'),internal_optimizer_work=None,compiled_SLSQP_FFI_calls=None,returncode=None if self.p is None else self.p.returncode,console_bytes=self.total_bytes,console_chunks=self.chunks,console_sha256=self.digest.hexdigest(),identity=self.identity,own_model_constructions=0))
