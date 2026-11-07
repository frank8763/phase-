"""Generate only the reviewed operations continuation; scientific worker unmodified."""
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;old=R/'experiments/staged_90_then12_20261106'
def rewrite(text,before,after,count=1):
 assert text.count(before)==count,(before,text.count(before),count)
 return text.replace(before,after)
for name in ['evidence_rules.py','limits.py','archive.py','hold_awake.py']:(C/name).write_bytes((old/name).read_bytes())
engine=(old/'engine.py').read_text()
start=engine.index('def unchanged():');end=engine.index('\ndef stage_run(',start)
engine=engine[:start]+'''def unchanged():
 frozen=read(C/'DEVELOPMENT_FREEZE.json');assert all(sha(R/n)==h for n,h in frozen['files'].items()),'FROZEN_SOURCE_OR_INPUT_CHANGED'
 claim=read(ROOT/'DEVELOPMENT12_WINDOW_CLAIM.json');assert sha(ROOT/'SUPPLEMENT_FINALIZED.json')==claim['pilot_finalized_sha256'],'SUPPLEMENT_REFERENCE_CHANGED'
 assert all(sha(R/x['path'])==x['sha256']for x in read(ROOT/'ORIGINAL_EVIDENCE_FREEZE.json')),'ORIGINAL_PILOT_CHANGED'
''' +engine[end:]
engine=rewrite(engine,"ROOT=R/'runs/staged_90_then12_20261106'","ROOT=R/'runs/staged_audit_completion_20261106'")
engine=rewrite(engine,"phase=O/stage;phase.mkdir(exist_ok=False)","assert stage=='development12';phase=O/stage;phase.mkdir(exist_ok=False)")
engine=rewrite(engine,"cmd+=[str(C.relative_to(R)/'worker_entry.py')]\n    if not models:cmd+=['--saved-only']\n    cmd+=[W.name,script]",'''if script=='replay_native_audit.py':
     cmd+=[str((R/'experiments/staged_90_then12_20261106/worker_entry.py').relative_to(R)),W.name,script]
    else:
     cmd+=[str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(Path(args[0]))]
     if script=='audit_run.py':cmd+=['--model-deadline',str(deadline)]
     cmd+=[script]''')
engine=rewrite(engine,"limits['outer']+180","limits['outer']+720")
engine=rewrite(engine,"pair/'audit_run.py.console',120,True","pair/'audit_run.py.console',600,True")
engine=rewrite(engine,"read(O/'pilot90/FINAL_INDEPENDENT_AUDIT.json')['records'][0]","read(ROOT/'FINAL_INDEPENDENT_AUDIT.json')['records'][0]")
engine=rewrite(engine,"[str((O/'pilot90/FINALIZED.json').relative_to(R)),str((O/'pilot90/FINAL_INDEPENDENT_AUDIT.json').relative_to(R))]","[str((ROOT/'SUPPLEMENT_FINALIZED.json').relative_to(R)),str((ROOT/'FINAL_INDEPENDENT_AUDIT.json').relative_to(R))]")
ast.parse(engine);(C/'engine.py').write_text(engine)
final=(old/'finalize.py').read_text()
final=rewrite(final,"from archive import archive","from archive import archive\nC=Path(__file__).parent\nROOT=Path(__file__).resolve().parents[2]/'runs/staged_audit_completion_20261106'")
final=rewrite(final,"stage in['pilot90','development12']","stage in['development12']")
final=rewrite(final,"freeze=read(W/'CANDIDATE_FREEZE.json')","freeze=read(C/'DEVELOPMENT_FREEZE.json')")
final=rewrite(final,"can_transition(read(O/'pilot90/FINALIZED.json'))","can_transition(read(ROOT/'SUPPLEMENT_FINALIZED.json'))")
final=rewrite(final,"archive(R,P,W,report,W/'CANDIDATE_FREEZE.json'","archive(R,P,W,report,C/'DEVELOPMENT_FREEZE.json'")
ast.parse(final);(C/'finalize.py').write_text(final)
print(json.dumps(dict(operations_only=True,scientific_files_modified=0,engine_syntax=True,finalizer_syntax=True)))
