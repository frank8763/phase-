"""Run the exact frozen legacy write guard on proposed output operations; no models."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
RAW = R / 'runs/v858_nav2_verified/v1347'


def child():
    guard_source = R / 'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
    tree = ast.parse(guard_source.read_text())
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'write_guard')
    namespace = dict(Path=Path, os=os, OUT=R / 'runs/v858_nav2_verified')
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(guard_source), 'exec'), namespace)
    sys.addaudithook(namespace['write_guard'])
    out = RAW / 'qualification'
    out.mkdir(parents=True, exist_ok=False)
    checks = {}
    for folder in ['physics/paired', 'physics/assets', 'logs']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    for name in ['APPLIED_JOURNAL.json', 'RESULT.json', 'physics/PATCHED_ASSEMBLY.xml',
                 'physics/MODEL_BUILD_CONTRACT.json', 'physics/SETUP.json', 'physics/INITIAL_STATE.npz']:
        p = out / name
        temporary = p.with_name(p.name + '.tmp')
        temporary.write_bytes(b'zero-model write-boundary fixture\n')
        temporary.replace(p)
        assert p.read_bytes() == b'zero-model write-boundary fixture\n'
        checks[name] = True

    def rejected(name, fn):
        try:
            fn()
        except PermissionError:
            checks[name] = True
        else:
            raise AssertionError('OUTSIDE_WRITE_NOT_REJECTED ' + name)

    rejected('old_metadata_root', lambda: (R / 'runs/v1293_rpp_component90/UNEXPECTED_WRITE.tmp').write_text('forbidden'))
    rejected('parent_traversal_outside_legacy_root', lambda: (out / '../../../../UNEXPECTED_WRITE.tmp').write_text('forbidden'))
    rejected('outside_mkdir', lambda: (R / 'runs/v1293_rpp_component90/UNEXPECTED_DIR').mkdir())
    rejected('outside_rename', lambda: (out / 'RESULT.json').replace(R / 'runs/v1293_rpp_component90/UNEXPECTED_RENAME.tmp'))
    link = out / 'readonly_source_link'
    link.symlink_to(R / 'experiments', target_is_directory=True)
    rejected('symlink_write_escape', lambda: (link / 'UNEXPECTED_WRITE.tmp').write_text('forbidden'))
    # Legacy guard resolves symlinks even for unlink. Parent cleans this test
    # link without changing the guard or following its target.
    print(json.dumps(dict(passed=all(checks.values()), checks=checks, production_guard_function_executed=True,
                         guard_root_broadened=False, models=0, physical_native=0)), flush=True)


def main():
    O.mkdir(exist_ok=True)
    out = RAW / 'qualification'
    if out.exists():
        link = out / 'readonly_source_link'
        if link.is_symlink():
            link.unlink()
        for item in sorted(out.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if item.is_symlink():
                raise AssertionError('UNEXPECTED_QUALIFICATION_SYMLINK')
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink()
        out.rmdir()
    p = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--child'],
                       cwd=R, capture_output=True, text=True, timeout=15)
    index = len(list(O.glob('output_qualification*.console'))) + 1
    (O / ('output_qualification%02d.console' % index)).write_text(p.stdout + p.stderr)
    if p.returncode:
        print(p.stdout + p.stderr)
        return p.returncode
    proof = json.loads(p.stdout.strip().splitlines()[-1])
    (O / 'OUTPUT_SCOPE_QUALIFICATION.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))
    return 0


if __name__ == '__main__':
    raise SystemExit(child() if '--child' in sys.argv else main())
