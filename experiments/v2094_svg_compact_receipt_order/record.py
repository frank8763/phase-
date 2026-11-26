"""Saved-input evidence codec only; no command, model or runtime authority."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
INTERFACE=R/'experiments/v2054_svg_current_control_contract/interface.py'
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def wire_bytes(value):return json.dumps(value,allow_nan=False).encode()+b'\n'
def pack(*,cycle,receipt,selected,frame,reply,source_freeze_sha256):
 assert type(cycle)is int and 0<=cycle<12000 and reply['passed']
 assert frame['physical_authority']is False and receipt['packet_sha256']==frame['source_receipt_sha256']
 raw=wire_bytes(frame);ack=dict(sequence=cycle,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());assert reply['transport_ack']==ack
 value=dict(schema='SVG_COMPACT_CURRENT_EVIDENCE_SOFTWARE_V1',cycle=cycle,run_id=frame['request']['run_id'],native_tick=frame['request']['native_tick'],source_freeze_sha256=source_freeze_sha256,
  source_receipt_sha256=receipt['packet_sha256'],selected_segment_sha256=digest(selected),receipt_json=json.dumps(receipt,separators=(',',':'),allow_nan=False),frame_sha256=digest(frame),maps_sha256=frame['maps_sha256'],reply=reply,
  actual_execution_permitted=False,formal_runtime_admitted=False)
 assert len(wire_bytes(value))<=8192,'SVG_COMPACT_RECORD8KIB_CAP'
 return value

class Rebuilder:
 def __init__(self,source,*,source_freeze_sha256,run_id):
  assert source[str(INTERFACE.relative_to(R))]==hashlib.sha256(INTERFACE.read_bytes()).hexdigest()
  spec=importlib.util.spec_from_file_location('exact_original_current_evidence_interface',INTERFACE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  self.control=m.CurrentControl(source,run_id=run_id);self.freeze=source_freeze_sha256;self.run_id=run_id;self.cycle=0;self.poisoned=False
 def check(self,np,value,*,selected,goal_xy):
  assert not self.poisoned;self.poisoned=True
  assert value['schema']=='SVG_COMPACT_CURRENT_EVIDENCE_SOFTWARE_V1'and value['cycle']==self.cycle and value['run_id']==self.run_id and value['source_freeze_sha256']==self.freeze
  assert value['actual_execution_permitted']is False and value['formal_runtime_admitted']is False
  assert value['selected_segment_sha256']==digest(selected)
  receipt=json.loads(value['receipt_json']);assert receipt['packet_sha256']==value['source_receipt_sha256']and receipt['packet']['native_tick']==value['native_tick']
  frame=self.control.frame(np,receipt,goal_xy=goal_xy,rear_path=selected['poses'],gear=selected['gear'])
  assert digest(frame)==value['frame_sha256']and frame['maps_sha256']==value['maps_sha256'],'SVG_REBUILT_CURRENT_MAP_OR_FRAME_DIGEST'
  line=wire_bytes(frame);assert value['reply']['transport_ack']==dict(sequence=self.cycle,bytes=len(line),sha256=hashlib.sha256(line).hexdigest()),'SVG_REBUILT_TRANSPORT_BYTES'
  checked=self.control.proposal(value['reply']['raw'],now=100.)
  assert checked['physical_authority']is False and checked['actual_execution_permitted']is False
  self.cycle+=1;self.poisoned=False
  return frame,checked
 def close(self):self.poisoned=True;self.control.close()
