"""New namespace merge interface software only; no downloaded code execution."""
import importlib.util,json,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def main():
 os.sched_setaffinity(0,{5});assert not(O/'NAMESPACE_SOFTWARE_REVIEW.json').exists()
 s=importlib.util.spec_from_file_location('v1714_namespace_interface',C/'namespace.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
 f=O/'software_fixture';f.mkdir();a=f/'a';b=f/'b';h=f/'host'
 for p in [a,b,h]:p.mkdir()
 (a/'same').write_bytes(b'unchanged');(b/'same').write_bytes(b'unchanged');(a/'literal').symlink_to('../lib/original.so');(h/'fallback').write_bytes(b'host')
 out=f/'view';rows=[];n.union(out,h,[a,b],rows,'/usr/example');assert os.readlink(out/'literal')=='../lib/original.so'and(out/'same').resolve().read_bytes()==b'unchanged'and os.readlink(out/'fallback').startswith('/phase-host/')
 (b/'same').write_bytes(b'different')
 try:n.union(f/'bad',h,[a,b],[],'/usr/example')
 except AssertionError as e:assert str(e)=='NATIVE_FILE_COLLISION'
 else:raise AssertionError('CONFLICT_ACCEPTED')
 proof=dict(passed=True,exact_native_merge=True,literal_package_symlink=True,host_fallback_proxy=True,nonidentical_native_collision_rejected=True,namespace_source_sha256=n.sha(C/'namespace.py'),compiler_calls=0,models=0,optimizer_calls=0)
 (O/'NAMESPACE_SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
