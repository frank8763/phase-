"""Strict 200ms command/observation validity with explicit safe expiry refusal."""
import importlib.util
import math
from pathlib import Path

R=Path(__file__).resolve().parents[2]
_s=importlib.util.spec_from_file_location('phase_unchanged_command_contract',R/'experiments/v1288_baseline_interface/contract.py')
_contract=importlib.util.module_from_spec(_s);_s.loader.exec_module(_contract)


def decode_origin(stamp_ns,ros_now_ns,received_monotonic):
    assert type(stamp_ns) is int and type(ros_now_ns) is int and stamp_ns>0,'MISSING_SOURCE_STAMP'
    age=(ros_now_ns-stamp_ns)*1e-9
    assert math.isfinite(age) and age>=0. and math.isfinite(received_monotonic),'SOURCE_COMMAND_FUTURE_OR_NONFINITE'
    return dict(kind='NAV2_STAMPED',stamp_ns=stamp_ns,receipt_ros_ns=ros_now_ns,
        receipt_monotonic=received_monotonic,generated_monotonic=received_monotonic-age,receipt_age_s=age)


def origin_from_header(stamp_ns,ros_now_ns,received_monotonic):
    result=decode_origin(stamp_ns,ros_now_ns,received_monotonic)
    assert result['receipt_age_s']<=.2,'SOURCE_COMMAND_EXPIRED_OR_FUTURE'
    return result


def local_zero(now):return dict(kind='LOCAL_ZERO',generated_monotonic=now)


def assess_delivery(packet,now,*,run_id,previous_sequence):
    assert packet['run_id']==run_id,'FOREIGN_COMMAND'
    assert type(packet['sequence']) is int and packet['sequence']>previous_sequence,'FOREIGN_OR_REPLAYED_COMMAND'
    _contract.twist(packet['v'],packet['w'])
    origin=packet['origin'];assert origin['kind'] in ['NAV2_STAMPED','LOCAL_ZERO'],'UNKNOWN_ORIGIN'
    if origin['kind']=='LOCAL_ZERO':assert packet['v']==packet['w']==0.,'LOCAL_ORIGIN_NONZERO'
    else:
        rebuilt=decode_origin(origin['stamp_ns'],origin['receipt_ros_ns'],origin['receipt_monotonic'])
        assert rebuilt==origin,'ORIGIN_METADATA_CHANGED'
    assert type(packet['observation_sequence']) is int and packet['observation_sequence']>=0
    assert type(packet['observation_native_tick']) is int and packet['observation_native_tick']>=0
    values=[now,origin['generated_monotonic'],packet['issued_at'],packet['observation_sampled_at']]
    assert all(type(v) in [float,int] and math.isfinite(v) for v in values),'NONFINITE_CLOCK'
    source_age=now-origin['generated_monotonic'];observation_age=now-packet['observation_sampled_at'];envelope_age=now-packet['issued_at']
    assert min(source_age,observation_age,envelope_age)>=0.,'FUTURE_ORIGIN_OBSERVATION_OR_ENVELOPE'
    reason='SOURCE_EXPIRED' if source_age>.2 else 'OBSERVATION_EXPIRED' if observation_age>.2 else 'ENVELOPE_EXPIRED' if envelope_age>.2 else None
    return dict(accepted=reason is None,reason=reason,source_age_s=source_age,
        observation_age_s=observation_age,envelope_age_s=envelope_age,receipt_monotonic=now)


def validate_delivery(packet,now):
    decision=assess_delivery(packet,now,run_id=packet['run_id'],previous_sequence=packet['sequence']-1)
    assert decision['accepted'],decision['reason']
    return dict(origin=packet['origin'],validated_monotonic=now,observation_sequence=packet['observation_sequence'],
        observation_native_tick=packet['observation_native_tick'],observation_sampled_at=packet['observation_sampled_at'])


def before_step(v,w,delivery,now):
    assert delivery is not None,'MISSING_NATIVE_DELIVERY_BINDING'
    age=now-delivery['origin']['generated_monotonic']
    assert math.isfinite(age) and age>=0.,'NATIVE_CLOCK_OR_ORIGIN_FUTURE'
    fresh=age<=.2 and now-delivery['observation_sampled_at']<=.2
    return (v if fresh else 0.),(w if fresh else 0.),dict(fresh=fresh,source_age_s=age,applied_monotonic=now,
        reason='FRESH' if fresh else 'EXPIRED_COMMAND_ZEROED')
