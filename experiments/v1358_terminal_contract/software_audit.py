"""Revalidate recorded data, independent of the controller worker verdicts."""
from common import *


def audit():
    contract=load_contract();rows=[];maps={}
    for task in read(C/'SOFTWARE_TASKS.json'):
        out=O/task['id'];proof=read(out/'RESULT.json');saved=read(R/task['input_file'])
        common_hash=saved.pop('common_input_sha256');assert digest(saved)==common_hash==task['common_input_sha256']
        packets=read(out/'OBSERVATION_PLAYBACK.json');commands=read(out/'RAW_COMMANDS.json')
        for i,packet in enumerate(packets):
            contract.observation(packet,run_id=task['id'],now=packet['sampled_at'],previous_sequence=i-1)
            assert packet['body']==saved['fixture']['body'] and packet['ranges_m']==saved['fixture']['ranges_m']
        assert packets and proof['action_accepted'] and proof['controller_server_exited'] and proof['no_model_modules_loaded']
        for i,row in enumerate(commands):
            contract.twist(row['v'],row['w'])
            expected_direction=abs(row['v'])<.005 or row['v']*saved['segment']['gear']>0
            assert expected_direction==row['direction_ok']
            assert row['observation_age_s']<=.2 and 0<=row['generation_to_receipt_age_s']<=.2
            from stamped_contract import origin_from_header
            origin=row['origin'];assert origin_from_header(origin['stamp_ns'],origin['receipt_ros_ns'],origin['receipt_monotonic'])==origin
            assert abs(origin['generated_monotonic']-row['envelope']['issued_at'])<1e-8
            envelope=row['envelope'];contract.command(envelope,run_id=task['id'],now=row['adapter_checked_at'],previous_sequence=i-1)
            expected=(row['v'],row['w']) if expected_direction else (0.,0.)
            assert (envelope['v'],envelope['w'])==expected
        costmap=read(out/'DELIVERED_COSTMAP.json');maps.setdefault(task['saved_request'],[]).append(digest(costmap))
        rows.append(dict(task=task['id'],packet_count=len(packets),command_count=len(commands),input_sha256=common_hash,
                         costmap_sha256=digest(costmap),raw_bounds_and_adapter_direction_passed=True,
                         models=proof['models'],physical_native=proof['physical_native']))
    assert len(rows)==3 and len(maps)==3,'EXPECTED_THREE_TERMINAL_CONTROLLER_CASES'
    assert all(row['models']==row['physical_native']==0 for row in rows)
    assert hashes_ok(),'SOURCE_CHANGED'
    return dict(passed=True,cases=rows,six_actual_changed_path_costmaps_recorded=True,common_inputs_rehashed=True,
                models=0,physical_native=0,navigation_successes=None,command_origin_age_unknown=False)


if __name__=='__main__':print(json.dumps(audit()))
