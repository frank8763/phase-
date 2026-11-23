"""Reuse actual namespace proof; bind only the necessary changed C headers."""
import ast,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1720_teb_writable_mountpoints'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text())
 old=R/'experiments/v1720_teb_writable_mountpoints';assert(C/'namespace.py').read_bytes()==(old/'namespace.py').read_bytes();assert(C/'owner.py').read_text()==(old/'owner.py').read_text().replace('v1721_teb_mount_build_recovery','v1725_teb_header_build_recovery').replace('v1720_exact_namespace','v1724_exact_namespace')
 assert read(P/'RESULT.json')['configure_passed'];inputs=read(P/'INPUT_BINDING.json');headers=R/'runs/v1722_focal_c_headers/rounds/05_focal_headers_01';assert read(headers/'RESULT.json')['passed'];manifest=read(headers/'UNPACK_MANIFEST.json')
 assert all(row['path']in ['usr','usr/include']or row['path'].startswith('usr/include/')for row in manifest['entries'].values())
 inputs['native_roots'].append(str((headers/'sysroot').relative_to(R)));inputs['native_manifests'].append(str((headers/'UNPACK_MANIFEST.json').relative_to(R)))
 for p in [P/'POST_ROUND_STORAGE_BARRIER.json',headers/'POST_ROUND_STORAGE_BARRIER.json']:
  v=read(p);assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items());inputs['barriers'].append(str(p.relative_to(R)))
 for p in [P/'RESULT.json',P/'compile.console',headers/'RESULT.json',headers/'UNPACK_MANIFEST.json',headers/'POST_ROUND_STORAGE_BARRIER.json']:inputs['files_SHA256'][str(p.relative_to(R))]=sha(p)
 assert all(sha(R/k)==h for k,h in inputs['files_SHA256'].items());(O/'INPUT_BINDING.json').write_text(json.dumps(inputs,indent=2)+'\n')
 proof=dict(passed=True,scope='EXACT_ACTUAL_NAMESPACE_REUSE_CHANGED_HEADER_INPUT_ONLY',namespace_sha256=sha(C/'namespace.py'),namespace_actual_configure_result_sha256=sha(P/'configure_RETURN.json'),header_only_manifest_sha256=sha(headers/'UNPACK_MANIFEST.json'),new_software_cases=0,models=0,compiler_calls=0)
 (O/'NAMESPACE_SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n');files=[p for p in C.iterdir()if p.is_file()and p.name!='CONFIG.json']
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 (C/'CONFIG.json').write_text(json.dumps(dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},input_binding_sha256=sha(O/'INPUT_BINDING.json')),indent=2)+'\n');used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(passed=True,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
