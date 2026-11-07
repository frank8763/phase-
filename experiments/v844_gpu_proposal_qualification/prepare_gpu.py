"""Bounded GPU math/interface preparation; no physics or navigation."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback


class NoModels:
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('GPU_COMPONENT_NO_PHYSICS')


sys.meta_path.insert(0, NoModels())
import numpy as np
import torch
from cases import REPO, load, parameters
from gpu_proposer import GPUProposer
from numpy_oracle import evaluate

OUTPUT = Path(os.environ['PHASE_RUNS']) / 'v844_gpu_proposal_qualification'


def check(case, outputs, expected):
    pose_error, control_error, cost_error = [float(np.max(abs(actual - oracle)))
                                            for actual, oracle in zip(outputs[:3], expected[:3])]
    controls = outputs[1]
    delta = np.diff(np.concatenate((np.tile(case['last'], (len(controls), 1, 1)), controls), axis=1), axis=1)
    checks = dict(pose_error=pose_error <= 1e-8, control_error=control_error <= 1e-8,
                  cost_error=cost_error <= 1e-8,
                  finite=all(np.isfinite(value).all() for value in outputs),
                  top4_equal=np.array_equal(outputs[3][:4], expected[3][:4]),
                  amplitude=bool(np.all(controls >= case['lower'] - 1e-12) and np.all(controls <= case['upper'] + 1e-12)),
                  slew=bool(np.all(abs(delta) <= case['rate'] + 1e-12)))
    return dict(step=case['step'], passed=bool(all(checks.values())), checks=checks,
                maximum_pose_error=pose_error, maximum_control_error=control_error,
                maximum_cost_error=cost_error, top4=outputs[3][:4].tolist())


def main():
    assert os.environ.get('PHASE_GPU_COMPONENT_ONLY') == '1'
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert torch.cuda.is_available()
    torch.cuda.set_per_process_memory_fraction(.25, 0)
    data, sources = load()
    configuration = parameters()
    start = time.perf_counter()
    proposer = GPUProposer(data[0], configuration)
    details = []
    for case in data:
        assert time.time() < float(os.environ['PHASE_GPU_COMPONENT_DEADLINE'])
        proposer.execute(case)
        row = check(case, proposer.full_outputs(), evaluate(case, configuration))
        details.append(row)
        print(json.dumps(row), flush=True)
        assert row['passed'], 'PREPARATION_MATH_OR_COMMAND_GATE_FAILED'
    result = dict(status='GPU_INTERFACE_MATH_PREPARATION_PASS', passed=True, details=details,
                  preparation_s=time.perf_counter()-start, source_inputs=sources,
                  physical_models=0, physics_integrations=0, navigation=0,
                  not_a_real_time_or_physical_acceptance=True)
    (OUTPUT / 'PREPARATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        path = OUTPUT / ('PREPARATION_ERROR_' + str(time.time_ns()) + '.json')
        path.write_text(json.dumps(dict(type=type(error).__name__, message=str(error),
                                       traceback=traceback.format_exc(), models=0,
                                       physics_integrations=0), indent=2) + '\n')
        raise
