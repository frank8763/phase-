"""No numerical imports: exact ordered request, digest and causal-clock binding."""
import hashlib,json
from context import digest
MAX_QUERIES=20

def decode(raw,sequence,method,run_id):
 assert type(sequence)is int and 0<=sequence<MAX_QUERIES
 assert len(raw)<=1024**2 and raw.endswith(b'\n'),'FILTER_FRAME_BYTE_LIMIT'
 frame=json.loads(raw);current=frame['current'];request=frame['request'];k=5*sequence
 assert current['method']==request['method']==method and current['run_id']==request['run_id']==run_id,'FILTER_FRAME_FOREIGN_IDENTITY'
 assert current['native']==request['origin_native']==k and abs(current['sim_time']-.01*k)<=1e-8 and abs(request['origin_sim_time']-.01*k)<=1e-8,'FILTER_FRAME_STALE_OR_FUTURE'
 for z,key in[(current,'input_sha256'),(request,'request_sha256')]:
  clean=dict(z);h=clean.pop(key);assert digest(clean)==h,'FILTER_FRAME_DIGEST'
 assert request['input_sha256']==current['input_sha256'] and request['case']['pose']==current['pose']and request['case']['nominal']==current['nominal_twist'] and request['case']['gear']==current['gear']and request['case']['causal']==current['causal']and request['case']['sim_time']==request['origin_sim_time']==current['sim_time']
 assert not current['physical_authority']and not request['physical_authority']and request['model_identity']=='EXPLICIT_IDEAL_KINEMATIC_ONLY'
 assert request['public_known']==current['public_known']and digest(request['public_known'])==current['public_known_sha256']
 return frame,dict(sequence=sequence,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
