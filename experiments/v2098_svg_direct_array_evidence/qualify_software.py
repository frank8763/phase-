"""Saved-array timing/integrity and exact original deadline regression seam."""
import hashlib,importlib.abc,importlib.util,json,os,sys,time,types,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name

def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
 os.environ['CUDA_VISIBLE_DEVICES']=''
 assert not(D/'RESULT.json').exists();result=dict(passed=False,models=0,DLLs=0,optimizer_queries=0,physics=0,replay=0,new_old_case_audit=False)
 try:
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,n,*a):
    if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SOFTWARE_NO_MODEL_IMPORT:'+n)
  sys.meta_path.insert(0,Ban());import numpy as np
  old=load('old_scalar_float_bits',R/'experiments/v1902_dwa_lossless_evidence/array_bits.py');new=load('new_vectorized_bits',C/'array_bits.py');pack=load('original_proof_container',R/'experiments/v1903_dwa_durable_proof_pack/proof_pack.py')
  source=R/'runs/v1672_svg_direct_live_component/actual/CURRENT_SHADOW.npz'
  with np.load(source)as z:arrays={k:z[k].copy()for k in z.files}
  class Map:
   files=list(arrays)
   def __getitem__(self,k):return arrays[k]
  samples=[]
  for label,codec in [('old',old),('new',new)]:
   t=time.monotonic();raw=pack.array_container(np,Map(),codec.encode);encoded=pack.blob('same_closed_array_math_only.npz',raw);encode_s=time.monotonic()-t;t=time.monotonic()
   decoded=pack.read_arrays(raw,codec.decode);elapsed=time.monotonic()-t
   assert all(decoded[k].tobytes()==a.tobytes()for k,a in arrays.items())
   samples.append(dict(codec=label,packed_bytes=len(encoded),encode_s=encode_s,decode_s=elapsed,arrays_raw_bytes=sum(a.nbytes for a in arrays.values())))
  # Preserve all IEEE754 payload bits, including signed zero, denormals,
  # infinities and NaN payloads; no tolerance or quantization.
  words=np.random.default_rng(2098).integers(0,2**64,size=(2211,8),dtype=np.uint64);words[:6,0]=[0,2**63,1,0x7ff0000000000000,0x7ff8000000000051,0xfff0000000000000];x=words.view(np.float64)
  h,p=new.encode(x);assert new.decode(h,p).tobytes()==x.tobytes();bad=bytearray(p);bad[17]^=1
  try:new.decode(h,bytes(bad))
  except AssertionError:pass
  else:raise AssertionError('CORRUPTED_PAYLOAD_ACCEPTED')
  # Drive the exact old ModelWork.before deadline assertion using a virtual
  # clock. Prospective full arrays never call a numerical reconstruction at all.
  work=load('exact_failed_original_work_deadline',R/'experiments/v2095_svg_common_full_route/work.py');work.os=types.SimpleNamespace(sched_getaffinity=lambda p:{2});work.time=types.SimpleNamespace(time=lambda:570.001)
  ledger=work.ModelWork(dict(python_native_cap=25000000,cpp_native_cap=150000000),570.)
  try:ledger.before('python',1)
  except AssertionError:old_red=True
  else:raise AssertionError('ORIGINAL_DEADLINE_RED_MISSING')
  t=time.monotonic()
  for i in range(32):
   decoded=pack.read_arrays(raw if samples[-1]['codec']=='new'else b'',new.decode);assert decoded['states'].tobytes()==arrays['states'].tobytes()
  result.update(passed=True,old_actual_deadline_red=old_red,prospective_full_arrays_no_reconstruction_needed=True,timing=samples,vectorized_decode_32_s=time.monotonic()-t,byte_exact_full_arrays=True,arbitrary_IEEE754_bits_exact=True,corruption_refused=True,closed_input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),closed_input=str(source.relative_to(R)),source_SHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'array_bits.py',C/'qualify_software.py']})
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result['closed']=True;(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
