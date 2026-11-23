"""Read-only byte/metadata closure after the payload owner has exited."""
import fcntl,hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1706_noetic_payload_intake';P=R/'runs/v1704_signed_noetic_metadata'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 assert not p.exists(),str(p);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'RUNTIME_CLOSED_REVIEW.json').exists()
 result=read(O/'RESULT.json');claim=read(O/'ONCE_CLAIM.json');assert result['closed']and result['passed']and result['recovered_packages']==74
 assert not Path('/proc',str(claim['owner_pid'])).exists()
 assert claim['owner_sha256']==sha(R/'experiments/v1706_noetic_payload_intake/owner.py')and claim['protocol_sha256']==sha(R/'experiments/v1706_noetic_payload_intake/PROTOCOL.md')
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 manifest=read(O/'UNPACK_MANIFEST.json');packages=read(O/'PACKAGE_MANIFEST.json');prefix=R/manifest['prefix'];expected=set()
 for row in packages['packages']:
  p=R/row['deb_path'];assert p.stat().st_size==row['deb_bytes']and sha(p)==row['deb_sha256']
 for name,row in manifest['entries'].items():
  p=R/row['path'];assert str(p.relative_to(prefix))==name;expected.add(name)
  if row['type']in ['regular','hardlink']:assert not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']and stat.S_IMODE(p.lstat().st_mode)==row['mode']
  elif row['type']=='symlink':assert p.is_symlink()and os.readlink(p)==row['target']
  else:assert stat.S_ISDIR(p.lstat().st_mode)and stat.S_IMODE(p.lstat().st_mode)==row['mode']
 actual=set()
 for parent,dirs,files in os.walk(prefix,followlinks=False):
  for name in dirs+files:actual.add(str((Path(parent)/name).relative_to(prefix)))
 assert expected<=actual
 extra={name:dict(type='implicit_directory',mode=stat.S_IMODE((prefix/name).lstat().st_mode))for name in sorted(actual-expected)}
 assert all(stat.S_ISDIR((prefix/name).lstat().st_mode)for name in extra),'UNMANIFESTED_NON_DIRECTORY'
 put(O/'FILESYSTEM_SUPPLEMENT.json',dict(passed=True,explicit_entries=len(expected),implicit_directories=extra,no_unmanifested_file_or_symlink=True,original_manifest_sha256=sha(O/'UNPACK_MANIFEST.json'),models=0,new_numerical_calls=0))
 frozen=read(R/'runs/v1694_shared_observation_closure/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 task=int(subprocess.check_output(['du','-sx','-B1',str(O)]).split()[0]);used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert task<224*1024**2 and used+(32+32+512)*1024**2<15*1024**3
 proof=dict(closed=True,passed=True,scope='EXACT_ROS_PACKAGE_DATA_RECOVERY_NO_PACKAGE_EXECUTION',owner_gone=True,source_SHA_exact=True,package_count=74,original_deb_bytes=packages['original_deb_bytes'],all_original_deb_SHA_size_verified=True,unpack_entries=len(expected),implicit_directory_count=len(extra),expanded_regular_content_bytes=manifest['expanded_regular_content_bytes'],all_unpacked_member_SHA_size_mode_link_verified=True,no_unmanifested_file_or_symlink=True,original_tar_uid_gid_retained_as_metadata_host_replication_not_claimed=True,all_originals_retained=True,task_allocated_bytes=task,allruns_bytes=used,remaining_external_dependency_groups=86,nonROS_transitive_closure_unresolved=True,ABI_or_build_qualified=False,package_executions=0,maintainer_scripts_executed=0,compiler_calls=0,optimizer_calls=0,models=0,physical_native=0,replay_native=0,method_executed=False,method_outcome=None,review_original=True,execution_idle=True,shared_frozen_members=len(frozen),all_shared_frozen_SHA_verified=True,runtime_recovery_pending=True,closure_numerical_calls=0,source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in [O/'RESULT.json',O/'ONCE_CLAIM.json',O/'PACKAGE_MANIFEST.json',O/'UNPACK_MANIFEST.json',O/'FILESYSTEM_SUPPLEMENT.json',P/'DEPENDENCY_PLAN.json',P/'POST_ROUND_STORAGE_BARRIER.json']},late_closure_helper_not_in_source_commit=True,closure_helper_sha256=sha(Path(__file__)))
 put(O/'RUNTIME_CLOSED_REVIEW.json',proof)
 report=R/'docs/NOETIC_PAYLOAD_INTAKE_V1706_REPORT.md';assert not report.exists()
 report.write_text(f'''# Exact ROS Noetic payload intake V1706

The74 ROS packages locked by the publisher-signed V1704 index were recovered exactly: {packages['original_deb_bytes']}B original .deb inputs, every size/SHA256 verified before static archive parsing. Original version/filenames are retained in PACKAGE_MANIFEST. The selected mirror is a byte carrier; the upstream ROS primary fingerprint, actualgpgv record and Release-to-Packages SHA chain are retained from V1704. No successful recovery claim for the earlier inaccessible official HTTPS endpoints.

Pure static Debian ar2.0/data.tar parsing completed with {len(expected)} explicit extracted entries, {len(extra)} implicit directories and {manifest['expanded_regular_content_bytes']}B expanded regular content. Every regular/hardlink byteSHA/size/mode and symbolic link literal was independently checked on closure; no unmanifested file or symlink. Original .debs and the extracted sysroot are retained. Host uid/gid replication is not claimed; original tar ownership is metadata. No package maintainer script, downloaded program/library, compiler, optimizer, model, physics or replay was executed.

Task allocation at closure {task}B<224MiB; allruns {used}B and original32MiBarchive/32MiBdownload/512MiBroot reserves remain within15GiB. Safe path/new ar parser software sample:3positive/8negative, not model or scientific work. Owner exited and original REVIEW/execution-idle/all14079sharedfrozenSHA verified. Closure only reads bytes/metadata, no numerical re-audit.

ROS payload data recovery is not TEB build, ABI, safety/navigation or comparative performance PASS.86nonROS dependency groups remain unresolved, including original-version Boost/OpenCV/SuiteSparse/Eigen/Python prerequisites. Original CMake exports also reference absolute /opt/ros/noetic and /usr paths; future build requires a separate, explicit namespace binding without modifying author source. The original missing-catkin configure/failures remain frozen, with no old case retry or new scientific denominator.

Source {claim['source_commit']} was pushed/refverified once before intake. This closure helper/report and upcoming dependency draft are later than that Git commit. V1707 firstruntimeRelease covers exact .deb payloads plus complete unpacked-member manifest and source/metadata; extracted sysroot is recoverable from those originals and explicitly not duplicated as archive members. Remote closure is recorded separately in POST_ROUND_STORAGE_BARRIER and REMOTE_RECOVERY_SUPPLEMENT when available; original pending review is not rewritten. No second push, reseal or automation restart.
''')
 p=R/'CURRENT_EXPERIMENT.json';current=read(p);current.update(status='NOETIC_ROS_PAYLOAD_CLOSED_PASS_NATIVE_DEPENDENCIES_UNRESOLVED_NO_MODELS',active_preparation=None,next_experiment=None,next_preparation='v1708_focal_dependency_resolution')
 current['latest_noetic_payload_intake']=dict(version='V1706',closed=True,passed=True,packages=74,original_deb_bytes=packages['original_deb_bytes'],unpack_entries=len(expected),all_member_SHA_verified=True,task_allocated_bytes=task,external_groups_unresolved=86,ABI_or_build_qualified=False,package_executions=0,models=0,method_executed=False,recovery_pending=True)
 p.write_text(json.dumps(current,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n')
 p=R/'docs/ALGORITHM_COMPARISON_COMPLETION_20261123.md';lines=p.read_text().splitlines();rows=[i for i,x in enumerate(lines)if x.startswith('|TEB|')];assert len(rows)==1
 lines[rows[0]]='|TEB|Original55authorfiles exact; signed Noetic74ROS packages recovered/SHA+unpackmanifest verified; originalconfigure missing-catkin result retained, optimizer/vehicle0|Resolve86nonROS groups and original absolute-path/ABI build binding, then vehicleclient; method UNEXECUTED|';p.write_text('\n'.join(lines)+'\n')
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f"\nV1706唯一74ROS原deb payload真正CLOSED datarecoveryPASS：{packages['original_deb_bytes']}B全签名索引SHA/size，纯ar/tar静态解包{len(expected)}explicitentries/{len(extra)}implicitdirs/{manifest['expanded_regular_content_bytes']}Bregularcontent，全SHA-size-mode-link及noextra文件核。实际task{task}B<224MiB/allruns{used}B+原恢复peak<15GiB，原deb/sysroot全留。0包脚本/程序/library/compiler/optimizer/model/physical/replay，86nonROSgroups/ABI/build仍无资格，不当TEB算法成功。owner已退出/REVIEW原/闲锁/14079sharedSHA核。V1707首次archive仅originaldeb+fullmembermanifest、不重复sysroot，fullremote/cleanupbarrier待做；lateclosehelper/report非5f39Git由Release成员SHA覆盖。下一V1708仅ASTdraftELF静态依赖reader，无entry/qual/once/sourcefreeze/model权限；旧失败/formal20保持/heartbeat删除。\n")
 print(json.dumps({k:proof[k]for k in ['passed','package_count','original_deb_bytes','unpack_entries','task_allocated_bytes','remaining_external_dependency_groups','models']}))
if __name__=='__main__':main()
