"""Real installed ROS result red/green regression, no controller or vehicle."""
from common import *
from nav2_msgs.action import FollowPath


def main():
    result = FollowPath.Result()
    fields = {key: getattr(result, key) for key in result.get_fields_and_field_types()}
    old_error = None
    try:json.dumps(fields, allow_nan=False)
    except TypeError as exc:old_error = str(exc)
    assert old_error and 'Empty' in old_error, 'ORIGINAL_EMPTY_MESSAGE_ERROR_NOT_REPRODUCED'
    converted = plain(fields)
    assert json.loads(json.dumps(converted, allow_nan=False)) == converted
    for value in [object(), {'unknown': object()}]:
        try:plain(value)
        except TypeError:pass
        else:raise AssertionError('UNSUPPORTED_OBJECT_NOT_REJECTED')
    proof = dict(passed=True, original_error=old_error, real_ros_result_fields=converted,
                 empty_ros_message_roundtrip=True, unsupported_object_negatives=2, models=0, physical_native=0)
    dump(O/'MESSAGE_QUALIFICATION.json', proof)
    print(json.dumps(proof))


if __name__=='__main__':main()
