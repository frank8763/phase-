"""Actual production ROS component with explicitly synthetic stationary peer."""
import importlib.util
import json
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def main():
    taskfile=Path(sys.argv[1]);folder=taskfile.parent
    spec=importlib.util.spec_from_file_location('phase_production_ros_close',C/'ros_component.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    task=json.loads(taskfile.read_text());window=json.loads((folder/'ROUND_WINDOW.json').read_text())
    def software_authority(actual,actual_window):
        assert actual==task and actual_window==window
        assert actual['scope']=='SOFTWARE_ONLY_STATIONARY_PEER_NO_MODELS' and actual['dynamic'] is False
        assert Path(actual['output'])==folder
    # Only the no-model ROS-side fixture uses this data-only local authority.
    # All real physical CLI entry checks still use the frozen production ledger.
    module.O=folder;module.authorize=software_authority
    result=module.main()
    assert not any(name in sys.modules for name in ['mujoco','vehicle','torch'])
    return result


if __name__=='__main__':raise SystemExit(main())
