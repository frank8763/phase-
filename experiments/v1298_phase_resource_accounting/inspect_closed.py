"""Report Phase allocation and known closed task use, without reading other jobs."""
import datetime
import json
import os
from pathlib import Path
from stage_timer import measure_stage

R = Path(__file__).resolve().parents[2]
O = R / 'runs/v1298_phase_resource_accounting'


def main():
    rows = []
    with measure_stage('closed_phase_metadata_read', rows.append):
        current = json.loads((R / 'CURRENT_EXPERIMENT.json').read_text())
        completion = json.loads((R / 'runs/v1296_rpp_turn_brake/COMPLETION.json').read_text())
        main = completion['results'][0]['native']
        assert current['status'] == 'REVIEW_PENDING' and current['active_run'] is None and completion['closed']
        # Existence only for exact registered Phase PIDs. Never read cmdline,
        # memory or affinity of a PID which could have been reused by another job.
        launch = json.loads((R / 'runs/v1296_rpp_turn_brake/LAUNCH.json').read_text())
        workers = json.loads((R / 'runs/v1296_rpp_turn_brake/CLOSED_PROCESSES.json').read_text())
        ids = [launch['pid'], *workers['pids']]
        absent = [pid for pid in ids if not (Path('/proc') / str(pid)).exists()]
        assert len(absent) == len(ids), 'REGISTERED_PID_EXISTS_UTILIZATION_UNKNOWN_DO_NOT_INSPECT_OTHER_JOB'
        proof = dict(checked_local=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
                     scope='Phase experiment workers only, excludes assistant and all other research lines',
                     active_experiment=None, registered_phase_pids_absent=absent,
                     phase_experiment_current_cpu_percent=0., phase_experiment_current_gpu_percent=0.,
                     usage_basis='No active run; last registered Phase workers no longer exist; all experiment rendering was CPU and CUDA devices hidden.',
                     whole_machine_cpu_utilization=None, whole_machine_gpu_utilization=None,
                     other_processes_or_stage_resources_inspected=False,
                     configured_resources=dict(native_cpus=[2], ros_cpus=[3,4,5], maximum_assigned_cpu_threads=4,
                                               native_scheduler='SCHED_IDLE', native_nice=19, gpu_enabled=False,
                                               numeric_library_threads=1),
                     historical_exact_cpu_percent=None, historical_cpu_time_not_recorded=True,
                     last_task=dict(actual_native=main['new_actual_native'], own_replay_native=main['own_replay_native'],
                                    worker_wall_s=main['wall_s'], actual_simulation_s=main['new_actual_native']*.01,
                                    controller_wall_s=completion['results'][0]['ros']['wall_s'],
                                    wall_includes_initialization_navigation_stop_allocation_audit_and_replay=True),
                     frozen_experiment_sources_changed=False, new_models=0, new_physical_native=0)
    O.mkdir(exist_ok=True)
    (O / 'RESOURCE_SNAPSHOT.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2)+'\n')
    (O / 'ACCOUNTING_SMOKE.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(proof, ensure_ascii=False))


if __name__ == '__main__':
    main()
