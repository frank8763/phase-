"""Command origin and expiry checks; no ROS/model dependencies."""
import math


def origin_from_header(stamp_ns, ros_now_ns, received_monotonic):
    assert type(stamp_ns) is int and type(ros_now_ns) is int and stamp_ns > 0, 'MISSING_SOURCE_STAMP'
    age=(ros_now_ns-stamp_ns)*1e-9
    assert math.isfinite(age) and 0. <= age <= .2, 'SOURCE_COMMAND_EXPIRED_OR_FUTURE'
    return dict(kind='NAV2_STAMPED',stamp_ns=stamp_ns,receipt_ros_ns=ros_now_ns,
                receipt_monotonic=received_monotonic,generated_monotonic=received_monotonic-age,
                receipt_age_s=age)


def local_zero(now):
    return dict(kind='LOCAL_ZERO',generated_monotonic=now)


def validate_delivery(packet, now):
    origin=packet['origin']
    assert origin['kind'] in ['NAV2_STAMPED','LOCAL_ZERO'], 'UNKNOWN_ORIGIN'
    if origin['kind']=='LOCAL_ZERO':assert packet['v']==packet['w']==0., 'LOCAL_ORIGIN_NONZERO'
    else:
        rebuilt=origin_from_header(origin['stamp_ns'],origin['receipt_ros_ns'],origin['receipt_monotonic'])
        assert rebuilt==origin, 'ORIGIN_METADATA_CHANGED'
    assert 0 <= now-origin['generated_monotonic'] <= .2, 'SOURCE_EXPIRED_BEFORE_NATIVE_RECEIPT'
    assert type(packet['observation_sequence']) is int and packet['observation_sequence']>=0
    assert type(packet['observation_native_tick']) is int and packet['observation_native_tick']>=0
    assert 0 <= now-packet['observation_sampled_at'] <= .2, 'OBSERVATION_EXPIRED_AT_DELIVERY'
    return dict(origin=origin,validated_monotonic=now,observation_sequence=packet['observation_sequence'],
                observation_native_tick=packet['observation_native_tick'],observation_sampled_at=packet['observation_sampled_at'])


def before_step(v,w,delivery,now):
    assert delivery is not None, 'MISSING_NATIVE_DELIVERY_BINDING'
    age=now-delivery['origin']['generated_monotonic']
    assert math.isfinite(age) and age>=0., 'NATIVE_CLOCK_OR_ORIGIN_FUTURE'
    fresh=age<=.2 and now-delivery['observation_sampled_at']<=.2
    return (v if fresh else 0.),(w if fresh else 0.),dict(fresh=fresh,source_age_s=age,applied_monotonic=now,
             reason='FRESH' if fresh else 'EXPIRED_COMMAND_ZEROED')
