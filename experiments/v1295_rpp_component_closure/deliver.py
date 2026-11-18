"""One release publication and full downloaded member verification; no models."""
import json
import subprocess
import time
from package import *

GH = R / 'tools/phase_storage_20261107/vendor/gh'
REPO = 'frank8763/phase-'


def gh(args, timeout=60):
    p = subprocess.run([str(GH), *args], cwd=R, capture_output=True, text=True, timeout=timeout)
    assert p.returncode == 0, 'GITHUB_OPERATION_FAILED ' + str(args[:3]) + ': ' + p.stderr[-500:]
    return p.stdout


def main():
    assert not (D / 'DELIVERY_CLAIM.json').exists(), 'NO_DUPLICATE_DELIVERY'
    sync = read(D / 'GIT_SYNC_RESULT.json'); assert sync['push_succeeded'] and sync['remote_head_verified']
    index = read(D / 'RECORD_INDEX.json'); head = sync['head']; tag = index['release_tag']
    dump(D / 'DELIVERY_CLAIM.json', dict(tag=tag, source_commit=head, at=time.time(), models=0))
    req = O / 'CREATE_RELEASE.json'
    dump(req, dict(tag_name=tag, target_commitish=head, name='RPP current-vehicle component: main and complete repeat',
                   body='Actual upstream RPP short straight component with current V1281 vehicle/adapter. Main and repeat passed,1685 actual plus1685 own replay each, zero complete-pair state/control error. This is not whole-route/dynamic acceptance. Original V1293 zero-navigation entry failure retained. See committed report and member SHA inventory.', draft=True, make_latest='false'))
    release = json.loads(gh(['api', '--method', 'POST', f'repos/{REPO}/releases', '--input', str(req)]))
    dump(D / 'RELEASE_CREATED.json', dict(id=release['id'], url=release['html_url'], draft=True, head=head))
    items = [O / index['asset']['name'], D / 'RECORD_INDEX.json', D / 'SOURCE_INVENTORY.json']
    for item in items:
        gh(['release', 'upload', tag, str(item), '--repo', REPO])
        print(json.dumps(dict(uploaded=item.name)), flush=True)
    assets = json.loads(gh(['api', f'repos/{REPO}/releases/{release["id"]}/assets']))
    byname = {x['name']: x for x in assets}
    downloaded = O / 'downloaded'; downloaded.mkdir()
    for item in items:
        expected = sha(item); info = byname[item.name]
        assert info['size'] == item.stat().st_size and info['state'] == 'uploaded'
        if info.get('digest'):
            assert info['digest'] == 'sha256:' + expected
        dest = downloaded / item.name
        with dest.open('xb') as f:
            p = subprocess.run([str(GH), 'release', 'download', tag, '--repo', REPO, '--pattern', item.name, '--output', '-'], cwd=R, stdout=f, stderr=subprocess.PIPE, timeout=60)
        assert p.returncode == 0 and sha(dest) == expected, 'DOWNLOADED_ASSET_SHA'
    count = verify(downloaded / index['asset']['name'], read(D / 'SOURCE_INVENTORY.json')['files'])
    gh(['release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest=false'])
    public = json.loads(gh(['api', f'repos/{REPO}/releases/{release["id"]}']))
    ref = json.loads(gh(['api', f'repos/{REPO}/git/ref/tags/{tag}']))
    assert not public['draft'] and public['tag_name'] == tag and ref['object']['sha'] == head
    proof = dict(passed=True, published=True, release_url=public['html_url'], release_id=release['id'],
                 source_commit=head, all_assets_downloaded_SHA_verified=True, every_member_SHA_verified=True,
                 verified_members=count, raw_bytes=index['raw_bytes'], archive=index['asset'], tag_commit_verified=True,
                 models=0, physical_native=0, completed_unix=time.time())
    dump(D / 'FULL_REMOTE_VERIFIED.json', proof)
    print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    main()
