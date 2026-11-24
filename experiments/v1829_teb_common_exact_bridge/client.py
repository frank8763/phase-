"""One read-only persistent native worker. All mailbox/console writes metered."""
import json,os,selectors,signal,subprocess,time
from pathlib import Path
from context import C,O,R,read,sha,load,digest,remaining

class Client:
 def __init__(self,source,out,save,quota):
  assert quota.write_enforcement_active
  self.source=source;self.out=out;self.save=save;self.process=None;self.identity=None;self.sequence=0;self.poisoned=False;self.closed=False;self.console=bytearray();self.pending=bytearray();self.records=[];self.selector=None
  a=read(O/'PILOT_ADMISSION.json');assert a['models_authorized']and a['scope']=='TEB_COMMON_CONDITION_FULL_TASK'
  assert os.sched_getaffinity(0)=={2}and not(R/'REVIEW_PENDING').exists()
  self.freeze=sha(O/'SOURCE_FREEZE.json');assert a['source_freeze_sha256']==self.freeze
  contract=load('v1824_persistent_mailbox_contract',C/'session_contract.py');self.contract=contract.Session(self.freeze,read(O/'TEB_CONFIG.json'))
  self.native=out/'teb_native'
  for n in ['build','tmp','build/empty_cwd','build/home','requests']:(self.native/n).mkdir(parents=True,exist_ok=False)
 def start(self):
  assert self.process is None and not self.closed
  for p in C.iterdir():
   if p.is_file():assert sha(p)==self.source[str(p.relative_to(R))]
  namespace=load('v1824_readonly_native_namespace',C/'native_namespace.py')
  argv=namespace.command([namespace.PYTHON,'-I','-B','-S',str(C/'native_worker.py'),'--serve-current'],self.native)
  assert '--bind'not in argv
  self.process=subprocess.Popen(argv,cwd=R,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  stat=Path('/proc',str(self.process.pid),'stat').read_text().split(') ',1)[1].split()
  self.identity=dict(pid=self.process.pid,pgid=os.getpgid(self.process.pid),start_ticks=stat[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
  self.save('TEB_NATIVE_OWNED_CHILD.json',self.identity)
  self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)
 def drain(self,delay=.1):
  for key,_ in self.selector.select(delay):
   block=os.read(key.fileobj.fileno(),16384)
   if not block:self.selector.unregister(key.fileobj);continue
   assert len(self.console)+len(block)<=4*1024**2,'TEB_NATIVE_CONSOLE_CAP'
   self.console.extend(block);self.pending.extend(block)
   while b'\n'in self.pending:
    line,_,tail=self.pending.partition(b'\n');self.pending=bytearray(tail)
    if line.startswith(b'PHASE_TEB_'):
     tag,data=line.split(b' ',1);self.records.append((tag.decode(),json.loads(data)))
 def query(self,wire,cycle):
  assert not self.closed and not self.poisoned,'TEB_SESSION_POISONED_NO_RETRY'
  envelope=dict(sequence=self.sequence+1,wire=wire,wire_sha256=digest(wire),source_freeze_sha256=self.freeze)
  self.contract.accept(envelope);self.sequence+=1
  raw=json.dumps(envelope,separators=(',',':'),allow_nan=False).encode();assert len(raw)<=1024**2
  try:
   self.save(f'cycle_{cycle:04d}_teb_envelope.json',envelope)
   self.save(f'teb_native/requests/{self.sequence:06d}.json',envelope)
   if self.process is None:self.start()
   start=time.monotonic();wall=time.time();before=len(self.console)
   while True:
    assert time.monotonic()<start+60 and time.time()<wall+60 and remaining(read(O/'PILOT_WINDOW.json'))>1200,'TEB_CURRENT_QUERY_DUAL_CLOCK_STOP'
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==self.identity['boot_id']
    self.drain()
    assert len(self.console)-before<=256*1024,'TEB_CURRENT_QUERY_PIPE_CAP'
    answers=[v for tag,v in self.records if tag=='PHASE_TEB_ANSWER'and v['sequence']==self.sequence]
    if answers:
     assert len(answers)==1;answer=answers[0]
     assert answer['wire_sha256']==digest(wire)and answer['source_native']==wire['source_native']
     self.save(f'cycle_{cycle:04d}_teb_answer.json',answer)
     if not answer['passed']:self.poisoned=True;self.contract.refuse()
     return answer
    assert self.selector.get_map(),'TEB_NATIVE_MISSING_CURRENT_ANSWER'
  except BaseException:
   self.poisoned=True;self.contract.refuse();raise
 def close(self):
  assert not self.closed,'TEB_SESSION_CLOSE_NO_RETRY';self.closed=True
  if self.process is None:return
  try:
   self.save('teb_native/STOP.json',dict(sequence=self.sequence,closed=True))
   end=time.monotonic()+8
   while self.selector.get_map()and time.monotonic()<end:self.drain(.05)
   self.process.wait(timeout=2)
   finals=[v for tag,v in self.records if tag=='PHASE_TEB_FINAL'];assert len(finals)==1,'TEB_NATIVE_FINAL_MISSING'
   self.save('TEB_NATIVE_SESSION_RESULT.json',finals[0]);assert finals[0]['closed']and finals[0]['counts']['destructor_calls']==1,'TEB_NATIVE_SESSION_NOT_CLOSED'
  finally:
   if self.process.poll()is None:
    p=Path('/proc',str(self.identity['pid']),'stat');assert p.read_text().split(') ',1)[1].split()[19]==self.identity['start_ticks']
    os.killpg(self.identity['pgid'],signal.SIGTERM)
    try:self.process.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(self.identity['pgid'],signal.SIGKILL);self.process.wait(timeout=5)
   self.save('TEB_NATIVE_CONSOLE.json',dict(text=self.console.decode(errors='replace'),returncode=self.process.poll(),sequence=self.sequence,poisoned=self.poisoned,owned=self.identity))
