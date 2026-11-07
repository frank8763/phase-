"""Rootless verified ROS2 Jazzy binary environment; no installation scripts or models."""
import concurrent.futures,gzip,hashlib,json,os,re,shutil,subprocess,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v856_nav2_foundation';APT=OUT/'apt';PREFIX=OUT/'rootfs';BUDGET=2*1024**3
PACKAGES=['ros-jazzy-nav2-planner','ros-jazzy-nav2-smac-planner','ros-jazzy-nav2-controller','ros-jazzy-nav2-mppi-controller','ros-jazzy-nav2-bt-navigator','ros-jazzy-nav2-behaviors','ros-jazzy-nav2-lifecycle-manager','ros-jazzy-nav2-map-server','ros-jazzy-nav2-collision-monitor','ros-jazzy-nav2-velocity-smoother','ros-jazzy-rclpy','ros-jazzy-tf2-ros-py','ros-jazzy-nav2-msgs','ros-jazzy-rosgraph-msgs','python3-numpy','python3-yaml']

def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def get(url,p):
    with urllib.request.urlopen(url,timeout=60)as source,p.open('wb')as target:
        shutil.copyfileobj(source,target,1048576)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def options():return ['-o','Dir::Etc::sourcelist='+str(APT/'sources.list'),'-o','Dir::Etc::sourceparts=-','-o','Dir::State::lists='+str(APT/'lists'),'-o','Dir::State::status=/var/lib/dpkg/status','-o','Dir::Cache::archives='+str(APT/'archives'),'-o','Dir::Cache::pkgcache='+str(APT/'pkgcache.bin'),'-o','Dir::Cache::srcpkgcache='+str(APT/'srcpkgcache.bin'),'-o','APT::Sandbox::User='+str(os.getuid()),'-o','Debug::NoLocking=1']

def main():
    APT.mkdir(parents=True,exist_ok=True);lists=APT/'lists';lists.mkdir(exist_ok=True);(lists/'partial').mkdir(exist_ok=True);(APT/'archives').mkdir(exist_ok=True)
    key=APT/'ros.key'
    if not key.exists():get('https://raw.githubusercontent.com/ros/rosdistro/master/ros.key',key)
    subprocess.run(['gpg','--batch','--yes','--dearmor','--output',str(APT/'ros.gpg'),str(key)],check=True)
    mirror='https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu/';release=APT/'InRelease.verified'
    get(mirror+'dists/noble/InRelease',release)
    signature=subprocess.run(['gpgv','--keyring',str(APT/'ros.gpg'),str(release)],capture_output=True,text=True,check=True);(APT/'SIGNATURE.console').write_text(signature.stdout+signature.stderr)
    text=release.read_text();section=text.split('SHA256:\n',1)[1].split('\nSHA512:',1)[0];entries={line.split()[2]:(line.split()[0],int(line.split()[1]))for line in section.splitlines()if len(line.split())==3 and re.fullmatch('[0-9a-f]{64}',line.split()[0])};wanted='main/binary-amd64/Packages.gz';expected,size=entries[wanted];compressed=APT/'Packages.gz';get(mirror+'dists/noble/'+wanted,compressed);assert sha(compressed)==expected and compressed.stat().st_size==size
    name='mirrors.tuna.tsinghua.edu.cn_ros2_ubuntu_dists_noble';(lists/(name+'_InRelease')).write_bytes(release.read_bytes())
    with gzip.open(compressed,'rb')as source,(lists/(name+'_main_binary-amd64_Packages')).open('wb')as target:shutil.copyfileobj(source,target,1048576)
    # Existing system-owned Ubuntu indices are read through links, never edited.
    for p in Path('/var/lib/apt/lists').iterdir():
        if p.is_file()and(p.name.endswith('_InRelease')or p.name.endswith('_binary-amd64_Packages'))and p.name.startswith('mirrors.tuna.tsinghua.edu.cn_ubuntu_'):
            target=lists/p.name
            if not target.exists():target.symlink_to(p)
    (APT/'sources.list').write_text('deb [signed-by='+str(APT/'ros.gpg')+'] '+mirror+' noble main\ndeb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ubuntu noble main universe\ndeb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ubuntu noble-updates main universe\ndeb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ubuntu noble-security main universe\n')
    sim=subprocess.run(['apt-get',*options(),'--simulate','--no-install-recommends','install',*PACKAGES],capture_output=True,text=True);(APT/'SIMULATION.console').write_text(sim.stdout+sim.stderr);assert sim.returncode==0,'DEPENDENCY_RESOLUTION_FAILED'
    uris=subprocess.run(['apt-get',*options(),'--print-uris','--yes','--no-install-recommends','install',*PACKAGES],capture_output=True,text=True,check=True);(APT/'DOWNLOAD_URIS.console').write_text(uris.stdout+uris.stderr);rows=[]
    for line in uris.stdout.splitlines():
        m=re.match(r"'([^']+)' (\S+) (\d+) (\S+)",line)
        if m:rows.append(dict(url=m[1],filename=m[2],download_bytes=int(m[3]),apt_checksum=m[4]))
    install=[]
    for line in sim.stdout.splitlines():
        if line.startswith('Inst '):install.append(line.split()[1])
    assert rows and len(rows)==len(install)
    size_out=subprocess.run(['apt-cache',*options(),'show','--no-all-versions',*install],capture_output=True,text=True,check=True).stdout;installed_kib=sum(int(x)for x in re.findall(r'^Installed-Size: (\d+)$',size_out,re.M));download=sum(x['download_bytes']for x in rows)
    estimate=dict(packages=len(rows),download_bytes=download,installed_bytes=installed_kib*1024,combined_peak_estimate_bytes=download+installed_kib*1024,cap_bytes=BUDGET,official_ros_release_signature_verified=True,ros_packages_index_sha256=expected,rootless=True,no_system_package_changes=True,models=0,requested=PACKAGES,packages_to_fetch=rows);dump(OUT/'DEPENDENCY_ESTIMATE.json',estimate);print(json.dumps({k:v for k,v in estimate.items()if k!='packages_to_fetch'}),flush=True)
    assert download+installed_kib*1024<1.75*1024**3,'ROOTLESS_DEPENDENCIES_EXCEED_LOCAL_BUDGET'
    # Freeze package metadata SHA256 from the verified index and existing apt indices.
    metadata={}
    for row in rows:
        package=row['filename'].split('_')[0];out=subprocess.run(['apt-cache',*options(),'show','--no-all-versions',package],capture_output=True,text=True,check=True).stdout;found=re.search(r'^SHA256: ([0-9a-f]{64})$',out,re.M);assert found;metadata[row['filename']]=found[1]
    dump(OUT/'PACKAGE_SHA256.json',metadata);PREFIX.mkdir(exist_ok=True)
    def fetch(row):
        p=APT/'archives'/row['filename'];get(row['url'],p);assert p.stat().st_size==row['download_bytes']and sha(p)==metadata[row['filename']];return row,p
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for row,p in pool.map(fetch,rows):
            subprocess.run(['dpkg-deb','-x',str(p),str(PREFIX)],check=True,stdout=subprocess.DEVNULL);p.unlink()
    dump(OUT/'DEPENDENCIES_READY.json',dict(passed=True,prefix=str(PREFIX),package_count=len(rows),all_download_sha256_verified=True,no_package_maintainer_scripts_executed=True,rootless=True,models=0));print('ROOTLESS_NAV2_PACKAGES_READY',flush=True)
if __name__=='__main__':main()
