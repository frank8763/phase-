"""Future bounded CPU-math worker import seam; missing authority refuses first."""
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import types
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def load(*,authority,request,lock,output_boundary):
 admission=R/'runs/v1500_priest_thread_observation/OPTIMIZER_ONLY_ADMISSION.json'
 assert admission.is_file(),'PRIEST_OPTIMIZER_TARGET_NOT_ADMITTED'
 assert json.loads(admission.read_text())==authority and authority['scope']=='PRIEST_OPTIMIZER_ONLY'and not authority['models_authorized']
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 assert os.environ.get('CUDA_VISIBLE_DEVICES')==''and os.environ.get('JAX_PLATFORMS')=='cpu'and os.environ.get('JAX_ENABLE_X64')=='true'
 assert all(os.environ.get(k)=='1'for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
 assert time.time()<authority['absolute_deadline_unix']<=1795395600 and time.monotonic()<authority['hard_stop_monotonic']
 assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and authority['request_sha256']==request['request_sha256']
 assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert Path(type(output_boundary).__enter__.__code__.co_filename).resolve()==R/'experiments/v1436_pathlib_control_rename/bounded_io.py'
 assert output_boundary.saved is not None and not output_boundary.control_paths and not output_boundary.control_renames,'PRIEST_OPTIMIZER_WORKER_BOUNDARY_NOT_INSTALLED'
 writer=output_boundary.reserve.__self__
 assert Path(writer.reserve.__func__.__code__.co_filename).resolve()==R/'experiments/v1436_pathlib_control_rename/writer_budget.py'
 assert writer.role=='PLANNER'and writer.identity==authority['source_manifest_sha256']and writer.output==output_boundary.output
 assert writer.maximum==authority['optimizer_writer_maximum_bytes']<=8*1024**2
 registry=json.loads((writer.output/'EXTERNAL_WRITER_RESERVATIONS.json').read_text())
 assert registry['source_identity']==writer.identity and registry['purpose']=='PRIEST_OPTIMIZER_ONLY'
 assert registry['writers']['PLANNER']['maximum_bytes']==writer.maximum and registry['writers']['PLANNER']['source_hook_coverage_qualified']is True
 assert hashlib.sha256((writer.output/'APPROVAL.json').read_bytes()).hexdigest()==registry['approval_sha256']
 # No package imports or fallback interpreter before an exact versions scope.
 target=R/'runs/v1491_priest_dependency_target'
 completion=json.loads((target/'COMPLETION.json').read_text());assert completion['passed']and completion['all_extracted_file_SHA_verified']
 extracted_path=target/'EXTRACTED_INDEX.json'
 assert hashlib.sha256(extracted_path.read_bytes()).hexdigest()==authority['dependency_index_sha256']
 extracted=json.loads(extracted_path.read_text());assert extracted['remote_recovery_proof_sha256']==authority['dependency_remote_proof_sha256']
 site=target/'site';assert str(site)not in sys.path and site.is_dir()and not site.is_symlink()
 for row in extracted['files']:
  path=R/row['path'];assert path.is_relative_to(site)and not path.is_symlink()and path.stat().st_size==row['bytes']
  h=hashlib.sha256()
  with path.open('rb')as stream:
   for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
  assert h.hexdigest()==row['sha256'],'PRIEST_PINNED_DEPENDENCY_MEMBER_CHANGED'
 sys.path.insert(0,str(site))
 versions={p:importlib.metadata.version(p)for p in ['jax','jaxlib','numpy','scipy','matplotlib']}
 assert versions==authority['qualified_distribution_versions'],'PRIEST_OPTIMIZER_DEPENDENCY_VERSION_CHANGED'
 for name in ['jax','jaxlib','bernstein_coeff_order10_arbitinterval']:
  assert name not in sys.modules,'PRIEST_OPTIMIZER_DIRTY_IMPORT_NAMESPACE'
 def exact(name,path):
  s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 port=exact('v1487_cpu_port_source',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source()
 assert port['ported_sha256']==request['port_identity']['ported_sha256']==authority['kernel_source_sha256']
 import jax
 import jax.numpy as jnp
 import numpy as np
 assert jax.config.x64_enabled and all(d.platform=='cpu'for d in jax.devices()),'PRIEST_CPU_X64_NOT_EFFECTIVE'
 helper=R/'runs/v1484_baseline_disposition_priest/upstream/priest/src/bernstein_coeff_order10_arbitinterval.py'
 assert hashlib.sha256(helper.read_bytes()).hexdigest()=='5695fc07260671785b14bc84bc89105174b58e680cb2fe0d2bc45f918ce90469'
 name='bernstein_coeff_order10_arbitinterval';spec=importlib.util.spec_from_file_location(name,helper);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
 name='v1487_exact_cpu_author_kernel';assert name not in sys.modules
 module=types.ModuleType(name);module.__file__=str(C/'ported_author_core.py');sys.modules[name]=module
 exec(compile(port['source'],module.__file__,'exec'),module.__dict__)
 return types.SimpleNamespace(module=module,author_sha256=port['author_sha256'],ported_sha256=port['ported_sha256'],versions=versions),jax,jnp,np
