"""Pure current request checks, no numerical or model imports."""
import hashlib,json,math

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def decode(line,*,sequence,run_id,previous_native=-1):
 assert type(sequence)is int and 0<=sequence<12000,'SVG_PERSISTENT_QUERY_COUNT'
 assert isinstance(line,bytes)and len(line)<=1024**2 and line.endswith(b'\n'),'SVG_INPUT_BYTE_CAP'
 frame=json.loads(line)
 assert set(frame)=={'request','author_state','maps','source_receipt_sha256','maps_sha256','physical_authority'}and frame['physical_authority']is False
 request=frame['request'];maps=frame['maps']
 assert request['method']=='SVG-MPPI'and request['run_id']==run_id,'SVG_PERSISTENT_RUN_ID'
 assert type(request['native_tick'])is int and previous_native<request['native_tick']<=57600 and request['native_tick']%5==0 and (sequence!=0 or request['native_tick']==0),'SVG_PERSISTENT_CURRENT_CLOCK'
 assert abs(request['sim_time']-.01*request['native_tick'])<=1e-8,'SVG_PERSISTENT_SIM_CLOCK'
 assert frame['maps_sha256']==digest(maps)and maps['source_request_sha256']==digest(request),'SVG_PERSISTENT_MAP_BINDING'
 assert len(frame['author_state'])==5 and all(type(x)in[int,float]and math.isfinite(x)for x in frame['author_state'])
 assert maps['nx']==maps['ny']==100
 assert all(len(maps[k])==10000 and all(type(x)in[int,float]and math.isfinite(x)for x in maps[k])for k in ['collision_layer','distance_field','angle_field','speed_field'])
 return frame,dict(sequence=sequence,bytes=len(line),sha256=hashlib.sha256(line).hexdigest())

def verify_author_counts(values,*,attempts,returns,code):
 # Original bridge.cpp getter reports solve_attempts, solve_returns. Constructor
 # lifetime is independently recorded by this one persistent Python/native handle.
 assert type(attempts)is int and type(returns)is int and 1<=returns<=attempts<=12000
 assert values==[attempts,returns],'SVG_AUTHOR_ATTEMPT_RETURN_COUNTER_BINDING'
 assert code==0,'SVG_AUTHOR_SOLVE_RETURN_CODE'
 return dict(author_solve_attempts=values[0],author_solve_returns=values[1],native_solve_returncode=code)
