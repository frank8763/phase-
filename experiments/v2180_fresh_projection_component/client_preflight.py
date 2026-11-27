"""Actual production Client with explicit fake authority/worker, real bounded I/O."""
from context import R,C,SOURCE as S,read,load,sha
from pathlib import Path
import os,json,types,copy,sys,datetime
import client_once as client
assert os.sched_getaffinity(0)=={5}and not(S/'CLIENT_SOFTWARE.json').exists()
folder=S/'client_fixture';folder.mkdir(exist_ok=False);task=dict(read(S/'components/PROJ/PILOT_TASK.json'),run_id='SYNTHETIC_SOCKET_ONLY',output=str(folder));parent=S/'software_socket';receipt=read(parent/'FRAME_FIXTURE.json')['receipt']
# Explicit fake authority is local to this software process, not installable admission.
client.authority=lambda task:({'normal_end_unix':__import__('time').time()+300,'hard_stop_monotonic':__import__('time').monotonic()+1500,'absolute_deadline_unix':__import__('time').time()+1500,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()},'a'*64)
client.remaining=lambda _:1500;client.secrets.token_hex=lambda n:'SYNTHETIC_SOCKET_NOT_ACTUAL_QUERY';original_readbytes=Path.read_bytes
# The original readonly fake child reads fixed proof fixtures. Regenerate its
# admission and frame after Client saves its real serialized bytes, before spawn.
namespace=load('CP_readonly_SOFTWARE_child',C/'peer_namespace.py');original_popen=client.subprocess.Popen;captured=[]
def popen(cmd,*args,**kwargs):
 a=read(folder/'PROJECTION_OPTIMIZER_ADMISSION.json');f=read(folder/'PROJECTION_QUERY_FRAME.json');claim=read(folder/'PROJECTION_PEER_ONCE.json')
 # Dedicated sibling fixture input paths supplied by a new tiny child wrapper.
 p=original_popen(['taskset','-c','0','nice','-n','19',*namespace.command(C/'client_fixture_child.py')],*args,**kwargs);captured.append(p.pid);return p
client.subprocess=types.SimpleNamespace(Popen=popen,PIPE=__import__('subprocess').PIPE)
io=load('CP_original_IO_forClient',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');Budget=load('CP_fixture_budget',R/'experiments/v2177_priest_vector_orientation/write_budget.py').Budget;budget=Budget(folder)
with io.OutputBoundary(folder,budget.reserve):
 def save(name,value):(folder/name).write_text(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n')
 c=client.Client(save,receipt,task);proposal=c.query();assert c.closed and c.complete and c.replied['passed']and proposal['query']['episode_id']==task['run_id']and c.p.returncode==0;assert c.channel.frames==1
 try:c.query()
 except AssertionError:second=True
 else:raise AssertionError('SECOND_QUERY_ALLOWED')
 c.close();assert read(folder/'PROJECTION_NATIVE_ACCOUNTING.json')['NLP_returns']==1
x=dict(passed=True,actual_production_Client_body=True,admission_and_backend_explicit_software_fakes=True,readonly_Phase_child_CPU=0,parent_IO_CPU=5,one_query_only=True,raw_return_durable_before_reply_gate=(folder/'PROJECTION_NATIVE_RAW_RETURN.json').is_file(),complete_peer_reply_ack_EOF_close=True,duplicate_query_refused=second,console_bytes=c.total_bytes,cumulative_write_bytes=budget.charged,actual_real_NLP_models_physics_Source=0,source_SHA256={str(p.relative_to(R)):sha(p)for p in [C/'client_once.py',C/'client_preflight.py',C/'client_fixture_child.py']},created_at=datetime.datetime.now().astimezone().isoformat());(S/'CLIENT_SOFTWARE.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k!='source_SHA256'}))
