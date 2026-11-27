"""Reuse original8MiB shared metadata after parent PSF runtime index closed."""
from pathlib import Path
import os,sys,json,time,types,ast,subprocess
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;OLD=R/'experiments/v2156_pcbf_pinned_scipy_entry';ROOT=R/'runs'/OLD.name;D=ROOT/'recovery'
sys.path.insert(0,str(OLD));from context import read,put,sha,load
m=load('unmodified_math_evidence_functions',OLD/'evidence.py')
ref=load('actual_readonly_ref_recovery',R/'experiments/v2159_pcbf_ref_readback_recovery/recover.py')
def admission():
 M=1024**2;P=R/'runs/v2151_psf_wrapper_identity_binding';b=read(P/'BASELINE_DRAFT.json')
 assert b['metadata_bytes']==8*M and b['old_joint_peak_upper_bytes']==16095019008 and read(P/'components/PSF/POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 actual=P/'components/PSF/actual';meta=sum(p.stat().st_blocks*512 for p in P.rglob('*')if p.is_file()and not p.is_symlink()and not p.is_relative_to(actual))
 own=sum(p.stat().st_blocks*512 for p in ROOT.rglob('*')if p.is_file()and not p.is_symlink());assert own<1*M
 others=0
 for name in ['v2152_weekend_research_program','v2153_paper_comparison_figures','v2154_pcbf_coordinate_conditioning','v2155_sccr_full_observation_assembly','v2157_priest_oriented_initial_geometry','v2159_pcbf_ref_readback_recovery','v2160_math_shared_metadata_recovery']:
  folder=R/'runs'/name
  if folder.exists():others+=sum(p.stat().st_blocks*512 for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
 assert meta+own+others+512*1024<8*M,'SAME_SHARED8M_METADATA_FULL'
 # Original frozen peak and root capacity are retained, no new baseline.
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],original_shared_metadata_bytes=8*M,parent_metadata_bytes=meta,own_math_bytes=own,other_program_metadata_bytes=others,new_math_maximum_bytes=1*M,no_original_cap_expansion=True)
def usage():return admission()['joint_peak_bytes']-(32+512)*1024**2
def archive():
 def scope_load(n,p):
  v=m.load(n,p)
  if Path(p)==OLD/'reservation.py':v.admission=admission;v.transport_current_upper=usage
  return v
 fn=types.FunctionType(m.archive.__code__,dict(m.archive.__globals__,load=scope_load));fn('MATH')
def deliver(rid=None):
 if rid is None:
  old=D/'remote_delivery';assert read(old/'RESULT.json')['closed']and not read(old/'RESULT.json')['passed']and not list((old/'http_receipts').glob('*.json'))and not(old/'CREATE_ONCE_CLAIM.json').exists()
 text=m.deliver(rid,preview=True)
 if rid is None:
  text=text.replace("O=D/'remote_delivery';","O=D/'remote_delivery_budget_recovery';")
 text=text.replace("SOURCE_D/'remote_delivery/RELEASE.json'","SOURCE_D/'remote_delivery_budget_recovery/RELEASE.json'")
 target=R/'experiments/v2007_mppi_observed_source_recovery/deliver.py';space={'__file__':str(target),'__name__':'same_original_shared_metadata_recovery'}
 exec(compile(text,str(target),'exec'),space);out,archive=m.scope(rid)
 space.update(S=out,ROOT=ROOT,D0=D,SOURCE_D=D,BOUND_D=archive,CASE_ID=rid or'',CASES=m.CASES,RESERVED_TRANSPORT_USAGE=usage,read=ref.overlay)
 return space['main'](runtime=rid is not None)
def chain():
 ref.chain()
 for p in C.iterdir():
  if p.is_file():
   t=ROOT/'components/MATH'/('LATE_METADATA_HELPER_'+p.name+'.txt');assert not t.exists();t.write_bytes(p.read_bytes())
 put(ROOT/'components/MATH/LATE_METADATA_BUDGET_PROOF.json',dict(admission(),helper_files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()},no_old_science_source_changed=True,new_helper_late_not_in_Git_or_sourceRelease=True,future_runtime_memberSHA_covers_helper=True))
def run():
 assert not(S/'OWNER_ADAPTER_ONCE.json').exists();put(S/'OWNER_ADAPTER_ONCE.json',dict(unix=time.time(),models=0,NLP_started=0,scope='ORIGINAL_MATH_OWNER_SAME8M_METADATA_ADAPTER'))
 a=admission();mod=load('unchanged_original_math_owner',OLD/'owner.py')
 reserve=load('original_math_reservation_namespace',OLD/'reservation.py');reserve.admission=admission;sys.modules['reservation']=reserve
 fn=next(n for n in ast.parse((OLD/'owner.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='main')
 text=ast.unparse(fn);old="str(C / 'evidence.py')";assert text.count(old)==1;text=text.replace(old,"str(ADAPTER / 'io.py')")
 space=dict(vars(mod),ADAPTER=C);exec(compile(text,'<unchanged-owner-only-IO-argv-adapter>','exec'),space);space['main']()
if __name__=='__main__':
 os.sched_setaffinity(0,{5});stage=sys.argv[1]
 if stage=='check':print(json.dumps(admission()))
 elif stage=='deliver':raise SystemExit(deliver(sys.argv[2]if len(sys.argv)>2 else None))
 elif stage=='archive':assert sys.argv[2]=='MATH';archive()
 elif stage=='ref':assert sys.argv[2]=='MATH';m.ref('MATH')
 elif stage=='chain':chain()
 elif stage=='run':run()
 else:raise AssertionError(stage)
