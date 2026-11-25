"""Exercise actual old Client.wait with one actual saved diagnostic signature."""
from pathlib import Path
import importlib.util,json,os,selectors,subprocess,sys,time,hashlib,collections
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;old=R/'experiments/v1978_rpp_first_common_round';sys.path.insert(0,str(old))
def main():
 os.sched_setaffinity(0,{6});p=R/'runs/v1978_rpp_first_common_round/actual/RPP_NATIVE_CONSOLE.json';saved=json.loads(p.read_text());lines=saved['text'].splitlines();line=next(x for x in lines if '[tf2_buffer]'in x).encode()+b'\n';n=(4*1024**2)//len(line)+1
 spec=importlib.util.spec_from_file_location('closed_RPP_client_readonly',old/'native_client.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 script="import os,sys,json,time;line=bytes.fromhex(sys.argv[1]);n=int(sys.argv[2]);[os.write(2,line)for _ in range(n)];time.sleep(.05);os.write(1,b'RPP_REPLY {\\\"passed\\\":true}\\n')"
 child=subprocess.Popen(['/usr/bin/python3.12','-I','-B','-S','-c',script,line.hex(),str(n)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 client=m.Client.__new__(m.Client);client.sel=selectors.DefaultSelector();client.buffers={};client.log=bytearray();client.messages=[];client.received_bytes=0
 for stream in [child.stdout,child.stderr]:client.sel.register(stream,selectors.EVENT_READ);client.buffers[stream.fileno()]=bytearray()
 start=time.monotonic();error=None
 try:client.wait('RPP_REPLY ',10)
 except AssertionError as e:error=str(e)
 finally:
  if child.poll()is None:child.terminate()
  child.wait(timeout=5)
 assert error=='RPP_PEER_CONSOLE_CAP',(error,child.returncode)
 result=dict(reproduced=True,error=error,one_saved_line_bytes=len(line),repetitions=n,producer_bytes=n*len(line),original_cap=4*1024**2,original_client_sha256=hashlib.sha256((old/'native_client.py').read_bytes()).hexdigest(),saved_console_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),saved_tf2_error_lines=sum('[tf2_buffer]'in x for x in lines),saved_total_lines=len(lines),models=0,RPP_DLL=0,controller_queries=0,physical_native=0,replay_native=0,wall_s=time.monotonic()-start)
 (O/'CONSOLE_REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
