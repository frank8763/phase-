"""Retain partial network reads; finish only missing bytes inside original bound."""
import concurrent.futures
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from package import *
from deliver import gh, GH, REPO
from resume_readback import NoRedirect


def main():
    assert not (D / 'SMALL_FRAGMENT_CLAIM.json').exists()
    previous = read(D / 'READBACK_CONTINUATION_CLAIM.json')
    deadline = previous['started_unix'] + 420
    assert time.time() < deadline and not (D / 'FULL_REMOTE_VERIFIED.json').exists()
    dump(D / 'SMALL_FRAGMENT_CLAIM.json', dict(original_deadline_unix=deadline, chunk_bytes=65536, partial_read_bytes=16384, models=0))
    release = read(D / 'RELEASE_CREATED.json'); rid = release['id']; head = release['head']
    index = read(D / 'RECORD_INDEX.json'); tag = index['release_tag']; output = O / 'readback'
    assets = {a['name']: a for a in json.loads(gh(['api', f'repos/{REPO}/releases/{rid}/assets?per_page=100'], 30))}
    token = subprocess.check_output([str(GH), 'auth', 'token'], cwd=R, text=True, timeout=10).strip()
    jobs = []
    for group in index['archives']:
        for part in group['parts']:
            path = output / part['name']
            if path.exists() and path.stat().st_size == part['bytes'] and sha(path) == part['sha256']: continue
            jobs.append(dict(part, local=O / 'transport' / group['group'] / part['name']))

    def run(item):
        path = output / item['name']; offset = path.stat().st_size if path.exists() else 0
        with item['local'].open('rb') as source: assert path.read_bytes() == source.read(offset)
        assert assets[item['name']]['size'] == item['bytes']
        request = urllib.request.Request(f'https://api.github.com/repos/{REPO}/releases/assets/{assets[item["name"]]["id"]}', headers={'Accept': 'application/octet-stream', 'Authorization': 'Bearer ' + token})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=20): raise AssertionError('REDIRECT_REQUIRED')
        except urllib.error.HTTPError as error:
            assert error.code == 302; url = error.headers['Location']; error.close()
        parsed = urllib.parse.urlsplit(url); assert parsed.scheme == 'https' and parsed.hostname in ['release-assets.githubusercontent.com', 'objects.githubusercontent.com']
        with path.open('ab') as stream:
            while offset < item['bytes']:
                remaining = deadline - time.time(); assert remaining > 0, 'ORIGINAL_READBACK_DEADLINE'
                end = min(offset + 65536, item['bytes']) - 1
                req = urllib.request.Request(url, headers={'Range': f'bytes={offset}-{end}'})
                with urllib.request.urlopen(req, timeout=min(30, remaining)) as response:
                    assert response.status == 206 and response.headers['Content-Range'] == f'bytes {offset}-{end}/{item["bytes"]}'
                    while offset <= end:
                        assert time.time() < deadline, 'ORIGINAL_READBACK_DEADLINE'
                        data = response.read(min(16384, end - offset + 1)); assert data, 'SHORT_READ'
                        stream.write(data); stream.flush(); offset += len(data)
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
        print(json.dumps(dict(completed=item['name'], bytes=item['bytes'])), flush=True)

    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run, item): item['name'] for item in jobs}
        for future in concurrent.futures.as_completed(futures):
            try: future.result()
            except Exception as error: errors.append(dict(name=futures[future], error_type=type(error).__name__, reason=str(error) if isinstance(error, AssertionError) else 'TRANSPORT_EXCEPTION_REDACTED'))
    dump(D / 'SMALL_FRAGMENT_RESULT.json', dict(passed=not errors, errors=errors, original_deadline_unix=deadline, models=0))
    assert not errors, 'READBACK_STOP_NO_CLEANUP'
    members = read(D / 'SOURCE_INVENTORY.json')['files']; groups = []
    for group in index['archives']:
        archive = output / (group['group'] + '.tar.gz')
        with archive.open('xb') as stream:
            for part in group['parts']:
                p = output / part['name']; assert p.stat().st_size == part['bytes'] and sha(p) == part['sha256']; stream.write(p.read_bytes())
        assert sha(archive) == group['archive_sha256']
        count = verify(archive, [x for x in members if x['group'] == group['group']]); groups.append(dict(group=group['group'], members=count, member_sha_verified=True))
    for name in ['RECORD_INDEX.json', 'SOURCE_INVENTORY.json', 'RESULT_SUMMARY.json']: assert sha(output / name) == sha(D / name)
    gh(['release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest=false'], 30)
    final = json.loads(gh(['api', f'repos/{REPO}/releases/{rid}'], 30)); ref = json.loads(gh(['api', f'repos/{REPO}/git/ref/tags/{tag}'], 30))
    assert not final['draft'] and ref['object']['sha'] == head
    proof = dict(passed=True, published=True, release_url=final['html_url'], release_id=rid, source_commit=head, all_parts_downloaded_SHA_verified=True, every_decompressed_member_SHA_verified=True, groups=groups, verified_members=sum(g['members'] for g in groups), raw_bytes=index['raw_bytes'], tag_commit_verified=True, initial_timeouts_preserved=True, missing_byte_continuation_original_bound=True, models=0, physical_native=0, completed_unix=time.time())
    dump(D / 'FULL_REMOTE_VERIFIED.json', proof); print(json.dumps(proof), flush=True)


if __name__ == '__main__': main()
