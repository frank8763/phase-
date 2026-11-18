"""Expected functional ROS rejection must drain native stop/save/replay."""
import json


def peer_exit_policy(returncodes, output):
    ros, native = returncodes
    if native is not None and native != 0:
        path = output / 'RESULT.json'
        if path.exists():
            result = json.loads(path.read_text())
            if result.get('evidence_saved') and not result.get('error') and result.get('replay', {}).get('passed'):
                return 'DRAIN'
        return 'ABORT'
    if ros is not None and ros != 0:
        path = output / 'ROS_RESULT.json'
        if ros == 1 and path.exists():
            result = json.loads(path.read_text())
            if (not result.get('error') and result.get('action_status') == 6
                    and result.get('error_code') == 104
                    and result.get('public_static_map_receipt', {}).get('passed')):
                return 'DRAIN'
        return 'ABORT'
    return 'WAIT'
