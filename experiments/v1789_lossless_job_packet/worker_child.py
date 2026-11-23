"""Single CPU2 original mathematical job; inputs charged by parent, stdio bounded."""
from pathlib import Path
import hashlib,json,os,pickle,sys,time,zlib
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def main():
 os.sched_setaffinity(0,{2});path=Path(sys.argv[1]).resolve();raw=path.read_bytes();assert len(raw)<=8*1024**2 and hashlib.sha256(raw).hexdigest()==sys.argv[2]
 decoder=zlib.decompressobj();decoded=decoder.decompress(raw,64*1024**2+1);assert len(decoded)<=64*1024**2 and decoder.eof and not decoder.unused_data,'DECODED_INPUT_CAP_OR_TRAILING_BYTES';value=pickle.loads(decoded);out=Path(value['output']).resolve();assert path.is_relative_to(out/'ew_worker_inputs')and out.is_relative_to(R/'runs')and not path.is_symlink()
 parent=Path('/proc',str(value['parent_pid']),'stat');assert parent.exists()and parent.read_text().split()[21]==value['parent_start_ticks']and os.getpgrp()==value['pgid']
 assert not any(n in sys.modules for n in ['mujoco','vehicle','torch'])
 if value['metadata_only']:
  assert out.name=='metadata_exchange'and value['job'].get('software_only')is True,'METADATA_ONLY_SCOPE'
  result=value['job']['software_result'];assert result['models']==result['physical_native']==0
 else:
  # No SOURCE-mode authority ever reaches an Engine/library numerical call.
  aid=os.environ.get('PHASE_FORMAL_ASSIGNMENT');assert aid and out==R/'runs/v1643_formal_parent_metadata/rounds'/aid/'actual'
  admission=json.loads((out.parent/'FORMAL_ADMISSION.json').read_text());assert admission['models_authorized']and admission['assignment']['case_id']=='EAST_WEST'
  assert hashlib.sha256((R/admission['source_version_root']/'SOURCE_FREEZE.json').read_bytes()).hexdigest()==admission['source_freeze_sha256']
  assert time.time()<value['window']['normal_end_unix']and time.monotonic()<value['job']['deadline']
  import worker_pool
  worker_pool.initialize(str(out),value['window'],value['source'])
  sys.path.insert(0,str(R/'experiments/v1271_ew_joint_phase_validation'));import ew_retained_parallel as original
  assert Path(original.__file__).resolve()==R/'experiments/v1271_ew_joint_phase_validation/ew_retained_parallel.py'
  result=original.solve_job(value['job'])
 if not value['include_candidate_arrays']and result.get('candidate')is not None:result=dict(result,candidate={'original_nonselected_candidate_present':True})
 compressed=zlib.compress(pickle.dumps(result,protocol=4),1);assert len(compressed)+100<=4*1024**2,'WORKER_RESULT_STDIO_CAP'
 sys.stdout.buffer.write(b'PHASE_EW_JOB1\n'+hashlib.sha256(compressed).hexdigest().encode()+b'\n'+compressed);sys.stdout.buffer.flush();return 0
if __name__=='__main__':raise SystemExit(main())
