"""Necessary software checks for the newly repaired root-directory reader."""
import hashlib,importlib.util,io,json,os,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOFTWARE_REVIEW.json').exists()
 spec=importlib.util.spec_from_file_location('v1712_static_reader',C/'materials.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 old=R/'experiments/v1710_native_build_materials/materials.py';expected=old.read_text().replace("if not name:return None","if name in ['', '.']:return None").replace('if name is None:continue',"if name is None:\n    assert member.isdir(),'ROOT_MEMBER_NOT_DIRECTORY';continue")
 assert expected==(C/'materials.py').read_text(),'EXACT_REPAIR_SCOPE'
 fixture=O/'software_fixtures';fixture.mkdir();meter=m.Meter(fixture);prefix=fixture/'sysroot';meter.mkdir(prefix)
 def deb(rootkind):
  raw=io.BytesIO()
  with tarfile.open(fileobj=raw,mode='w:xz')as tar:
   for name in ['.','./']:
    row=tarfile.TarInfo(name);row.mode=0o755;row.type=rootkind;tar.addfile(row)
   for name in ['usr','usr/include']:
    row=tarfile.TarInfo(name);row.mode=0o755;row.type=tarfile.DIRTYPE;tar.addfile(row)
   body=b'exact original data\x00\xff\n';row=tarfile.TarInfo('./usr/include/fake.h');row.mode=0o644;row.size=len(body);tar.addfile(row,io.BytesIO(body))
  members={'debian-binary':b'2.0\n','control.tar':b'','data.tar.xz':raw.getvalue()};blob=b'!<arch>\n'
  for name,data in members.items():
   header=f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{100644:<8}{len(data):<10}`\n'.encode();assert len(header)==60;blob+=header+data+(b'\n'if len(data)%2 else b'')
  return blob
 good=fixture/'roots.deb';meter.write(good,deb(tarfile.DIRTYPE));entries={};excluded=[];m.extract(good,prefix,meter,'fixture',entries,excluded)
 assert (prefix/'usr/include/fake.h').read_bytes()==b'exact original data\x00\xff\n'
 bad=fixture/'badroot.deb';meter.write(bad,deb(tarfile.REGTYPE))
 negatives=[]
 try:m.extract(bad,prefix,meter,'bad',{},[])
 except AssertionError as e:assert str(e)=='ROOT_MEMBER_NOT_DIRECTORY';negatives.append('non_directory_root')
 else:raise AssertionError('ROOT_REGULAR_ACCEPTED')
 for name in ['../usr/a','/usr/a','home/a','usr/../a','usr\\a']:
  try:m.safe_name(name)
  except AssertionError:negatives.append(name)
  else:raise AssertionError(('BAD_PATH_ACCEPTED',name))
 plan=json.loads((R/'runs/v1710_native_build_materials/BATCHES_LOCKED.json').read_text());pkg=plan['batches'][0]['packages'][0];actual=R/'runs/v1710_native_build_materials/rounds/01_boost_headers_01/packages'/Path(pkg['Filename']).name
 assert m.sha(actual)==pkg['SHA256']and actual.stat().st_size==int(pkg['Size'])
 with tarfile.open(fileobj=io.BytesIO(m.ar_data(actual.read_bytes())),mode='r:*')as tar:
  root=tar.next();assert root.isdir()and root.name=='.'and m.safe_name(root.name)is None
 assert meter.total==meter.reconcile()
 proof=dict(passed=True,exact_two_site_reader_repair=True,root_directory_forms=['.','./'],negative_cases=negatives,original_signed_Boost_SHA_size_and_root_header_verified=True,old_unchanged_selection_meter_proof_sha256=m.sha(R/'runs/v1710_native_build_materials/SOFTWARE_REVIEW.json'),package_execution=False,compiler_calls=0,models=0)
 (O/'SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
