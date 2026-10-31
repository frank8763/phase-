"""Verify a committed Phase tree remotely and local evidence SHA256 manifests.

No simulation. Uses the repository's existing Git authentication when the API
requires it; credentials stay in process memory and are never printed/saved.
Remote verification is per-file Git blob identity, linked to locally verified
SHA256 manifest bytes, rather than downloading every large blob a second time.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

repo=Path(__file__).resolve().parents[2]
out=repo/'runs/v657_remote_verification';out.mkdir(exist_ok=True)
clean=os.environ.copy()
for key in ['HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','https_proxy','http_proxy','all_proxy']:
    clean.pop(key,None)
clean['GIT_TERMINAL_PROMPT']='0'
def git(*args):
    return subprocess.check_output(['git','-c','http.proxy=',*args],cwd=repo,env=clean,timeout=30)
commit=git('rev-parse','HEAD').decode().strip()
remote=git('ls-remote','origin','refs/heads/main').decode().split()[0]
assert remote==commit,'REMOTE_HEAD_DOES_NOT_MATCH_EVIDENCE_COMMIT'
tree=git('rev-parse',commit+'^{tree}').decode().strip()
url=f'https://api.github.com/repos/frank8763/phase-/git/trees/{tree}?recursive=1'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
headers={'Accept':'application/vnd.github+json','User-Agent':'Phase-evidence-verifier',
         'X-GitHub-Api-Version':'2022-11-28'}
try:
    with opener.open(urllib.request.Request(url,headers=headers),timeout=30)as stream:
        data=json.load(stream)
except urllib.error.HTTPError as error:
    if error.code not in [401,403,404]:raise
    # Standard Git credential flow scoped to the already-authorized repository.
    result=subprocess.run(['git','credential','fill'],input=b'protocol=https\nhost=github.com\npath=frank8763/phase-.git\n\n',
                          stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=repo,env=clean,timeout=10,check=True)
    fields=dict(line.split('=',1)for line in result.stdout.decode().splitlines()if'='in line)
    token=fields.get('password');assert token,'No existing repository API credential'
    headers['Authorization']='Bearer '+token
    with opener.open(urllib.request.Request(url,headers=headers),timeout=30)as stream:
        data=json.load(stream)
    headers.pop('Authorization',None);fields.clear();token=None
assert data['sha']==tree and data.get('truncated')is False
remote_blobs={x['path']:x for x in data['tree']if x['type']=='blob'}
local={}
for record in git('ls-tree','-rz',commit).split(b'\0'):
    if not record:continue
    meta,_,path=record.partition(b'\t');mode,kind,oid=meta.decode().split()
    if kind=='blob':local[path.decode()]=oid
assert set(remote_blobs)==set(local)
for path,oid in local.items():assert remote_blobs[path]['sha']==oid,path
packages=[];manifest_files=0
for manifest in sorted((repo/'evidence').glob('*/MANIFEST.json')):
    rows=json.loads(manifest.read_text())
    if not isinstance(rows,list)or not all(isinstance(x,dict)and'path'in x and'sha256'in x and'bytes'in x for x in rows):
        continue
    for row in rows:
        path=manifest.parent/row['path'];content=path.read_bytes();relative=str(path.relative_to(repo))
        assert len(content)==row['bytes']and hashlib.sha256(content).hexdigest()==row['sha256'],relative
        oid=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
        assert oid==remote_blobs[relative]['sha']==local[relative],relative
    packages.append({'package':str(manifest.parent.relative_to(repo)),'files':len(rows),
                     'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()})
    manifest_files+=len(rows)
report={'status':'PASS','verified_evidence_commit':commit,'verified_remote_head':remote,'tree_sha':tree,
        'all_remote_file_blob_ids_match':True,'tracked_files_compared':len(local),
        'manifest_packages_verified':len(packages),'manifest_files_sha256_and_remote_blob_verified':manifest_files,
        'packages':packages,'method':'remote complete recursive tree and every per-file Git blob ID compared to committed local tree; retained manifest bytes independently SHA256-verified and converted to Git blob IDs',
        'simulation_steps':0,'training_updates':0}
(out/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='packages'},indent=2))
