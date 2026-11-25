"""Exercise actual output-boundary file-input subprocess pattern, no model."""
from context import R,C,O,load,put,sha
import os,subprocess,json

def check():
 boundary=load('same_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');out=O/'transport_software';out.mkdir();charged=[]
 def charge(path,n):
  assert path.is_relative_to(out)and type(n)is int and n>=0;charged.append(dict(path=str(path.relative_to(O)),bytes=n))
 payload='{"request_id":1}\n{"close":true}\n';target=out/'RPP_NATIVE_INPUT.jsonl'
 with boundary.OutputBoundary(out,charge):
  with target.open('x')as f:f.write(payload)
  with target.open('rb')as f:
   p=subprocess.Popen(['/usr/bin/python3.12','-I','-B','-S','-c',"import sys,json;lines=[json.loads(v)for v in sys.stdin];assert lines==[{'request_id':1},{'close':True}];print('ROUNDTRIP_OK')"],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   stdout,stderr=p.communicate(timeout=5)
  assert p.returncode==0 and stdout==b'ROUNDTRIP_OK\n'and not stderr
 assert len(charged)>=2 and sum(v['bytes']for v in charged)>=len(payload);return dict(passed=True,original_boundary_sha256=sha(R/'experiments/v1436_pathlib_control_rename/bounded_io.py'),stdin_regular_file_read_only=True,writable_PIPE_not_used=True,complete_bytes_charged=charged,subprocess_roundtrip=True,models=0,RPP_DLL=0,controller_calls=0,physics=0,replay=0)
