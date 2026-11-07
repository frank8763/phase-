"""One genuine ROS package, signed-index SHA verification, rootless extraction only."""
import gzip,hashlib,json,re,subprocess,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v863_rpp_preparation';APT=O/'apt';PREFIX=R/'runs/v856_nav2_foundation/rootfs'
def get(url,path):
 with urllib.request.urlopen(url,timeout=40)as response:path.write_bytes(response.read())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 APT.mkdir(parents=True,exist_ok=True);require='ros-jazzy-nav2-regulated-pure-pursuit-controller';mirror='https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu/'
 get('https://raw.githubusercontent.com/ros/rosdistro/master/ros.key',APT/'ros.key');subprocess.run(['gpg','--batch','--yes','--dearmor','--output',str(APT/'ros.gpg'),str(APT/'ros.key')],check=True)
 get(mirror+'dists/noble/InRelease',APT/'InRelease');p=subprocess.run(['gpgv','--keyring',str(APT/'ros.gpg'),str(APT/'InRelease')],capture_output=True,text=True,check=True);(APT/'SIGNATURE.console').write_text(p.stdout+p.stderr)
 text=(APT/'InRelease').read_text();section=text.split('SHA256:\n',1)[1].split('\nSHA512:',1)[0];entries={r.split()[2]:(r.split()[0],int(r.split()[1]))for r in section.splitlines()if len(r.split())==3 and re.fullmatch('[0-9a-f]{64}',r.split()[0])};wanted='main/binary-amd64/Packages.gz';expected,size=entries[wanted];get(mirror+'dists/noble/'+wanted,APT/'Packages.gz');assert sha(APT/'Packages.gz')==expected and(APT/'Packages.gz').stat().st_size==size
 candidates=[]
 for block in gzip.decompress((APT/'Packages.gz').read_bytes()).decode().split('\n\n'):
  row={}
  for line in block.splitlines():
   if ': 'in line and not line.startswith(' '):key,value=line.split(': ',1);row[key]=value
  if row.get('Package')==require:candidates.append(row)
 assert len(candidates)==1;c=candidates[0];assert c['Version'].startswith('1.3.13-'),'MUST_MATCH_EXISTING_NAV2_1_3_13'
 package=APT/'regulated-pure-pursuit.deb';get(mirror+c['Filename'],package);assert sha(package)==c['SHA256']and package.stat().st_size==int(c['Size'])
 before={str(p.relative_to(PREFIX)):sha(p)for p in PREFIX.rglob('*')if p.is_file()and not p.is_symlink()}
 subprocess.run(['dpkg-deb','-x',str(package),str(PREFIX)],check=True)
 for path,h in before.items():assert sha(PREFIX/path)==h,'EXISTING_RUNTIME_MODIFIED'
 new=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p))for p in PREFIX.rglob('*')if p.is_file()and not p.is_symlink()and str(p.relative_to(PREFIX))not in before]
 result=dict(passed=True,package=require,version=c['Version'],official_ros_release_signature_verified=True,package_index_sha256=expected,package_sha256=c['SHA256'],download_bytes=package.stat().st_size,package_filename=c['Filename'],no_maintainer_scripts=True,all_existing_runtime_bytes_unchanged=True,new_files=new,vehicle_models=0,native_integrations=0,ros_servers=0,actual_navigation_authorized=False,created_unix=time.time());(O/'PLUGIN_READY.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='new_files'},flush=True)
if __name__=='__main__':main()
