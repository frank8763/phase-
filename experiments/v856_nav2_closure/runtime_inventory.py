"""Read ELF dependency closures of verified ROS binaries, not model integration."""
import hashlib,json,os,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v856_nav2_foundation';FS=ROOT/'rootfs';PREFIX=Path('/opt/ros/jazzy');selected=set();host=set();missing=[]
def add(p):
    if not(p.is_symlink()or p.is_file()):return
    if p.is_symlink():
        selected.add(p)
        target=p.resolve()
        if target.is_relative_to(FS):add(target)
        elif target.is_relative_to(PREFIX):add(FS/str(target).lstrip('/'))
        else:host.add(str(target))
    else:selected.add(p)
for base in [FS/'opt/ros/jazzy/lib',FS/'opt/ros/jazzy/bin',FS/'opt/ros/jazzy/share',FS/'usr/lib/python3']:
    for p in base.rglob('*'):
        if any(x in p.parts for x in ['__pycache__','cmake','pkgconfig','test','tests'])or p.suffix in ['.a','.h','.hpp','.pyc']:continue
        add(p)
for p in (FS/'opt/ros/jazzy').iterdir():
    if p.is_file():add(p)
for p in sorted(list(selected)):
    if p.is_symlink():continue
    with p.open('rb')as f:magic=f.read(4)
    if magic!=b'\x7fELF':continue
    path=PREFIX/p.relative_to(FS/'opt/ros/jazzy')if p.is_relative_to(FS/'opt/ros/jazzy')else p
    completed=subprocess.run(['/usr/bin/ldd',str(path)],capture_output=True,text=True)
    for line in completed.stdout.splitlines():
        if 'not found'in line:missing.append(dict(binary=str(p),line=line))
        for match in re.finditer(r'(?:=>\s*)?(/[^\s]+)',line):
            value=Path(match[1])
            if value.is_relative_to(PREFIX):add(FS/str(value).lstrip('/'))
            elif value.is_relative_to(FS):add(value)
            else:host.add(str(value))
# ldd reports the full transitive closure for each ELF.
assert not missing,missing
records=[]
for p in sorted(selected):
    if p.is_symlink():records.append(dict(path=str(p.relative_to(R)),type='symlink',link=os.readlink(p),bytes=0))
    else:records.append(dict(path=str(p.relative_to(R)),type='file',bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(ROOT/'RUNTIME_SELECTED.json').write_text(json.dumps(dict(files=records,total_bytes=sum(x['bytes']for x in records),host_system_libraries=sorted(host),scope='Verified ROS runtime and transitive non-system library dependencies; not SDK, compiler or static libraries. Requires compatible Ubuntu24.04 host and system Python3.12.'),indent=2)+'\n');print(json.dumps(dict(runtime_files=len(records),runtime_bytes=sum(x['bytes']for x in records),host_libraries=len(host))))
