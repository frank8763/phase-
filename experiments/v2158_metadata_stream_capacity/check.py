"""Whole9994-record closed corpus, IN MEMORY only; not a physical re-audit."""
from pathlib import Path
import importlib.util,hashlib,json,os,time,resource,zlib,copy
from codec import Encoder,record,verify,h
R=Path(__file__).resolve().parents[2];S=R/'runs/v2158_metadata_stream_capacity';P=R/'runs/v2151_psf_wrapper_identity_binding/components/PSF/actual'
assert os.sched_getaffinity(0)=={1}and not(S/'RESULT.json').exists()
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);start=time.monotonic();source=R/'experiments/v2151_psf_wrapper_identity_binding/metadata_pack.py'
spec=importlib.util.spec_from_file_location('exact_old_json_record_reader',source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
pins={str(p.relative_to(R)):h(p.read_bytes())for p in [P/old.PACK,P/old.INDEX,source]};idx=old.index(P);enc=Encoder();old_physical=hashlib.sha256();raw_bytes=0
for name,row in idx.items():
 raw=old.read_bytes(P/name);assert h(raw)==row['raw_sha256'];enc.append(name,raw);raw_bytes+=len(raw)
 # This check also proves the ORIGINAL physical compressed-pack bytes can be
 # recreated, under the pinned same zlib version, without any model execution.
 rebuilt=zlib.compress(raw,1);assert h(rebuilt)==row['compressed_sha256'];old_physical.update(rebuilt)
assert old_physical.hexdigest()==pins[str((P/old.PACK).relative_to(R))]
assert verify(enc.data,enc.rows)==len(idx)==9994
for k in [0,1,127,128,129,999,1000,len(idx)-1]:assert h(record(enc.data,enc.rows,k))==enc.rows[k]['raw_sha256']
negative=[]
def reject(name,fn):
 try:fn()
 except(AssertionError,zlib.error):negative.append(name)
 else:raise AssertionError('STREAM_NEGATIVE_ACCEPTED:'+name)
reject('duplicate_logical_name',lambda:enc.append(enc.rows[0]['name'],b'{}'))
reject('truncated_stream',lambda:verify(enc.data[:-1],enc.rows))
bad=bytearray(enc.data);bad[len(bad)//2]^=1;reject('changed_payload',lambda:verify(bad,enc.rows))
rows=copy.deepcopy(enc.rows);rows[2],rows[3]=rows[3],rows[2];reject('reordered_index',lambda:verify(enc.data,rows))
index_bytes=len(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n'for r in enc.rows));original_bytes=(P/old.PACK).stat().st_size+(P/old.INDEX).stat().st_size
v=dict(passed=True,closed=True,source_records_verified=9994,original_pack_plus_index_bytes=original_bytes,new_stream_bytes=len(enc.data),new_index_bytes=index_bytes,new_stream_plus_index_bytes=len(enc.data)+index_bytes,ratio=(len(enc.data)+index_bytes)/original_bytes,raw_serialized_JSON_bytes=raw_bytes,all_original_JSON_SHA_exact=True,original_physical_pack_reencoding_SHA_exact=True,zlib_version=zlib.ZLIB_VERSION,zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,random_access_cases=8,negative_cases=negative,all_work_in_memory_no_new_large_files=True,models=0,NLP=0,physics=0,replay=0,new_physical_audit=0,production_writer_or_grants_qualified=False,source_SHA256=pins,wall_s=time.monotonic()-start,helper_sha256=h(Path(__file__).read_bytes()))
assert all(h((R/n).read_bytes())==sha for n,sha in pins.items());(S/'RESULT.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
