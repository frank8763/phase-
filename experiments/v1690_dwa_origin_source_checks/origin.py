"""Bind one actual packet to its acquisition and distinct bootstrap receipt.

No numerical imports, timestamp editing, state conversion, or model authority.
The bootstrap remains the original generic audit input. The current packet is
measured exactly once and passed verbatim to query, shadow and first admission.
"""
import copy,hashlib,json,math,time

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def validate_transition(bootstrap,current,before,after):
 assert math.isfinite(before)and math.isfinite(after)and before<=after,'ORIGIN_ACQUISITION_INTERVAL'
 a=copy.deepcopy(bootstrap);b=copy.deepcopy(current)
 assert a['native_tick']==b['native_tick']==a['steering']['native_tick']==b['steering']['native_tick']==0,'ORIGIN_NATIVE'
 assert a['sim_time']==b['sim_time']==0.,'ORIGIN_SIM_TIME'
 ta=[a.pop('body_measured_at'),a.pop('sent_at'),a['steering'].pop('measured_at')]
 tb=[b.pop('body_measured_at'),b.pop('sent_at'),b['steering'].pop('measured_at')]
 assert all(isinstance(x,(int,float))and math.isfinite(x)for x in ta+tb),'ORIGIN_CLOCK_FINITE'
 assert ta[0]==ta[1]==ta[2]and tb[0]==tb[1]==tb[2],'ORIGIN_SIMULTANEOUS_CHANNELS'
 assert ta[0]<=before<=tb[0]<=after,'ORIGIN_ACTUAL_MEASUREMENT_CLOCK'
 assert a==b,'ORIGIN_BOOTSTRAP_STATE_OR_MEMORY_CHANGED'
 return True

def verify_receipt(receipt,bootstrap):
 assert receipt['schema']=='SINGLE_MEASURED_ORIGIN_V1'and receipt['packet_acquisitions']==1,'ORIGIN_RECEIPT_SCHEMA'
 assert receipt['bootstrap_packet_sha256']==digest(bootstrap),'ORIGIN_BOOTSTRAP_SHA'
 current=receipt['packet'];assert receipt['packet_sha256']==digest(current),'ORIGIN_PACKET_SHA'
 validate_transition(bootstrap,current,receipt['acquisition_before_monotonic'],receipt['acquisition_after_monotonic'])
 return copy.deepcopy(current)

def acquire(vehicle,binding,bootstrap,save):
 before=time.monotonic();current=binding['packet'](vehicle);after=time.monotonic()
 receipt=dict(schema='SINGLE_MEASURED_ORIGIN_V1',packet_acquisitions=1,bootstrap_packet_sha256=digest(bootstrap),packet=copy.deepcopy(current),packet_sha256=digest(current),acquisition_before_monotonic=before,acquisition_after_monotonic=after)
 answer=verify_receipt(receipt,bootstrap)
 save('CURRENT_MEASURED_ORIGIN.json',receipt)
 return answer
