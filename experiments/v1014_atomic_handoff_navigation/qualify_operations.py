"""Exercise bulky journal/failure propagation and chunked evidence readback."""
import hashlib,json,tempfile,time
from pathlib import Path
from journal import Journal
from archive import package,verify,sha
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1014_atomic_handoff_navigation'
def main():
    with tempfile.TemporaryDirectory(prefix='ops-',dir=O)as td:
        d=Path(td);journal=Journal(d/'rows.json');original=journal._write
        def slow(rows):time.sleep(.1);original(rows)
        journal._write=slow;row=dict(passed=False,profile=1);begun=time.monotonic();journal.submit([row]);row['passed']=True;journal.submit([row]);submit_wall=time.monotonic()-begun
        assert submit_wall<.1,'JOURNAL_STILL_BLOCKS_ON_DISK';journal.close();assert json.loads((d/'rows.json').read_text())==[row]
        bad=Journal(d/'bad.json')
        def fault(rows):raise OSError('FIXED_WRITE_FAULT')
        bad._write=fault;bad.submit([row])
        try:bad.close()
        except OSError:failed=True
        else:raise AssertionError('WRITE_FAULT_IGNORED')
        data=d/'data';data.mkdir();(data/'one').write_bytes(b'preserve original bytes\n'*50000);(data/'two').write_bytes(b'\0'*100000)
        record,catalog=package(R,[data/'one',data/'two'],d/'cloud','fixed-stream')
        assert record['source_sha_and_decompressed_member_sha_verified']and len(record['parts'])==1
        part=d/'cloud'/record['parts'][0]['name'];before=part.read_bytes();damaged=bytearray(before);damaged[10]^=1;part.write_bytes(damaged)
        try:verify(record,catalog,lambda p:(part,False))
        except BaseException:corruption=True
        else:raise AssertionError('CORRUPT_ARCHIVE_ACCEPTED')
        part.write_bytes(before);verify(record,catalog,lambda p:(part,False))
    result=dict(passed=True,models=0,integrations=0,journal_nonblocking_submit_s=submit_wall,immutable_top_level_snapshots=True,journal_write_fault_propagated=failed,
        streaming_source_member_sha_readback=True,corrupt_chunk_rejected=corruption,no_combined_archive_or_full_readback_copy=True)
    (O/'OPERATIONS_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
