"""Once-only frozen CUDA proposal math/timing qualification, with zero physics."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


class NoModels:
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('GPU_QUALIFICATION_FORBIDS_PHYSICAL_MODELS')


sys.meta_path.insert(0, NoModels())
import numpy as np
import torch
from cases import BATCH, HORIZON, REPO, load, parameters
from gpu_proposer import GPUProposer
from numpy_oracle import evaluate
from prepare_gpu import check

PACKAGE = Path(__file__).resolve().parent
OUTPUT = REPO / 'runs/v844_gpu_proposal_qualification'


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unchanged():
    freeze = json.loads((PACKAGE / 'FREEZE.json').read_text())
    assert all(sha(REPO / name) == digest for name, digest in freeze['files'].items()), 'FROZEN_INPUT_OR_CODE_CHANGED'


def percentiles(values):
    return dict(zip(['p50_ms', 'p95_ms', 'p99_ms', 'maximum_ms'],
                    map(float, np.percentile(values, [50, 95, 99, 100]))))


def main():
    lock = (OUTPUT / 'qualification.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert json.loads((OUTPUT / 'PREPARATION.json').read_text())['passed']
    unchanged()
    assert os.environ.get('PHASE_GPU_COMPONENT_ONLY') == '1'
    start = time.time()
    deadline = min(start + 900., float(os.environ['PHASE_GPU_COMPONENT_DEADLINE']), 1794009600.)
    with (OUTPUT / 'QUALIFICATION_CLAIM.json').open('x') as stream:
        json.dump(dict(pid=os.getpid(), started_unix=start, deadline_unix=deadline,
                       attempts=1, old_windows_unchanged=True), stream)
    guard = (REPO / 'REVIEW_PENDING').read_bytes()
    result = None
    try:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        assert torch.cuda.is_available(), 'CUDA_REQUIRED_NO_CPU_FALLBACK'
        torch.cuda.set_per_process_memory_fraction(.25, 0)
        data, sources = load()
        configuration = parameters()
        before = time.perf_counter()
        proposer = GPUProposer(data[0], configuration)
        setup_s = time.perf_counter() - before
        rows, negative_checks = [], {}
        calls = 0
        for case in data:
            assert time.time() < deadline, 'GPU_QUALIFICATION_DEADLINE'
            proposer.execute(case)
            calls += 1
            before = time.perf_counter()
            outputs = proposer.full_outputs()
            full_transfer_ms = (time.perf_counter() - before) * 1000.
            row = check(case, outputs, evaluate(case, configuration))
            assert row['passed'], 'GPU_MATH_OR_CONTROL_QUALIFICATION_FAILED'
            if not negative_checks:
                corrupted = [value.copy() for value in outputs]
                corrupted[0][0, 0, 0] += .01
                negative_checks['pose_corruption_rejected'] = not check(case, corrupted, outputs)['passed']
                corrupted = [value.copy() for value in outputs]
                corrupted[1][0, 0, 0] = case['upper'][0] + .1
                negative_checks['illegal_control_rejected'] = not check(case, corrupted, outputs)['passed']
                corrupted = [value.copy() for value in outputs]
                corrupted[3][0], corrupted[3][1] = corrupted[3][1], corrupted[3][0]
                negative_checks['wrong_selection_rejected'] = not check(case, corrupted, outputs)['passed']
                try:
                    __import__('mujoco')
                except RuntimeError:
                    negative_checks['physical_model_import_blocked'] = True
                else:
                    negative_checks['physical_model_import_blocked'] = False
                assert all(negative_checks.values()), 'NEGATIVE_QUALIFICATION_FAILED'
            selected = outputs[3][:4]
            np.savez_compressed(OUTPUT / f'proposal_step{case["step"]:04d}.npz',
                                candidate_indices=selected, approximate_poses=outputs[0][selected],
                                controls=outputs[1][selected], costs=outputs[2][selected],
                                pose=case['pose'], previous_control=case['last'],
                                native_certification_required=np.asarray(True))
            for _ in range(8):
                proposer.execute(case)
                calls += 1
            timings, kernel = [], []
            for _ in range(100):
                assert time.time() < deadline
                before = time.perf_counter()
                proposer.execute(case)
                torch.cuda.synchronize()
                timings.append((time.perf_counter() - before) * 1000.)
                calls += 1
            begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            for _ in range(20):
                begin.record()
                proposer.graph.replay()
                end.record()
                end.synchronize()
                kernel.append(begin.elapsed_time(end))
                calls += 1
            row.update(end_to_end=percentiles(timings), kernel_only=percentiles(kernel),
                       end_to_end_samples_ms=timings, kernel_samples_ms=kernel,
                       full_batch_transfer_ms=full_transfer_ms,
                       latency_passed=percentiles(timings)['p95_ms'] <= 20.,
                       semantics='Input H2D, graph, selected4 D2H and synchronization; no native physical safety certificate')
            rows.append(row)
            print(json.dumps({key: value for key, value in row.items()
                              if not key.endswith('_samples_ms')}), flush=True)
            save(OUTPUT / 'PARTIAL.json', dict(completed_cases=len(rows), details=rows))
        unchanged()
        passed = all(row['passed'] and row['latency_passed'] for row in rows) and all(negative_checks.values())
        result = dict(status='GPU_PROPOSAL_COMPONENT_QUALIFIED' if passed else 'GPU_COMPONENT_NOT_QUALIFIED',
                      component_passed=passed, cases=len(rows), batch=BATCH, ideal_public_horizon=HORIZON,
                      details=rows, negative_checks=negative_checks, inputs=sources,
                      setup_and_graph_capture_s=setup_s, measured_graph_evaluations=calls,
                      counted_ideal_proposal_steps=calls * BATCH * HORIZON,
                      additional_setup_ideal_model_work='3 eager warmups and CUDA graph capture; capture execution count not asserted',
                      physical_models=0, physical_integrations=0, native_replay=0, navigation=0,
                      training=0, new24=0, native_certificate_latency_ms=None,
                      full_closed_loop_realtime_passed=False, dynamic_acceptance_passed=False,
                      device=torch.cuda.get_device_name(0), torch_version=torch.__version__,
                      cuda_build=torch.version.cuda, peak_allocator_bytes=torch.cuda.max_memory_allocated(),
                      elapsed_s=time.time()-start, deadline_unix=deadline,
                      frozen_sources_verified=True, source_or_guard_changed=False)
        save(OUTPUT / 'QUALIFICATION.json', result)
    except BaseException as error:
        save(OUTPUT / 'ERROR.json', dict(type=type(error).__name__, message=str(error),
                                        traceback=traceback.format_exc(), completed_result=result,
                                        physical_models=0, physical_integrations=0))
        raise
    finally:
        assert (REPO / 'REVIEW_PENDING').read_bytes() == guard, 'REVIEW_GUARD_CHANGED'
        save(OUTPUT / 'COMPLETION.json', dict(closed=True, result_present=result is not None,
                                             status=None if result is None else result['status'],
                                             no_automatic_navigation=True, no_model_retries=True,
                                             review_guard_exact=True, closed_unix=time.time()))


if __name__ == '__main__':
    main()
