"""Only the corrected mountpoint interface, unchanged input chain reused."""
import ast,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1714_teb_native_namespace'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text())
 old=R/'experiments/v1714_teb_native_namespace/namespace.py';expected=old.read_text().replace('/phase-host','/tmp/phase-host').replace("'--tmpfs','/tmp',","'--tmpfs','/tmp','--tmpfs','/opt',").replace('return args+argv',"return args+['--remount-ro','/tmp','--remount-ro','/opt','--remount-ro','/home']+argv");assert expected==(C/'namespace.py').read_text()
 prior=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert prior['passed']and all(sha(R/k)==h for k,h in prior['proof_paths_SHA256'].items());assert read(P/'WRAPPER_FAILURE_DIAGNOSIS.json')['actual_CMake_calls']==0
 inputs=read(P/'INPUT_BINDING.json');assert all(sha(R/k)==h for k,h in inputs['files_SHA256'].items());inputs['barriers'].append(str((P/'POST_ROUND_STORAGE_BARRIER.json').relative_to(R)));inputs['files_SHA256'][str((P/'WRAPPER_FAILURE_DIAGNOSIS.json').relative_to(R))]=sha(P/'WRAPPER_FAILURE_DIAGNOSIS.json')
 (O/'INPUT_BINDING.json').write_text(json.dumps(inputs,indent=2)+'\n')
 s=importlib.util.spec_from_file_location('v1720_mount_interface',C/'namespace.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n);f=O/'software_fixture';f.mkdir();h=f/'host';h.write_bytes(b'unchanged');proxy=f/'proxy';rows=[];n.union(proxy,h,[],rows,'/usr/example');assert os.readlink(proxy).startswith('/tmp/phase-host/')
 cmd=n.command(O,O/'view',R/inputs['ros_root'],['ORIGINAL_CMAKE_PLACEHOLDER'])
 assert cmd.index('/tmp')<cmd.index('/tmp/phase-host/usr')and cmd.index('/opt')<cmd.index('/opt/ros/noetic')and '/phase-host/usr'not in cmd
 assert cmd[-7:-1]==['--remount-ro','/tmp','--remount-ro','/opt','--remount-ro','/home']
 proof=dict(passed=True,exact_mountpoint_only_diff=True,new_host_proxy_under_tmp=True,tmpfs_before_alias_and_opt_mount=True,readonly_setup_mounts_before_command=True,unchanged_merge_software_proof_sha256=sha(P/'NAMESPACE_SOFTWARE_REVIEW.json'),actual_bwrap_or_CMake_executed=False,models=0)
 (O/'NAMESPACE_SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n');files=[p for p in C.iterdir()if p.is_file()and p.name!='CONFIG.json']
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 config=dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},input_binding_sha256=sha(O/'INPUT_BINDING.json'));(C/'CONFIG.json').write_text(json.dumps(config,indent=2)+'\n')
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(passed=True,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
