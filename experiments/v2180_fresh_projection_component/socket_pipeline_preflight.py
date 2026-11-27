"""Real worker-body/socket/OutputBoundary pipeline, explicit fake solver only."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,selectors,time,importlib.util,copy,signal,datetime
from peer_guard import R,C,S
from peer_namespace import command
from handshake import bind,digest
assert os.sched_getaffinity(0)=={5}and not(S/'SOCKET_PIPELINE_SOFTWARE.json').exists()and not(S/'SOURCE_ONCE.json').exists()
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
io=load('original_scoped_write_boundary_no_model',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');budget_mod=load('capped_software_writer',R/'experiments/v2177_priest_vector_orientation/write_budget.py');channel_mod=load('original_one_frame_owned_socket',R/'experiments/v2151_psf_wrapper_identity_binding/channel.py')
out=S/'software_socket';out.mkdir(exist_ok=False);budget=budget_mod.Budget(out);p=None;i=None;channel=None;sel=None;result=None
with io.OutputBoundary(out,budget.reserve):
 def save(name,value):(out/name).write_text(json.dumps(value,allow_nan=False,separators=(',',':'))+'\n')
 a=dict(scope='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY',maximum_queries=1,models_authorized=False,run_id='SYNTHETIC_SOCKET_ONLY',query_nonce='SYNTHETIC_SOCKET_NOT_ACTUAL_QUERY',source_freeze_sha256='a'*64,worker_sha256=hashlib.sha256((C/'peer_entry.py').read_bytes()).hexdigest());save('ADMISSION_FIXTURE.json',a)
 receipt=json.loads((R/'runs/v2176_sccr_common_plant_component/components/SCCR/actual/cycle_000000_origin.json').read_bytes())['receipt'];public=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'
 f=dict(schema='FRESH_REST_ORIENTATION_PROJECTION_V1',episode_id=a['run_id'],query_sequence=0,query_nonce=a['query_nonce'],source_freeze_sha256=a['source_freeze_sha256'],numerical_admission_sha256='',receipt=receipt,public_known=json.loads(public.read_bytes()),public_known_sha256=hashlib.sha256(public.read_bytes()).hexdigest(),whole_goal_xy=[4.,-2.]);f,claim=bind((out/'ADMISSION_FIXTURE.json').read_bytes(),f);save('CLAIM_FIXTURE.json',claim);save('FRAME_FIXTURE.json',f)
 channel=channel_mod.FrameChannel(maximum_frames=1);env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 started=time.monotonic();events=[];reply=None;closed=None;stdout_bytes=0;chunks=0;stderr_bytes=0;buf={}
 try:
  p=subprocess.Popen(['taskset','-c','0','nice','-n','19',*command(C/'socket_fixture_child.py')],cwd=R,env=env,stdin=channel.child.fileno(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip());save('OWNED_SOFTWARE_CHILD.json',i);channel.detach_child_endpoint();ack=channel.send(f);sel=selectors.DefaultSelector()
  for stream in [p.stdout,p.stderr]:sel.register(stream,selectors.EVENT_READ);buf[stream.fileno()]=bytearray()
  while sel.get_map():
   assert time.monotonic()-started<20 and stdout_bytes+stderr_bytes<64*1024,'SOFTWARE_SOCKET_FINITE_TIME_OR_BYTES'
   for key,_ in sel.select(.1):
    data=os.read(key.fileobj.fileno(),16384)
    if not data:sel.unregister(key.fileobj);continue
    if key.fileobj is p.stderr:stderr_bytes+=len(data)
    else:stdout_bytes+=len(data)
    save('CONSOLE_CHUNK_'+str(chunks)+'.json',dict(stream='stdout'if key.fileobj is p.stdout else'stderr',hex=data.hex()));chunks+=1;z=buf[key.fileobj.fileno()];z.extend(data)
    while b'\n'in z:
     line,_,rest=z.partition(b'\n');z[:]=rest
     if key.fileobj is not p.stdout:continue
     label,_,payload=line.partition(b' ');value=json.loads(payload);events.append(label.decode())
     if label==b'PROJECTION_RAW_RETURN':save('RAW_FAKE_RETURN.json',value)
     elif label==b'PROJECTION_REPLY':
      assert reply is None and value['transport_ack']==ack and value['query_sha256']==digest(f)and value['query_nonce']==a['query_nonce'];reply=value;save('REPLY_FIXTURE.json',value);channel.acknowledge(value['transport_ack']);channel.finish_input()
     elif label==b'PROJECTION_CLOSED':closed=value;save('CLOSED_FIXTURE.json',value)
  p.wait(timeout=3);assert p.returncode==0 and reply is not None and reply['passed']and closed is not None and closed['all_source_SHA_after']and closed['NLP_attempted_calls']==closed['NLP_returns']==1 and not closed['inflight_unknown']
  assert events==['PROJECTION_PROGRESS','PROJECTION_RAW_RETURN','PROJECTION_REPLY','PROJECTION_CLOSED']and channel.frames==1 and channel.pending is None
  result=dict(passed=True,actual_pipeline='original OutputBoundary + original FrameChannel + readonly Phase namespace + actual updated worker body',all_admission_and_optimizer_are_explicit_fakes=True,real_SLSQP_models_physics_Source=0,software_child_CPU=0,parent_CPU=5,sent_frames=1,wire_bytes=ack['bytes'],ack_sha256=ack['sha256'],source_derived_fake_NLP_calls=1,stdout_bytes=stdout_bytes,stderr_bytes=stderr_bytes,console_chunks=chunks,closed_after_reply_and_ack=True,events=events,charged_software_write_bytes=budget.charged,physical_authority=False,wall_s=time.monotonic()-started)
 except BaseException as e:
  import traceback
  result=dict(passed=False,error=repr(e),traceback=traceback.format_exc(),real_SLSQP_models_physics_Source=0);save('PIPELINE_FAILURE.json',result);raise
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=3)
  if channel is not None:channel.close()
  if sel is not None:sel.close()
assert result['passed'];result['source_sha256']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'socket_fixture_child.py',C/'socket_pipeline_preflight.py',C/'peer_entry.py',C/'peer_guard.py',C/'handshake.py',C/'fresh_problem.py']};result['created_at']=datetime.datetime.now().astimezone().isoformat();(S/'SOCKET_PIPELINE_SOFTWARE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'}))
