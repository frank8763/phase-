"""Correct one missing mutable-report inventory reference; no numerical edits."""
from pathlib import Path
import ast, hashlib, importlib.util, json, os, sys
R=Path(__file__).resolve().parents[2]; C=Path(__file__).resolve().parent; D=R/'runs'/C.name
H=R/'experiments/v2007_mppi_observed_source_recovery'
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});stage=sys.argv[1]
 if stage=='archive':
  assert not(D/'ARCHIVE_CLAIM.json').exists()
  assert not(R/'runs/v2007_mppi_observed_source_recovery/ARCHIVE_INDEX.json').exists()
  assert not(R/'runs/v2007_mppi_observed_source_recovery/remote_delivery').exists()
  target=H/'finalize.py'; proof=json.loads((D/'ORIGINAL_FAILURE.json').read_text())
  assert hashlib.sha256(target.read_bytes()).hexdigest()==proof['original_helper_sha256']
  tree=ast.parse(target.read_text())
  class RemoveMutableReport(ast.NodeTransformer):
   count=0
   def visit_For(self,n):
    if isinstance(n.target,ast.Name) and n.target.id=='name' and isinstance(n.iter,ast.List) and [x.value for x in n.iter.elts if isinstance(x,ast.Constant)]==['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPP_SYNCHRONOUS_LOADING_20261126.md']:
     self.count+=1;return None
    return self.generic_visit(n)
  edit=RemoveMutableReport();tree=edit.visit(tree)
  assert edit.count==1,'EXACT_ONE_MUTABLE_REPORT_LOOP_ONLY'
  scope={'__name__':'metadata_only_archive','__file__':str(target)}
  exec(compile(tree,str(target),'exec'),scope)
  scope['C']=C;scope['O']=D;scope['main']()
 else:
  target=H/('source_sync.py'if stage=='sync'else 'deliver.py'if stage=='deliver'else 'chain.py')
  m=load('exact_frozen_transport_'+stage,target)
  if stage=='sync':m.O=D;m.source_sync()
  elif stage=='deliver':m.D0=D;raise SystemExit(m.main())
  elif stage=='chain':m.D=D;m.main()
  else:raise AssertionError('UNKNOWN_STAGE')
if __name__=='__main__':main()
