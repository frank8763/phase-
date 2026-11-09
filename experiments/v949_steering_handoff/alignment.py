"""Measured mechanical handoff gate; no simulation, commands or obstacle truth."""
import math


def ready(packet,now):
    if not math.isfinite(now):raise ValueError('NONFINITE_ALIGNMENT_TIME')
    if not 0<=now-packet['body_measured_at']<=.05:raise ValueError('STALE_ALIGNMENT_BODY')
    if max(abs(packet['body'][3]),abs(packet['body'][4]))>.03:return False
    steering=packet.get('steering')
    if steering is None:raise ValueError('MEASURED_STEERING_REQUIRED')
    position=steering['position'];velocity=steering['velocity']
    if len(position)!=2 or len(velocity)!=2 or not all(math.isfinite(x)for x in [*position,*velocity,steering['measured_at']]):
        raise ValueError('INVALID_STEERING_ENCODERS')
    if not 0<=now-steering['measured_at']<=.05:raise ValueError('STALE_STEERING_ENCODERS')
    if steering['native_tick']!=packet['native_tick']:raise ValueError('INCOHERENT_STEERING_ENCODERS')
    return max(abs(x)for x in position)<=.01 and max(abs(x)for x in velocity)<=.03
