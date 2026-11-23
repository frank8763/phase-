"""One current query child, bounded pipe/dual clock and exact owned identity."""
import json,os,selectors,signal,subprocess,time
from pathlib import Path
from context import C,O,R,read,sha,load,digest

def query(wire,source,out,save):
 assert not(out/'TEB_QUERY_CLAIM.json').exists(),'TEB_QUERY_NO_RETRY'
 a=read(O/'PILOT_ADMISSION.json');assert a['models_authorized']and a['scope']=='TEB_FRESH_T0_ORIGINAL_ACTUATOR_COMPONENT'
 assert a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
 assert os.sched_getaffinity(0)=={2}and not(R/'REVIEW_PENDING').exists()
 for p in C.iterdir():
  if p.is_file():assert sha(p)==source[str(p.relative_to(R))]
 native=out/'teb_native'
 for name in ['build','tmp','build/empty_cwd','build/home']:(native/name).mkdir(parents=True,exist_ok=False)
 n=load('v1739_readonly_native_namespace',C/'native_namespace.py')
 argv=n.command([n.PYTHON,'-I','-B','-S',str(C/'native_query.py'),'--query-once'],native)
 assert '--bind'not in argv,'NATIVE_QUERY_CHILD_MUST_BE_READONLY'
 envelope=dict(wire=wire,wire_sha256=digest(wire),source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'))
 data=(json.dumps(envelope,separators=(',',':'),allow_nan=False)+'\n').encode();assert len(data)<=1024**2
 started=time.monotonic();wall=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 save('TEB_QUERY_CLAIM.json',dict(query_attempts=1,query_returns=0,query_inflight_unknown=True,wire_sha256=digest(wire),maximum_s=60,source_native=wire['source_native'],models_in_child=False))
 child=None;raw=bytearray();identity=None
 try:
  save('TEB_QUERY_ENVELOPE.json',envelope)
  with(out/'TEB_QUERY_ENVELOPE.json').open('rb')as readonly_input:
   child=subprocess.Popen(argv,cwd=R,stdin=readonly_input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  stat=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=stat[19],boot_id=boot)
  save('TEB_QUERY_OWNED_CHILD.json',identity)
  sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ)
  while sel.get_map():
   assert time.monotonic()<started+60 and time.time()<wall+60 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'TEB_SINGLE_QUERY_DUAL_CLOCK_LIMIT'
   for key,_ in sel.select(.1):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:sel.unregister(key.fileobj);continue
    assert len(raw)+len(block)<=256*1024,'TEB_NATIVE_PIPE_LIMIT';raw.extend(block)
  child.wait(timeout=5)
  finals=[json.loads(x.split('PHASE_TEB_FINAL ',1)[1])for x in raw.decode(errors='replace').splitlines()if x.startswith('PHASE_TEB_FINAL ')]
  assert len(finals)==1,'TEB_NATIVE_TERMINAL_RECORD_MISSING'
  answer=finals[0];assert answer['wire_sha256']==digest(wire)
  save('TEB_NATIVE_QUERY_RESULT.json',answer)
  assert child.returncode==0 or not answer['passed'],'TEB_NATIVE_RETURN_CONFLICT'
  return answer
 finally:
  if child is not None and child.poll()is None:
   s=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();assert s[19]==identity['start_ticks']
   os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
  save('TEB_NATIVE_CONSOLE.json',dict(text=raw.decode(errors='replace'),raw_hex=raw.hex(),returncode=child.returncode if child else None,wall_s=time.monotonic()-started,pipe_cap_bytes=256*1024))
