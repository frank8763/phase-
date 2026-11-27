"""Acyclic immutable admission -> frame -> once-claim data binding."""
import json,hashlib,copy

def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def bind(admission_bytes,frame):
 a=json.loads(admission_bytes);assert a['scope']=='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY'and a['maximum_queries']==1 and a['models_authorized']is False
 assert 'first_input_sha256'not in a,'NO_ADMISSION_FRAME_HASH_CYCLE'
 f=copy.deepcopy(frame);assert f['episode_id']==a['run_id']and f['query_nonce']==a['query_nonce']and f['source_freeze_sha256']==a['source_freeze_sha256']and f['query_sequence']==0,'FRESH_QUERY_AUTHORITY_BINDING'
 f['numerical_admission_sha256']=sha(admission_bytes)
 claim=dict(admission_sha256=sha(admission_bytes),first_input_sha256=digest(f),query_nonce=a['query_nonce'],maximum_queries=1,claimed_before_spawn=True,models=0)
 return f,claim

def verify(admission_bytes,claim,frame):
 a=json.loads(admission_bytes);assert 'first_input_sha256'not in a and a['scope']=='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY'and a['models_authorized']is False and a['maximum_queries']==1
 assert claim['admission_sha256']==frame['numerical_admission_sha256']==sha(admission_bytes)and claim['first_input_sha256']==digest(frame),'ADMISSION_QUERY_ONCE_SHA'
 assert frame['query_nonce']==claim['query_nonce']==a['query_nonce']and frame['episode_id']==a['run_id']and frame['source_freeze_sha256']==a['source_freeze_sha256']and claim['maximum_queries']==1 and frame['query_sequence']==0,'FOREIGN_QUERY_OR_ONCE'
 return True
