"""One bounded missing-byte readback continuation; no upload or git retry."""
import concurrent.futures
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from package import *
from deliver import gh, GH, REPO


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl): return None


def main():
    claim = D / 'READBACK_CONTINUATION_CLAIM.json'
    assert not claim.exists() and not (D / 'FULL_REMOTE_VERIFIED.json').exists()
    assert (D / 'INITIAL_READBACK_INTERRUPTION.json').exists()
    release = read(D / 'RELEASE_CREATED.json'); rid = release['id']; head = release['head']
    index = read(D / 'RECORD_INDEX.json'); tag = index['release_tag']
    start = time.monotonic(); dump(claim, dict(release_id=rid, started_unix=time.time(), maximum_s=420, no_upload=True, no_git_push=True, models=0))
    assets = json.loads(gh(['api', f'repos/{REPO}/releases/{rid}/assets?per_page=100'], 30))
    byname = {x['name']: x for x in assets}
    token = subprocess.check_output([str(GH), 'auth', 'token'], cwd=R, text=True, timeout=10).strip()
    assert token, 'AUTH_UNAVAILABLE'
    opener = urllib.request.build_opener(NoRedirect())
    output = O / 'readback'; jobs = []
    for group in index['archives']:
        for item in group['parts']:
            jobs.append(dict(item, local=O / 'transport' / group['group'] / item['name']))
    for name in ['RECORD_INDEX.json', 'SOURCE_INVENTORY.json', 'RESULT_SUMMARY.json']:
        path = D / name; jobs.append(dict(name=name, bytes=path.stat().st_size, sha256=sha(path), local=path))

    def signed_url(asset):
        request = urllib.request.Request(f'https://api.github.com/repos/{REPO}/releases/assets/{asset["id"]}', headers={'Accept': 'application/octet-stream', 'Authorization': 'Bearer ' + token, 'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with opener.open(request, timeout=30): raise AssertionError('EXPECTED_ASSET_REDIRECT')
        except urllib.error.HTTPError as error:
            assert error.code == 302, 'ASSET_REDIRECT_STATUS'
            url = error.headers['Location']
            parsed = urllib.parse.urlsplit(url)
            assert parsed.scheme == 'https' and parsed.hostname in ['release-assets.githubusercontent.com', 'objects.githubusercontent.com'], 'ASSET_HOST'
            return url

    def download(item):
        asset = byname[item['name']]; assert asset['size'] == item['bytes'] and asset['state'] == 'uploaded'
        if asset.get('digest'): assert asset['digest'] == 'sha256:' + item['sha256']
        path = output / item['name']
        if path.exists() and path.stat().st_size == item['bytes'] and sha(path) == item['sha256']:
            return dict(name=item['name'], reused_verified=True, newly_read_bytes=0)
        offset = path.stat().st_size if path.exists() else 0
        assert offset < item['bytes']
        if offset:
            # Prefix from the interrupted remote read must match the source;
            # final SHA still covers the complete remotely downloaded part.
            with item['local'].open('rb') as stream: assert path.read_bytes() == stream.read(offset), 'PREFIX_DIFFERS'
        url = signed_url(asset); first = offset
        with path.open('ab') as stream:
            while offset < item['bytes']:
                assert time.monotonic() - start < 420, 'READBACK_HARD_STOP'
                end = min(offset + 1024**2, item['bytes']) - 1
                request = urllib.request.Request(url, headers={'Range': f'bytes={offset}-{end}'})
                with urllib.request.urlopen(request, timeout=60) as response:
                    assert response.status == 206 and response.headers['Content-Range'] == f'bytes {offset}-{end}/{item["bytes"]}', 'EXACT_RANGE_REQUIRED'
                    data = response.read(end - offset + 2)
                assert len(data) == end - offset + 1, 'SHORT_RANGE'
                stream.write(data); stream.flush(); offset += len(data)
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], 'REMOTE_COMPLETE_PART_SHA'
        return dict(name=item['name'], reused_verified=False, newly_read_bytes=item['bytes'] - first)

    results = []; errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download, item): item['name'] for item in jobs}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                result = future.result(); results.append(result); print(json.dumps(result), flush=True)
            except Exception as error:
                # Never persist tokens or signed URL query strings in errors.
                errors.append(dict(name=name, error_type=type(error).__name__, reason=str(error) if isinstance(error, AssertionError) else 'TRANSPORT_EXCEPTION_REDACTED'))
    dump(D / 'READBACK_CONTINUATION_RESULT.json', dict(passed=not errors, results=results, errors=errors, models=0))
    assert not errors, 'READBACK_FAILED_NO_CLEANUP'
    allitems = read(D / 'SOURCE_INVENTORY.json')['files']; groups = []
    for group in index['archives']:
        archive = output / (group['group'] + '.tar.gz')
        with archive.open('xb') as stream:
            for part in group['parts']: stream.write((output / part['name']).read_bytes())
        assert sha(archive) == group['archive_sha256']
        count = verify(archive, [x for x in allitems if x['group'] == group['group']])
        groups.append(dict(group=group['group'], members=count, member_sha_verified=True))
        print(json.dumps(dict(remote_group_verified=group['group'], members=count)), flush=True)
    gh(['release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest=false'], 30)
    final = json.loads(gh(['api', f'repos/{REPO}/releases/{rid}'], 30))
    ref = json.loads(gh(['api', f'repos/{REPO}/git/ref/tags/{tag}'], 30))
    assert not final['draft'] and ref['object']['sha'] == head
    proof = dict(passed=True, published=True, release_url=final['html_url'], release_id=rid, source_commit=head, all_parts_downloaded_SHA_verified=True, every_decompressed_member_SHA_verified=True, groups=groups, verified_members=sum(g['members'] for g in groups), raw_bytes=index['raw_bytes'], tag_commit_verified=True, initial_timeout_preserved=True, bounded_missing_byte_readback=True, models=0, physical_native=0, completed_unix=time.time())
    dump(D / 'FULL_REMOTE_VERIFIED.json', proof); print(json.dumps(proof), flush=True)


if __name__ == '__main__': main()
