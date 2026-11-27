"""Production ordered frame decoder negatives, no solver/model imports."""
import json,copy
from context import R,C,SOURCE as S,load,put,digest
from peer_contract import decode

def main():
 frame=load('production_reader',C/'context.py').read(S/'software/PCBF/FILTER_QUERY_000_WIRE.json');frame=json.loads(frame['text']);raw=lambda z:json.dumps(z,allow_nan=False).encode()+b'\n'
 f,a=decode(raw(frame),0,'PCBF',frame['current']['run_id']);assert f==frame
 rejected=[]
 def reject(label,fn):
  try:fn()
  except(AssertionError,ValueError,KeyError):rejected.append(label)
  else:raise AssertionError('FRAME_NEGATIVE_ACCEPTED:'+label)
 reject('duplicate_current_at_next_sequence',lambda:decode(raw(frame),1,'PCBF',frame['current']['run_id']))
 reject('foreign_method',lambda:decode(raw(frame),0,'PSF',frame['current']['run_id']))
 reject('foreign_run_id',lambda:decode(raw(frame),0,'PCBF','foreign'))
 bad=copy.deepcopy(frame);bad['request']['case']['pose'][0]+=.01
 reject('modified_request_digest',lambda:decode(raw(bad),0,'PCBF',frame['current']['run_id']))
 reject('frame_count_cap',lambda:decode(raw(frame),20,'PCBF',frame['current']['run_id']))
 reject('non_newline_frame',lambda:decode(raw(frame)[:-1],0,'PCBF',frame['current']['run_id']))
 ch=load('original_frame_channel_guard',C/'channel.py').FrameChannel(maximum_frames=1)
 try:
  pending=ch.send(dict(explicit_software_fixture=True));reject('send_while_inflight',lambda:ch.send({}));reject('foreign_wire_ack',lambda:ch.acknowledge(dict(pending,sha256='0'*64)));ch.acknowledge(pending);reject('send_beyond_count',lambda:ch.send({}));reject('send_after_poison',lambda:ch.send({}))
 finally:ch.close()
 value=dict(passed=True,negative_cases=rejected,models=0,optimizer_queries=0,physical_native=0,production_decoder_and_channel=True);put(S/'PERSISTENT_PROTOCOL_PROOF.json',value);print(json.dumps(value))
if __name__=='__main__':main()
