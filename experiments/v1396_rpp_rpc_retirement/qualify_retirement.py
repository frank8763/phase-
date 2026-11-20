"""Replay the actual delayed reply and reject source/body/time tampering."""
import copy
import json
from pathlib import Path
from reply_contract import assess
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def main():
    raw=R/'runs/v858_nav2_verified/v1395/full9390_main';wires={x['sequence']:x for x in json.loads((raw/'OBSERVATIONS_SENT.json').read_text())};commands=json.loads((raw/'ORIGINAL_RPP_COMMANDS.json').read_text());by_seq={x['sequence']:x for x in commands};run_id=by_seq[41]['run_id']
    prior=assess(by_seq[40],wires[40],run_id=run_id,current_native=10910,previous_accepted=32,now=by_seq[40]['reply_monotonic']);assert prior['accepted']
    old=assess(by_seq[41],wires[41],run_id=run_id,current_native=10915,previous_accepted=40,now=by_seq[41]['reply_monotonic']);assert not old['accepted'] and old['reason']=='SUPERSEDED_ACTUAL_STATE'
    fresh=assess(by_seq[42],wires[42],run_id=run_id,current_native=10915,previous_accepted=40,now=by_seq[42]['reply_monotonic']);assert fresh['accepted']
    retired=[];rejected=[]
    for name,wire,previous,now in [('expired_generation',copy.deepcopy(wires[42]),40,by_seq[42]['origin']['generated_monotonic']+.21),('already_consumed',copy.deepcopy(wires[42]),42,by_seq[42]['reply_monotonic'])]:
        reply=copy.deepcopy(by_seq[42])
        if name=='expired_generation':wire['sampled_at']=now-.01;reply['observation_sampled_at']=wire['sampled_at']
        proof=assess(reply,wire,run_id=run_id,current_native=10915,previous_accepted=previous,now=now);assert not proof['accepted'];retired.append(proof['reason'])
    for name,mutate in [('foreign_run',lambda x:x.update(run_id='foreign')),('changed_body',lambda x:x['body'].__setitem__(0,99.)),('changed_tick',lambda x:x.update(native_tick=10916)),('changed_acquisition',lambda x:x.update(observation_sampled_at=x['observation_sampled_at']+.001)),('unknown_sequence',lambda x:x.update(sequence=999)),('future_generation',lambda x:x['origin'].update(generated_monotonic=by_seq[42]['reply_monotonic']+1.))]:
        reply=copy.deepcopy(by_seq[42]);mutate(reply)
        try:assess(reply,wires[42],run_id=run_id,current_native=10915,previous_accepted=40,now=by_seq[42]['reply_monotonic'])
        except AssertionError:rejected.append(name)
        else:raise AssertionError('BAD_REPLY_ACCEPTED '+name)
    journal=json.loads((raw/'APPLIED_JOURNAL.json').read_text());assert len(journal)==11115 and all(row['applied'] and row['request']==[0.,0.,False] and row['phase']=='ERROR_STOP_TAIL' for row in journal[-200:])
    assert all('response_membership' not in row for row in journal[-200:]) and all('response_membership' in row for row in journal[10775:10915])
    proof=dict(passed=True,actual_saved_sequence40_accept41_retire42_accept=True,retired_replies_never_applied=True,retired_reasons=retired,source_tampering_negative_cases=rejected,old_error_tail_metadata_200_actions_verified=True,old_complete_model_audit_still_not_claimed=True,old_failure_preserved=True,models=0,analytical_native=0,physical_native=0)
    target=O/'RPC_RETIREMENT_QUALIFICATION.json';assert not target.exists();target.write_text(json.dumps(proof,indent=2)+'\n');assert json.loads(target.read_text())==proof;print(json.dumps(proof))
if __name__=='__main__':main()
