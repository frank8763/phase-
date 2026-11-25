"""Actual repaired Client.wait and original quota boundary, zero native calls."""
from context import R,C,O,load,put
from console_codec import Writer,decoded_chunks,TF_SUFFIX
import hashlib,json,os,selectors,subprocess,time

def check():
 os.sched_setaffinity(0,{6});client_type=load('RPP_live_wait_no_controller',C/'native_client.py').Client;boundary=load('original_exact_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');out=O/('live_wait_software_'+str(len(list(O.glob('live_wait_software*')))));out.mkdir(exist_ok=False);charged=[]
 line=b'[ERROR] [1795612934.345198789'+TF_SUFFIX;n=(4*1024**2)//len(line)+1
 script="import os,sys,time;line=bytes.fromhex(sys.argv[1]);n=int(sys.argv[2]);[os.write(2,line)for _ in range(n)];time.sleep(.05);os.write(1,b'RPP_REPLY {\\\"passed\\\":true}\\n')"
 def charge(p,n):assert p.is_relative_to(out);charged.append(n)
 with boundary.OutputBoundary(out,charge):
  p=subprocess.Popen(['/usr/bin/python3.12','-I','-B','-S','-c',script,line.hex(),str(n)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  client=client_type.__new__(client_type);client.sel=selectors.DefaultSelector();client.buffers={};client.log=Writer(out/'actual_wait.rpplog');client.messages=[];client.received_bytes=0
  for stream in [p.stdout,p.stderr]:client.sel.register(stream,selectors.EVENT_READ);client.buffers[stream.fileno()]=bytearray()
  try:answer=client.wait('RPP_REPLY ',10);assert answer==dict(passed=True);p.wait(timeout=5)
  finally:
   if p.poll()is None:p.terminate();p.wait(timeout=5)
  receipt=client.log.finish()
 h=hashlib.sha256();raw=0
 for value in decoded_chunks(out/'actual_wait.rpplog'):h.update(value);raw+=len(value)
 assert h.hexdigest()==hashlib.sha256(line*n).hexdigest()==receipt['raw_SHA256']and raw==len(line)*n and receipt['packed_bytes']<=receipt['cap_bytes']
 value=dict(passed=True,actual_new_Client_wait=True,original_OutputBoundary_used=True,source_error_reproduction_now_passes=True,producer_raw_bytes=raw,lossless_receipt=receipt,every_stored_write_charged=charged,models=0,DLL_loads=0,controller_calls=0,physics=0,replay=0)
 put(O/'LIVE_WAIT_SOFTWARE_PROOF.json',value);print(json.dumps(dict(passed=True,old_error='RPP_PEER_CONSOLE_CAP',raw=raw,packed=receipt['packed_bytes'],models=0)));return value
if __name__=='__main__':check()
