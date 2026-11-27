"""Bind fixed existing raw outputs and measured origin; no new sensor/plant."""
import gzip,hashlib,json,math,struct
from context import R,PARENT,read,sha
RECEIPT='runs/v1978_rpp_first_common_round/actual/cycle_0000_origin.json'
SETUP='runs/v1978_rpp_first_common_round/actual/physics/SETUP.json'
EVIDENCE='runs/v2184_fair_raw_controller_math/RUNTIME/EVIDENCE.json.gz'
RESULT='runs/v2184_fair_raw_controller_math/RUNTIME/RESULT.json'
CLOSURE='runs/v2184_fair_raw_controller_math/RUNTIME_REMOTE_CLOSURE.json'

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def fixed(source):
    for n in [RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE]:assert source[n]==sha(R/n),'FIXED_RESPONSE_INPUT_CHANGED:'+n
    result=read(R/RESULT);closed=read(R/CLOSURE);assert result['passed']and closed['passed']and closed['scientific_result_sha256']==sha(R/RESULT)
    assert result['evidence_sha256']==sha(R/EVIDENCE)
    raw=gzip.decompress((R/EVIDENCE).read_bytes());assert len(raw)==result['evidence_raw_bytes']<=128*1024 and hashlib.sha256(raw).hexdigest()==result['evidence_raw_sha256']
    data=json.loads(raw);common=data['common_historical_input'];receipt=read(R/RECEIPT)['receipt'];p=receipt['packet']
    assert p['native_tick']==0 and p['sim_time']==0. and p['dynamic_discovered']is False
    assert common['body']==p['body']and common['source_packet_sha256']==receipt['packet_sha256']and common['historical_timestamps_preserved']is True
    assert receipt['packet_sha256']==digest(p)and p['controller_memory']==common['controller_memory']and receipt['scan']==common['scan']
    setup=read(R/SETUP);public={k:setup[k]for k in ['known','limits','slew_per_second']};assert len(public['limits'])==4 and len(public['slew_per_second'])==4
    assert set(public['known'])=={'known_rectangles','known_circles','source','source_sha256','bootstrap_seed','scope'},'UNDECLARED_PUBLIC_MAP_METADATA'
    cases=[]
    for i,method in enumerate(['DWA_SIGNED_GEAR_SHARED_PATH','RPP_RAW_ABI2']):
        row=data['methods'][i];assert row['method']==method and row['passed']and row['output_clipped_or_repaired']is False
        answer=row if i==0 else row['native_worker']['answer'];raw_twist=struct.unpack('<2d',bytes.fromhex(answer['raw_double_bytes_hex']))
        assert list(raw_twist)==answer['raw_twist']and all(math.isfinite(v)for v in raw_twist)
        assert row['common_input_sha256']==result['common_input_sha256']==digest(common)
        assert row['strict_common_request']==[*raw_twist,False]
        cases.append(dict(method=method,request=[*raw_twist,False],original_raw_double_hex=answer['raw_double_bytes_hex'],moving_requests=5,zero_requests=2200))
    return dict(packet=p,receipt=receipt,setup=public,goal_xy=common['actual_global_goal_xy'],causal_source=None,cases=cases,common_input_sha256=result['common_input_sha256'],historical_not_current_or_physical=True,world_truth_not_supplied=True)
