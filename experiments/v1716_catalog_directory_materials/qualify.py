"""Check the exact omitted empty catalog dirs, never execute package contents."""
import ast,importlib.util,io,json,os,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOFTWARE_REVIEW.json').exists()
 s=importlib.util.spec_from_file_location('v1716_catalog_reader',C/'materials.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 old=ast.parse((R/'experiments/v1712_root_member_materials/materials.py').read_text());new=ast.parse((C/'materials.py').read_text());assert len(old.body)==len(new.body)
 assert all(ast.dump(a)==ast.dump(b)for a,b in zip(old.body,new.body)if not isinstance(a,ast.FunctionDef)or a.name!='extract')
 fixture=O/'software_fixtures';fixture.mkdir();meter=m.Meter(fixture);prefix=fixture/'sysroot';meter.mkdir(prefix)
 def make(path,kind,body=b''):
  buf=io.BytesIO()
  with tarfile.open(fileobj=buf,mode='w:xz')as tar:
   row=tarfile.TarInfo(path);row.type=kind;row.mode=0o755 if kind==tarfile.DIRTYPE else 0o644;row.size=len(body);tar.addfile(row,io.BytesIO(body)if body else None)
  blob=b'!<arch>\n'
  for name,data in {'debian-binary':b'2.0\n','control.tar':b'','data.tar.xz':buf.getvalue()}.items():blob+=f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{100644:<8}{len(data):<10}`\n'.encode()+data+(b'\n'if len(data)%2 else b'')
  return blob
 exclusions=[]
 for i,name in enumerate(['var','var/lib','var/lib/sgml-base','var/lib/xml-core']):
  p=fixture/(str(i)+'.deb');meter.write(p,make('./'+name,tarfile.DIRTYPE));m.extract(p,prefix,meter,'fake',{},exclusions)
 assert len(exclusions)==4 and not(prefix/'var').exists()
 negatives=[]
 for i,(name,kind,body)in enumerate([('var',tarfile.REGTYPE,b''),('var/lib/sgml-base',tarfile.REGTYPE,b'x'),('var/lib/other',tarfile.DIRTYPE,b''),('var/../usr/escape',tarfile.REGTYPE,b'x')]):
  p=fixture/('bad'+str(i)+'.deb');meter.write(p,make(name,kind,body))
  try:m.extract(p,prefix,meter,'bad',{},[])
  except AssertionError:negatives.append(name)
  else:raise AssertionError('NON_DIRECTORY_OR_OUTSIDE_CATALOG_ACCEPTED')
 raw=R/'runs/v1712_root_member_materials/rounds/03_runtime_base_01/packages/sgml-base_1.29.1_all.deb';assert raw.exists()
 proof=dict(passed=True,only_exact4_empty_directory_metadata_excluded=True,no_var_path_created=True,negative_cases=negatives,all_other_top_level_AST_unchanged=True,real_sgml_failure_supplement_sha256=m.sha(R/'runs/v1712_root_member_materials/rounds/03_runtime_base_01/UNSELECTED_NAMESPACE_FAILURE_SUPPLEMENT.json'),models=0,package_execution=False)
 (O/'SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
