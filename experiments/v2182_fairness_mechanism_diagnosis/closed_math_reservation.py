"""Read-only exact closed-band accounting; never mutate the inventoried root."""
import datetime,fcntl,hashlib,json,os,signal,stat,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
TARGET=R/'runs/v2184_fair_raw_controller_math';DEST=R/'runs/v2152_weekend_research_program/CLOSED_V2184_PREPARATION_BAND.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):assert p.stat().st_size<=2*1024**2;return json.loads(p.read_bytes())
def du(p):return int(subprocess.check_output(['du','-sx','-B1',str(p)],timeout=10).split()[0])
def inventory():
    rows=[]
    for p in sorted([TARGET,*TARGET.rglob('*')]):
        st=p.lstat();link=os.readlink(p)if stat.S_ISLNK(st.st_mode)else None
        assert stat.S_ISREG(st.st_mode)or stat.S_ISDIR(st.st_mode)or link is not None
        rows.append(dict(path=str(p.relative_to(R)),kind='symlink'if link is not None else'directory'if stat.S_ISDIR(st.st_mode)else'file',bytes=st.st_size,allocated=st.st_blocks*512,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,link=link,sha256=hashlib.sha256(link.encode()).hexdigest()if link is not None else sha(p)if stat.S_ISREG(st.st_mode)else None))
    return rows

def verify_existing(record):
    assert record['passed']and record['scope']=='IMMUTABLE_CLOSED_MATH_PREPARATION_RESERVATION_ONLY'
    assert inventory()==record['exact_inventory'],'CLOSED_BAND_CHANGED_REFUSE_NEW_ADMISSION'
    assert du(TARGET)==record['actual_closed_allocated_bytes']and du(TARGET)<=record['closed_preparation_charge_bytes']
    for p,h in record['closure_proof_SHA256'].items():assert sha(R/p)==h
    return record['closed_preparation_charge_bytes']

def main():
    assert os.sched_getaffinity(0)=={5}and not DEST.exists()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('CLOSED_BAND120S')));signal.alarm(120)
    assert du(DEST.parent)+du(R/'runs/v2181_combined_close_reservation')+24*1024<=2*1024**2
    locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    once=read(TARGET/'RUNTIME_ONCE.json');child=read(TARGET/'OWNED_CHILD.json');completion=read(TARGET/'COMPLETION.json')
    assert completion['closed']and completion['original_REVIEW_exact_restored']and completion['source_unchanged_after_exit']
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for identity in [once['owner_identity'],child]:
        p=Path('/proc',str(identity['pid']),'stat')
        assert identity['boot_id']!=boot or not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks'],'CLOSED_OWNER_STILL_ACTIVE'
    source=read(TARGET/'SOURCE_FULL_REMOTE_VERIFIED.json');runtime=read(TARGET/'RUNTIME_REMOTE_CLOSURE.json');recovery=read(TARGET/'CURRENT_SOURCE_REMOTE_RECOVERY.json');sync=read(TARGET/'SOURCE_SYNC_RESULT.json')
    assert source['passed']and source['every_block_member_whole_index_actual_remote_SHA']
    assert runtime['passed']and runtime['actual_remote_all_block_member_whole_index_SHA']and runtime['canonical_post_runtime_barrier']and runtime['exact_SHA_size_mtime_device_inode_cleanup_completed']
    assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['source_commit']==sync['head']==source['source_commit']
    assert sync['all_Git_members_actual_remote_SHA']and len(sync['actual_remote_Git_members_SHA256'])==19
    archived_members=0
    for proof in [source,runtime]:
        index=R/proof['index_path'];assert sha(index)==proof['index_sha256'];idx=read(index)
        assert idx['archive_sha256']==proof.get('archive_sha256',idx['archive_sha256'])
        for row in idx['files']:
            p=R/row['path'];assert p.is_file()and not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256'];archived_members+=1
    removed=read(TARGET/'SOURCE_TRANSPORT_CLEANUP.json')['removed']+[e['path']for e in runtime['cleanup_manifest']]
    assert all(not(R/n).exists()for n in removed)
    before=inventory();actual=du(TARGET);assert sum(r['allocated']for r in before)==actual
    charged=((actual+32767)//32768)*32768;old=352*1024;assert actual<=charged<old
    meta=sum(r['allocated']for r in before if r['kind']=='file'and Path(r['path']).relative_to(TARGET.relative_to(R)).parts[0]not in {'RUNTIME','SOURCE_TRANSPORT','RUNTIME_TRANSPORT'});assert meta==128*1024
    proofs=[TARGET/n for n in ['COMPLETION.json','SOURCE_FULL_REMOTE_VERIFIED.json','RUNTIME_REMOTE_CLOSURE.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','SOURCE_SYNC_RESULT.json','SOURCE_TRANSPORT_CLEANUP.json','v2184-source.INDEX.json','v2184-runtime.INDEX.json']]
    other=du(R/'runs/v2182_fairness_mechanism_diagnosis')+du(R/'runs/v2183_lossless_capture_stream')
    result=dict(passed=True,scope='IMMUTABLE_CLOSED_MATH_PREPARATION_RESERVATION_ONLY',created_at=datetime.datetime.now().astimezone().isoformat(),target=str(TARGET.relative_to(R)),exact_inventory=before,closure_proof_SHA256={str(p.relative_to(R)):sha(p)for p in proofs},archived_local_members_matching_prior_actual_remote_proofs=archived_members,no_new_HTTP_or_remote_qualification=True,actual_closed_allocated_bytes=actual,closed_preparation_charge_bytes=charged,original_live_stage_cap_unchanged_bytes=old,unused_live_stage_reservation_bytes=old-charged,closed_charge_granularity_bytes=32768,global_baseline_unchanged=14873092096,new_global_15GiB_credit_bytes=0,other_preparation_allocated_bytes=other,parallel_cap_bytes=1024**2,available_parallel_only_if_snapshot_exact=1024**2-other-charged,requires_fresh_inventory_match_before_each_new_admission=True,raw_inputs_anchors_deleted=0,original_models_queries_replays_audits_Source=0,helper_SHA256=sha(Path(__file__)),local_after26769=True)
    assert verify_existing(result)==charged and before==inventory()
    raw=json.dumps(result,indent=2).encode()+b'\n';assert len(raw)<=24*1024
    with DEST.open('xb')as f:f.write(raw)
    assert du(DEST.parent)+du(R/'runs/v2181_combined_close_reservation')<=2*1024**2
    print(json.dumps({k:result[k]for k in ['passed','actual_closed_allocated_bytes','closed_preparation_charge_bytes','unused_live_stage_reservation_bytes','new_global_15GiB_credit_bytes','available_parallel_only_if_snapshot_exact']}))
if __name__=='__main__':main()
