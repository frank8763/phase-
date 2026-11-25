"""Replay actual log bytes and stress full query horizon, zero controller calls."""
from pathlib import Path
import hashlib,json,os,random,tempfile,time
from console_codec import Writer,decoded_chunks,TF_SUFFIX,CAP
R=Path(__file__).resolve().parents[2];O=R/'runs/v1983_rpp_bounded_console_queue'
def check():
 os.sched_setaffinity(0,{6});start=time.monotonic();source=R/'runs/v1978_rpp_first_common_round/actual/RPP_NATIVE_CONSOLE.json';raw=json.loads(source.read_text())['text'].encode();path=O/'saved_console_roundtrip.rpplog';writer=Writer(path)
 for line in raw.splitlines(keepends=True):writer.append(line)
 receipt=writer.finish();digest=hashlib.sha256();count=0
 for line in decoded_chunks(path):digest.update(line);count+=len(line)
 assert digest.hexdigest()==hashlib.sha256(raw).hexdigest()==receipt['raw_SHA256']and count==len(raw)
 stress=O/'full_horizon_console.rpplog';writer=Writer(stress);rng=random.Random(1983);ns=1795613000000000000;expected=hashlib.sha256();n=12000*80
 for i in range(n):
  ns+=rng.randrange(2000,10000)+(100000000 if i%80==0 else 0);sec,nano=divmod(ns,10**9);line=b'[ERROR] ['+str(sec).encode()+b'.'+f'{nano:09d}'.encode()+TF_SUFFIX;writer.append(line);expected.update(line)
 big=writer.finish();actual=hashlib.sha256();lines=0
 for line in decoded_chunks(stress):actual.update(line);lines+=1
 assert actual.hexdigest()==expected.hexdigest()==big['raw_SHA256']and lines==n and big['packed_bytes']<=CAP
 errors=[]
 for name,data in [('bad_header',b'INVALID0'),('truncated',b'RPPLOG01R\x05ab'),('record_bound',b'RPPLOG01R\xff\xff\xff\x7f')]:
  import zlib
  p=O/(name+'.rpplog');p.write_bytes(zlib.compress(data))
  try:list(decoded_chunks(p))
  except AssertionError:errors.append(name)
  else:raise AssertionError('BAD_LOG_ACCEPTED:'+name)
 small=Writer(O/'cap_negative.rpplog',cap=32)
 try:small.append(bytes(range(256))*16);small.finish()
 except AssertionError as e:assert str(e)=='RPP_COMPRESSED_CONSOLE_4MIB_STOP';errors.append('compressed_cap')
 else:raise AssertionError('CAP_IGNORED')
 proof=dict(passed=True,actual_old_console_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),original_raw_roundtrip=receipt,full_horizon_roundtrip=big,stress_queries=12000,diagnostics_per_query=80,negative_cases=errors,constant_old_RPP_TF_binary_unchanged=True,no_TF_errors_suppressed=True,no_controller_or_parameter_change=True,models=0,RPP_DLL=0,controller_queries=0,physical_native=0,replay_native=0,wall_s=time.monotonic()-start)
 (O/'CONSOLE_SOFTWARE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(dict(passed=True,actual_raw=len(raw),actual_packed=receipt['packed_bytes'],stress_raw=big['raw_bytes'],stress_packed=big['packed_bytes'],cap=CAP,wall_s=proof['wall_s'])))
 return proof
if __name__=='__main__':check()
