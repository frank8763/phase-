"""One fixed-policy timing proposal, no alternatives or endpoint tuning.

Carrier/Guard/sink are separately admitted production objects. This module
does not create or authorize them. Preserve every raw and filtered request.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def run(carrier,tracker,*,guard,save_block,save_partial,save_result):
    guard.require_nominal_proposal_once()
    native=carrier.native;start=native;blocks=[];first=None;secondary=[];stopping=False;zero_applied=0
    block=[];block_save_attempted=False
    try:
        while carrier.native-start<6000:
            guard.check();before=carrier.snapshot();state=before['state']
            body=[float(state[i])for i in (0,1,2,3,5)]
            decision=tracker.select(body,native_tick=before['native'],sim_time=before['sim_time'])
            block=[];block_save_attempted=False
            for _ in range(5):
                guard.check();row=carrier.advance(tuple(decision['raw_row']));block.append(row)
            # Durable raw/filtered/model state-control receipts precede cursor
            # publication or policy success. No expected state is a model input.
            block_save_attempted=True;identity=save_block(decision,block)
            tracker.commit(decision,applied_native=5,applied_request_receipts_sha256=identity)
            blocks.append(dict(start_native=decision['before_native'],raw_row=decision['raw_row'],receipt_sha256=identity))
            block=[]
            if decision['terminal_requested']:
                stopping=True;zero_applied=5;break
        assert stopping,'FIXED_SEGMENT_POLICY_MOTION_CAP_REACHED'
        while zero_applied<2200:
            block=[];block_save_attempted=False
            for _ in range(min(5,2200-zero_applied)):
                guard.check();block.append(carrier.advance((0.,0.,0)));zero_applied+=1
            decision=dict(kind='ORIGINAL_FINAL2200_ZERO_TAIL',before_native=block[0]['before']['native'])
            block_save_attempted=True;identity=save_block(decision,block)
            blocks.append(dict(start_native=decision['before_native'],raw_row=[0.,0.,0],receipt_sha256=identity))
            block=[]
        end=carrier.snapshot();s=end['state'];target=tracker.poses[-1]
        import math
        rear=[float(s[0])-.3*math.cos(float(s[2])),float(s[1])-.3*math.sin(float(s[2])),float(s[2])]
        distance=math.dist(rear[:2],target[:2]);yaw=abs(math.atan2(math.sin(rear[2]-target[2]),math.cos(rear[2]-target[2])))
        assert distance<=.12+1e-8 and yaw<=.20+1e-8,'ORIGINAL_SEGMENT_ENDPOINT_NOT_REACHED'
        nominal_native=carrier.native-start
        assert 2200<=nominal_native<=8200 and nominal_native%5==0
        # Timing is fixed once. Subsequent generation/audit recomputes policy
        # from each branch's OWN state with the fixed stop offset, never uses
        # these numerical output arrays as per-step state resets.
        answer=dict(passed=True,closed=True,origin_native=start,nominal_native=nominal_native,
            motion_native=nominal_native-2200,final_zero_tail_native=2200,
            feedback_native=5,endpoint_rear_error_m=distance,endpoint_heading_error_rad=yaw,
            segment_sha256=tracker.segment_sha256,block_receipts=blocks,
            no_parameter_search=True,complete_witnesses_still_required=True,
            physical_permission=False,whole_route_passed=False)
        save_result(answer)
        return answer
    except BaseException as error:
        first=repr(error)
        answer=dict(passed=False,closed=True,first_error=first,secondary_errors=secondary,
            completed_native=carrier.native-start,model_counts=guard.counts(),
            durable_block_receipts=blocks,physical_permission=False,whole_route_passed=False)
        if block and not block_save_attempted:
            try:save_partial(block,first_error=first,model_counts=guard.counts())
            except BaseException as saving:secondary.append('nominal_partial_save:'+repr(saving))
        elif block:
            secondary.append('nominal_block_save_failed_not_retried')
        try:save_result(answer)
        except BaseException as saving:error.secondary_proposal_save=repr(saving)
        raise
