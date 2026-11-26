"""Rebuild two closed real frames; no solver, plant, predictor or replay calls."""
from pathlib import Path
import ast,copy,hashlib,importlib.abc,importlib.util,json,os,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
S=R/'runs/v2090_svg_persistent_counter_fixture';A=S/'actual'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
 os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
 os.environ['CUDA_VISIBLE_DEVICES']='';O.mkdir(exist_ok=False)
 result=dict(closed=False,software_passed=False,models=0,solver_DLLs=0,constructors=0,optimizer_queries=0,physics=0,replay=0,formal_slots=0,formal_evidence_schema_admitted=False)
 try:
  assert json.loads((S/'COMPLETION.json').read_text())['passed']and json.loads((S/'POST_COMPONENT_STORAGE_BARRIER.json').read_text())['passed']
  reader=load('closed_component_source_reader',R/'experiments/v2090_svg_persistent_counter_fixture/context.py');source=reader.read(S/'SOURCE_FREEZE.json')['files'];freeze=sha(S/'SOURCE_FREEZE.json')
  class NoModels(importlib.abc.MetaPathFinder):
   def find_spec(self,name,*args):
    if name.split('.')[0]in {'mujoco','torch','jax','kernel','fast_predict','factory','vehicle','planner'}:raise AssertionError('COMPACT_EVIDENCE_NO_MODEL_IMPORT:'+name)
  sys.meta_path.insert(0,NoModels());import numpy as np
  codec=load('bounded_current_evidence_codec',C/'record.py');selected=reader.read(A/'SVG_SELECTED_SEGMENT.json');task=reader.read(S/'PILOT_TASK.json');run_id=task['run_id'];items=[];pins={}
  for p in [C/'record.py',C/'qualify_software.py',S/'SOURCE_FREEZE.json',A/'SVG_SELECTED_SEGMENT.json']:
   pins[str(p.relative_to(R))]=sha(p)
  for i in [0,1]:
   paths=[A/f'cycle_{i:04d}_origin.json',A/f'SVG_QUERY_{i}_FRAME.json',A/f'SVG_QUERY_{i}_RESULT.json',A/f'SVG_QUERY_{i}_PROPOSAL.json']
   for p in paths:pins[str(p.relative_to(R))]=sha(p)
   receipt=reader.read(paths[0])['receipt'];frame=reader.read(paths[1]);reply=reader.read(paths[2]);value=codec.pack(cycle=i,receipt=receipt,selected=selected,frame=frame,reply=reply,source_freeze_sha256=freeze)
   # A canonical JSON roundtrip deliberately discards insertion order. Rebuilt
   # wire bytes must still match the exact actual peer acknowledgement.
   packed=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode();value=json.loads(packed)
   items.append((value,frame,reader.read(paths[3]),len(packed),len(codec.wire_bytes(frame))))
   (O/f'compact_{i}.json').write_bytes(packed+b'\n')
  rebuilder=codec.Rebuilder(source,source_freeze_sha256=freeze,run_id=run_id)
  try:
   for value,original,proposal,_,_ in items:
    frame,checked=rebuilder.check(np,value,selected=selected,goal_xy=task['goal_xy']);assert frame==original and checked==proposal
  finally:rebuilder.close()
  negatives=[]
  def corrupt_receipt(value):
   receipt=json.loads(value['receipt_json']);receipt['packet']['body'][0]=999.;value['receipt_json']=json.dumps(receipt)
  for label,change in [('source_freeze',lambda v:v.update(source_freeze_sha256='0'*64)),('selected_route',lambda v:v.update(selected_segment_sha256='0'*64)),('origin_tick',lambda v:v.update(native_tick=5)),('receipt_packet',corrupt_receipt),('map_SHA',lambda v:v.update(maps_sha256='0'*64)),('transport_SHA',lambda v:v['reply']['transport_ack'].update(sha256='0'*64)),('foreign_reply',lambda v:v['reply']['raw'].update(run_id='foreign')),('invented_authority',lambda v:v.update(actual_execution_permitted=True)),('nonsequential',lambda v:v.update(cycle=1))]:
   bad=copy.deepcopy(items[0][0]);change(bad);check=codec.Rebuilder(source,source_freeze_sha256=freeze,run_id=run_id)
   try:
    try:check.check(np,bad,selected=selected,goal_xy=task['goal_xy'])
    except (AssertionError,KeyError,ValueError):negatives.append(label)
    else:raise AssertionError('COMPACT_BAD_RECORD_NOT_REFUSED:'+label)
    try:check.check(np,items[0][0],selected=selected,goal_xy=task['goal_xy'])
    except AssertionError:pass
    else:raise AssertionError('COMPACT_POISON_NOT_ENFORCED')
   finally:check.close()
  assert all(sha(R/n)==h for n,h in pins.items())
  result.update(software_passed=True,explicit_numpy_interpreter=__import__('sys').executable,ordered_receipt_JSON_string_preserves_original_nested_wire_order=True,saved_actual_frames=2,whole_frame_dict_equal=True,exact_actual_peer_byte_SHA_equal=True,canonical_record_roundtrip=True,
   original_full_frame_wire_bytes=sum(x[4]for x in items),compact_record_bytes=sum(x[3]for x in items),negative_cases=negatives,source_SHA256=pins,
   actual_models_and_safety_evidence_unchanged=True,old_full_frames_retained=True,per_case_all_evidence_224MiB_feasibility_not_proven=True,
   production_storage_schema_qualification_pending=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,unix=time.time());(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k]for k in ['closed','software_passed','models','physics','formal_evidence_schema_admitted']}));return 0 if result['software_passed']else 1
if __name__=='__main__':raise SystemExit(main())
