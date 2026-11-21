"""Actual route RPC identity first, then bounded stale retirement; no models."""
from collections import deque
import hashlib
import json
import copy
import math
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2]


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


frames=exact('v1411_original_actual_wire',R/'experiments/v1396_rpp_rpc_retirement/frames.py')
stamped=exact('v1411_original_stamp_decode',R/'experiments/v1396_rpp_rpc_retirement/stamped_contract.py')
contract=exact('v1411_original_twist_boundary',R/'experiments/v1288_baseline_interface/contract.py')
PLUGIN_SOURCES={'CONTROLLER','ENGINEERING_COHERENT_MPPI_WITH_SHARED_BRIDGE'}
ZERO_SOURCES={'CAUSAL_BRAKE_HOLD','CAUSAL_BRAKE_TIMER','EXPIRED_SOURCE_ZERO'}


class Commands:
    def __init__(self,run_id,*,controller_identity_sha256,retirement_sink):
        assert callable(retirement_sink),'ROUTE_RETIREMENT_DURABLE_SINK_REQUIRED'
        assert isinstance(controller_identity_sha256,str)and len(controller_identity_sha256)==64 and set(controller_identity_sha256)<=set('0123456789abcdef'),'MPPI_CONTROLLER_DIGEST'
        self.controller_identity_sha256=controller_identity_sha256
        self.run_id=run_id;self.previous=-1;self.retired=deque(maxlen=256);self.accepted=[]
        self.retirement_sink=retirement_sink;self.retired_total=0;self.retirement_chain='0'*64

    def accept(self,value,sent,*,current_native,now):
        p=copy.deepcopy(value)
        assert p['kind']=='command' and p['run_id']==self.run_id
        assert p['controller_identity_sha256']==self.controller_identity_sha256,'ACTUAL_MPPI_COMMAND_CONTROLLER_CHANGED'
        assert type(p['sequence']) is int and p['sequence']>=0
        assert p['command_source'] in PLUGIN_SOURCES|ZERO_SOURCES
        frames.validate_binding(p,sent);wire=sent[p['observation_sequence']]
        assert wire['native_tick']<=current_native,'ROUTE_REPLY_FROM_FUTURE_NATIVE'
        contract.twist(p['v'],p['w'])
        origin=p['origin']
        if p['command_source'] in PLUGIN_SOURCES:
            assert origin['kind']=='NAV2_STAMPED'
            assert stamped.decode_origin(origin['stamp_ns'],origin['receipt_ros_ns'],origin['receipt_monotonic'])==origin,'ROUTE_SOURCE_ORIGIN_CHANGED'
        else:
            assert p['v']==p['w']==0. and origin['kind']=='LOCAL_ZERO','LOCAL_ROUTE_NONZERO'
        ages=[now-origin['generated_monotonic'],now-p['observation_sampled_at'],now-p['issued_at']]
        assert all(math.isfinite(x)for x in ages)and min(ages)>=0.,'ROUTE_SOURCE_FROM_FUTURE_OR_NONFINITE'
        reason=('SUPERSEDED_ACTUAL_STATE' if wire['native_tick']<current_native else
                'ALREADY_CONSUMED_SEQUENCE' if p['sequence']<=self.previous else
                'EXPIRED_SOURCE' if max(ages)>.2 else None)
        if reason:
            row=dict(packet=p,reason=reason,current_native=current_native,checked_monotonic=now)
            raw=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            digest=hashlib.sha256(bytes.fromhex(self.retirement_chain)+raw).hexdigest()
            receipt=dict(retired_count=self.retired_total+1,previous_chain_sha256=self.retirement_chain,chain_sha256=digest,row=row)
            # Original owner journal flush + quota complete before committing
            # retirement bookkeeping. No stale request is ever returned.
            self.retirement_sink(copy.deepcopy(receipt))
            self.retired.append(row);self.retired_total+=1;self.retirement_chain=digest
            return None
        self.previous=p['sequence'];self.accepted.append(p)
        delivery=dict(source_kind='ACTUAL_FRAME',run_id=self.run_id,origin=origin,observation_sequence=p['observation_sequence'],
                      observation_native_tick=p['observation_native_tick'],observation_sampled_at=p['observation_sampled_at'],
                      command_sequence=p['sequence'],command_source=p['command_source'],controller_identity_sha256=self.controller_identity_sha256,validated_monotonic=now)
        return dict(v=p['v'],w=p['w'],delivery=delivery,control_owner='ENGINEERING_COHERENT_MPPI' if p['command_source'] in PLUGIN_SOURCES else 'DISCLOSED_SHARED_EXECUTION_BRIDGE')
