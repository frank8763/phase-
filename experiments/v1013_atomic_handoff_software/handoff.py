"""Keep completed-profile STOP ownership until a fresh zero tube is accepted."""
import time
from command_tube import admit
from steering_continuity import stopped_ready

def release_with_zero(node,pid,goal_until,tick,require,clock=time):
    require(node.profile_owner,'HANDOFF_WITHOUT_PROFILE_OWNER')
    until=min(goal_until,clock.monotonic()+.5)
    while True:
        tick();packet,source=node.motion.decision_snapshot();now=clock.monotonic()
        require(now<until,'HANDOFF_FRESH_ZERO_TIMEOUT')
        if not stopped_ready(packet,now)or not 0<=now-packet['body_measured_at']<=.05:continue
        try:proof=admit(packet,source,0.,0.,node.planner_proxy.known,now)
        except AssertionError as error:
            if str(error)in ['STALE_COMMAND_BODY','STALE_COMMAND_SCAN']:continue
            raise
        if not proof['passed']:continue
        shaping=node.steering_continuity.preview(packet,0.,0.,now)
        require(shaping['selected']==[0.,0.],'HANDOFF_NOT_ZERO')
        if clock.monotonic()-now>.04:continue
        sequence=node.command_sequence+1
        command=dict(kind='command',run_id=packet['run_id'],sequence=sequence,issued_at=now,v=0.,w=0.,tube=proof)
        node.tube_decisions.append(dict(packet=packet,source=source,raw_wanted=[0.,0.],wanted=[0.,0.],
            nominal_shaping=shaping,selected_shaping=shaping,proof=proof,wait_renewal=False,last_nominal_at=node.last_nominal_at,
            retained_previous=False,retained_anchor_tick=None,recovery=None,handoff_stop=True,profile_id=pid))
        node.send(dict(kind='release_profile',issued_at=now,profile_id=pid,resume_command=command))
        ack_until=min(goal_until,clock.monotonic()+1.)
        while True:
            status=node.latest.get('profile_status',{})
            if status.get('released_id')==pid and status.get('handoff_sequence')==sequence:break
            tick();require(clock.monotonic()<ack_until,'HANDOFF_ZERO_ACK_MISSING')
        node.retained_proof=proof;node.command_sequence=sequence;node.commands.append([now,0.,0.]);node.steering_continuity.commit(shaping)
        # Changing this order recreates V1009: an unprotected normal callback
        # must never run between releasing the profile and installing the proof.
        node.profile_owner=False
        return dict(profile_id=pid,sequence=sequence,body_native_tick=packet['native_tick'],source_native_tick=source['source_native_tick'],
            issued_at=now,ack_at=clock.monotonic(),zero_tube=proof,stop_ownership_until_ack=True)
