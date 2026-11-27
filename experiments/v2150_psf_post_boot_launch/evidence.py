"""Shared SOURCE, independent per-case archives, reserved concurrent I/O."""
from pathlib import Path
import gzip, hashlib, importlib.util, json, os, subprocess, sys, tarfile, time
R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
ROOT = R / 'runs' / C.name
P = R / 'runs/v2147_psf_full_route'
SOURCE_D = ROOT / 'recovery'
STUDY = ROOT
CASES = {'PSF':'PSF'}

def read(p):
    p = Path(p)
    v = json.loads(p.read_text())
    if p.name == 'SOURCE_FREEZE.json' and 'inherit_freeze_path' in v:
        parent = R / v['inherit_freeze_path']
        assert sha(parent) == v['inherit_freeze_sha256']
        base = read(parent)['files']
        assert all((n not in base or base[n] == h for (n, h) in v['files'].items()))
        v = dict(v, files=dict(base, **v['files']))
    return v

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda : f.read(1024 ** 2), b''):
            h.update(b)
    return h.hexdigest()

def put(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(v, indent=2, allow_nan=False).encode() + b'\n'
    assert len(raw) < (10 if p.name=='ARCHIVE_INDEX.json'else 2) * 1024 ** 2
    t = p.with_suffix(p.suffix + '.tmp')
    t.write_bytes(raw)
    t.replace(p)

def load(n, p):
    spec = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[n] = m
    spec.loader.exec_module(m)
    return m

def scope(rid):
    assert rid is None or rid in CASES
    return (ROOT, SOURCE_D) if rid is None else (ROOT/'components'/rid, ROOT / 'runtime_archives' / rid)

def archive(rid=None):
    (S, D) = scope(rid)
    runtime = rid is not None
    D.mkdir(parents=True, exist_ok=True)
    assert not (D / 'ARCHIVE_CLAIM.json').exists()
    if runtime:
        assert read(S / 'COMPLETION.json')['closed'] and read(S / 'COMPLETION.json')['closed']
    else:
        assert read(ROOT / 'SOURCE_QUALIFICATION.json')['passed'] and read(P / 'POST_SOURCE_STORAGE_BARRIER.json')['passed']
    census = load('bounded_existing_prep_reservation', C / 'reservation.py')
    admission = census.admission()
    frozen = read(ROOT / 'SOURCE_FREEZE.json')['files']
    assert all((sha(R / n) == h for (n, h) in frozen.items()))
    put(D / 'ARCHIVE_CLAIM.json', dict(unix=time.time(), rid=rid, archive_cap=(48 if runtime else 16) * 1024 ** 2, new_model_or_optimizer_calls=0, joint_peak_bytes=admission['joint_peak_bytes']))
    files = set()
    for folder in [C]:
        for p in folder.iterdir():
            if p.is_file():
                files.add(p)
    if runtime:
        for p in S.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and (not p.is_relative_to(ROOT / 'recovery')) and (not p.is_relative_to(ROOT / 'runtime_archives')):
                files.add(p)
        for p in (ROOT / 'math').rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                files.add(p)
        for name in ['CURRENT_SOURCE_REMOTE_RECOVERY.json', 'POST_SOURCE_STORAGE_BARRIER.json', 'AUTHORIZATION.json']:
            files.add(ROOT / name)
        for folder in [ROOT / 'evidence_lane', ROOT / 'workers', ROOT / 'round_reports' / rid]:
            if folder.exists():
                for p in folder.rglob('*'):
                    if p.is_file():
                        files.add(p)
    inherited = read(P / 'SOURCE_FREEZE.json')['files']
    for (n, h) in frozen.items():
        if inherited.get(n) != h:
            files.add(R / n)
    for n in ['SOURCE_FREEZE.json', 'SOURCE_QUALIFICATION.json', 'SOURCE_OUTER_CLOSED.json', 'SOURCE_INHERITED_CHAINS.json']:
        files.add(ROOT / n)
    inv = load('original_exact_archive_inventory', R / 'experiments/v1391_handoff_archive_recovery/archive.py').inventory
    items = inv(sorted(files), {})
    wanted = {x['path']: x for x in items}
    io = load('original_bounded_archive_parts', R / 'experiments/v1382_weekend_campaign/storage_preserve.py')

    class Parts(io.Parts):

        def write(self, b):
            assert self.total + len(b) <= (48 if runtime else 16) * 1024 ** 2, 'RESERVED_ARCHIVE_CAP'
            return super().write(b)
    folder = D / 'archive'
    folder.mkdir()
    writer = Parts(folder, ('v2150-source' if not runtime else 'v2150-' + rid) + '-evidence.tar.gz')
    with gzip.GzipFile(fileobj=writer, mode='wb', compresslevel=3, mtime=0) as z, tarfile.open(fileobj=z, mode='w|') as tar:
        for row in items:
            info = tarfile.TarInfo(row['path'])
            if 'symlink' in row:
                info.type = tarfile.SYMTYPE
                info.linkname = row['symlink']
                tar.addfile(info)
            else:
                info.size = row['bytes']
                with (R / row['path']).open('rb') as f:
                    tar.addfile(info, f)
    writer.finish()
    parts = [folder / x['name'] for x in writer.parts]
    whole = hashlib.sha256()
    for (p, row) in zip(parts, writer.parts):
        assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
        whole.update(p.read_bytes())
    assert whole.hexdigest() == writer.digest.hexdigest()
    seen = set()
    with tarfile.open(fileobj=io.Reader(parts), mode='r|gz') as tar:
        for m in tar:
            assert m.name in wanted and m.name not in seen
            row = wanted[m.name]
            if 'symlink' in row:
                assert m.issym() and m.linkname == row['symlink']
            else:
                assert m.isfile() and m.size == row['bytes']
                h = hashlib.sha256()
                f = tar.extractfile(m)
                for b in iter(lambda : f.read(1024 ** 2), b''):
                    h.update(b)
                assert h.hexdigest() == row['sha256']
            seen.add(m.name)
    assert seen == set(wanted) and all((sha(R / n) == h for (n, h) in frozen.items()))
    put(D / 'ARCHIVE_INDEX.json', dict(files=items, parts=writer.parts, archive_bytes=writer.total, archive_sha256=writer.digest.hexdigest(), local_members_and_reassembly_verified=True, rid=rid, scope='PSF exposed fullroute, unchanged mathematics and original gates, counted exact prediction reconstruction; not formal confirmation' if not runtime else 'PSF exposed fullroute original goal attempt, original physical capture/replay/fullgoal or canonical refusal; not formal confirmation'))
    put(D / 'FINALIZED.json', dict(passed=True, scientific_navigation_passed=None, only_archive_complete=True, members=len(items), archive_bytes=writer.total, new_model_or_optimizer_calls=0))
    print(json.dumps(read(D / 'FINALIZED.json')))

def sync():
    D = SOURCE_D
    assert not (D / 'SOURCE_SYNC_CLAIM.json').exists()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip()
    assert head != read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit'], 'NEW_SOURCE_MUST_HAVE_NEW_COMMIT_BEFORE_PUSH'
    for source_file in C.iterdir():
        if source_file.is_file() and source_file.suffix in {'.py','.md'}:
            assert subprocess.check_output(['git','show',head+':'+str(source_file.relative_to(R))],cwd=R)==source_file.read_bytes(), 'SOURCE_GIT_BYTES_MUST_MATCH_BEFORE_SYNC_CLAIM'
    put(D / 'SOURCE_SYNC_CLAIM.json', dict(head=head, unix=time.time(), no_retry=True))
    proof = dict(head=head, remote_verified=False, push_executed=False)
    try:
        p = subprocess.run(['git', 'push', 'origin', 'HEAD:main'], cwd=R, capture_output=True, timeout=30)
        proof.update(push_executed=True, push_returncode=p.returncode)
        p = subprocess.run([str(R / 'tools/phase_storage_20261107/vendor/gh'), 'api', 'repos/frank8763/phase-/git/ref/heads/main'], cwd=R, env=dict(os.environ, GODEBUG='http2client=0'), capture_output=True, timeout=5)
        proof['remote_verified'] = p.returncode == 0 and json.loads(p.stdout)['object']['sha'] == head
    except subprocess.TimeoutExpired:
        proof['error'] = 'BOUNDED_PUSH_OR_REF_TIMEOUT'
    put(D / 'SOURCE_SYNC_RESULT.json', proof)
    print(json.dumps(proof))
    assert proof['remote_verified']

def ref(rid):
    (S, D) = scope(rid)
    assert rid and (not (D / 'SOURCE_SYNC_RESULT.json').exists())
    r = read(ROOT / 'CURRENT_SOURCE_REMOTE_RECOVERY.json')
    p = R / r['source_sync_result_path']
    assert sha(p) == r['source_sync_result_sha256']
    x = read(p)
    assert x['remote_verified'] and x['head'] == r['source_commit']
    put(D / 'SOURCE_SYNC_RESULT.json', dict(head=x['head'], remote_verified=True, push_executed=False, ref_executed=False))

def deliver(rid=None, episode=0, preview=False):
    (S, D) = scope(rid)
    runtime = rid is not None
    target = R / 'experiments/v2007_mppi_observed_source_recovery/deliver.py'
    text = target.read_text()
    recovery = episode > 0
    if recovery:
        assert runtime and 1 <= episode <= 2
        previous = 'remote_delivery' if episode == 1 else 'remote_delivery_retry_1'
        assert read(D / previous / 'RESULT.json')['closed'] and (not read(D / previous / 'RESULT.json')['passed'])
        receipts = [read(p) for p in (D / previous / 'http_receipts').glob('*.json')]
        assert len(receipts) == 6 and all((x['call'] == 1 and x['method'] == 'GET' and (not x['passed']) for x in receipts)), 'RECOVERY_ONLY_PREMUTATION_FIRST_METADATA_FAILURE'
        text = text.replace("O=D/'remote_delivery';", 'O=D/' + repr('remote_delivery_retry_' + str(episode)) + ';')
    text = text.replace("rid=os.environ.get('PHASE_EVENING_ASSIGNMENT','')", 'rid=CASE_ID')
    text = text.replace("D=S/'runtime_archives'/rid if runtime else D0", 'D=BOUND_D')
    text = text.replace("assert rid in [f'common_{i:02d}__DWA'for i in range(6,13)]", "assert rid in CASES and read(S/'COMPLETION.json')['closed']")
    text = text.replace("prior=read(D0/'remote_delivery/RELEASE.json')", "prior=read(SOURCE_D/'remote_delivery/RELEASE.json')")
    text = text.replace('phase-v2006-mppi-observed-dependencies-source-20261126', 'phase-v2150-filter-vehicle-handoff-source-20261127').replace('v2006_source', 'v2150_source')
    text = text.replace("auth=read(S/'AUTHORIZATION.json')", "auth=read(ROOT/'AUTHORIZATION.json')")
    text = text.replace('experiments/v1940_content_addressed_runtime_recovery/net.py', 'experiments/v2062_bounded_dual_route_transport/net.py')
    text = text.replace('end=start+600', "end=min(start+600,read(ROOT/'AUTHORIZATION.json')['absolute_end_unix']-15)")
    text = text.replace('h.base.ROOT_END=end', 'h.base.ROOT_END=end;h.base.usage=RESERVED_TRANSPORT_USAGE')
    text = text.replace('(4+512)*1024**2', '(8+512)*1024**2')
    text = text.replace('Phase MPPI two exact observed typesupport dependencies source', 'Phase PSF exposed full route with exact reconstruction and complete physical stopping')
    text = text.replace('One independent Stage-hidden readonly Phase namespace', 'Readonly Phase namespace; CPU2 original vehicle and reconstruction; CPU6 readonly SciPy; geometryCPU4 ownerCPU5')
    text = text.replace('One first numerical query', 'At most2500 fresh PSF queries, original full2200stop at every prediction, strict original wholegoal, exact counted reconstruction and byte-preserving metadata')
    text = text.replace('not formal navigation or vehicle safety qualification', 'original full stopping, capture, replay and independent audit; one exposed fullroute development, no formal confirmation')
    old = "assert not alias.exists();alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
    new = "assert not alias.exists()or sha(alias)==sha(D/'ARCHIVE_INDEX.json');\n        if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
    assert text.count(old) == 1
    text = text.replace(old, new)
    compile(text, str(target), 'exec')
    if preview:
        return text
    census = load('exact_bounded_existing_prep_IO', C / 'reservation.py')
    space = {'__file__': str(target), '__name__': 'source_bound_reserved_transfer'}
    exec(compile(text, str(target), 'exec'), space)
    space.update(S=S, ROOT=ROOT, D0=SOURCE_D, SOURCE_D=SOURCE_D, BOUND_D=D, CASE_ID=rid or '', CASES=CASES, RESERVED_TRANSPORT_USAGE=census.transport_current_upper)
    return space['main'](runtime=runtime)

def chain():
    D = SOURCE_D
    r = read(D / 'FULL_REMOTE_VERIFIED.json')
    assert r['passed'] and read(D / 'TRANSPORT_CLEANUP.json')['passed']
    assert not Path('/proc', str(read(D / 'remote_delivery/CLAIM.json')['pid'])).exists()
    frozen = read(ROOT / 'SOURCE_FREEZE.json')['files']
    old = read(P / 'SOURCE_FREEZE.json')['files']
    prior = read(P / 'CURRENT_SOURCE_REMOTE_RECOVERY.json')
    assert prior['passed'] and prior['all_frozen_members_remote_chain_covered']
    members = {x['path']: x for x in read(D / 'ARCHIVE_INDEX.json')['files']}
    assert all((old.get(n) == h or members.get(n, {}).get('sha256') == h for (n, h) in frozen.items()))
    assert all((sha(R / n) == h for (n, h) in frozen.items()))
    sync = read(D / 'SOURCE_SYNC_RESULT.json')
    assert sync['remote_verified'] and sync['head'] == r['source_commit']
    for name in ['owner.py','software_checks.py','qualify_source.py','evidence.py','dispatcher.py','filter_scope.py','native_worker.py','current_request.py','nominal.py','navigation.py','audit_component.py','metadata_pack.py','evidence_service.py']:
        p = C / name
        assert subprocess.check_output(['git', 'show', sync['head'] + ':' + str(p.relative_to(R))], cwd=R) == p.read_bytes()
    value = dict(passed=True, all_frozen_members_remote_chain_covered=True, uncovered_members=[], source_members=len(frozen), source_commit=sync['head'], index_path=str((D / 'ARCHIVE_INDEX.json').relative_to(R)), index_sha256=sha(D / 'ARCHIVE_INDEX.json'), full_remote_proof_path=str((D / 'FULL_REMOTE_VERIFIED.json').relative_to(R)), full_remote_proof_sha256=sha(D / 'FULL_REMOTE_VERIFIED.json'), source_sync_result_path=str((D / 'SOURCE_SYNC_RESULT.json').relative_to(R)), source_sync_result_sha256=sha(D / 'SOURCE_SYNC_RESULT.json'), models_authorized=False)
    put(ROOT / 'CURRENT_SOURCE_REMOTE_RECOVERY.json', value)
    put(ROOT / 'POST_SOURCE_STORAGE_BARRIER.json', dict(passed=True, recovery_sha256=sha(ROOT / 'CURRENT_SOURCE_REMOTE_RECOVERY.json'), actual_remote_all_SHA=True, cleanup_sha256=sha(D / 'TRANSPORT_CLEANUP.json'), models_authorized=False))
    print(json.dumps(dict(passed=True, source_members=len(frozen), finite_original_unclaimed_cases=len(CASES))))

def main():
    os.sched_setaffinity(0, {5})
    stage = sys.argv[1]
    rid = sys.argv[2] if len(sys.argv) > 2 else None
    if stage == 'archive':
        archive(rid)
    elif stage == 'sync':
        sync()
    elif stage == 'ref':
        ref(rid)
    elif stage == 'deliver':
        raise SystemExit(deliver(rid, episode=int(os.environ.get('PHASE_TRANSFER_EPISODE', '0'))))
    elif stage == 'chain':
        chain()
    else:
        raise AssertionError('UNKNOWN_STAGE')
if __name__ == '__main__':
    main()
