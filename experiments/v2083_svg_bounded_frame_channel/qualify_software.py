from pathlib import Path
import copy, hashlib, importlib.util, json, os, subprocess

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    O.mkdir();out=O/'fixture';out.mkdir();assert not(O/'RESULT.json').exists()
    source=R/'runs/v2079_svg_file_bound_transport/actual/SVG_CURRENT_SOLVER_FRAME.json'
    source_sha=sha(source);frame=json.loads(source.read_text())
    transport=load('bounded_local_frame_channel',C/'channel.py')
    path=R/'experiments/v1436_pathlib_control_rename/bounded_io.py';boundary_sha=sha(path)
    boundary=load('unchanged_real_frame_output_boundary',path);rejected=[]
    def reject(label,fn):
        try:fn()
        except AssertionError:rejected.append(label)
        else:raise AssertionError('EXPECTED_CHANNEL_REFUSAL:'+label)
    charges=[]
    def reserve(path,size):charges.append(size);assert sum(charges)<=128*1024
    # Explicit fixture echo: no numerical imports or consumption by a plant.
    script="import sys,hashlib,json\nfor i,line in enumerate(sys.stdin.buffer):\n assert len(line)<=1048576\n print(json.dumps(dict(sequence=i,bytes=len(line),sha256=hashlib.sha256(line).hexdigest())),flush=True)"
    channel=transport.FrameChannel(maximum_frames=2);peer=None
    try:
        with boundary.OutputBoundary(out,reserve):
            peer=subprocess.Popen(['/usr/bin/python3','-I','-B','-S','-c',script],stdin=channel.child.fileno(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            channel.detach_child_endpoint()
            sent=[]
            for value in [frame,dict(kind='EXPLICIT_SECOND_SOFTWARE_FRAME',current_frame=frame)]:
                proof=channel.send(value);sent.append(proof)
                reject('concurrent_pending_request',lambda:channel.send(value))
                received=json.loads(peer.stdout.readline())
                assert received==proof
                reject('wrong_frame_ack',lambda:channel.acknowledge(dict(proof,sha256='0'*64)))
                channel.acknowledge(received)
            reject('message_count_cap',lambda:channel.send(frame))
            channel.finish_input();peer.wait(timeout=5)
            assert peer.returncode==0 and not peer.stderr.read()
            reject('original_raw_writable_descriptor_still_blocked',lambda:__import__('io').open(12345678,'wb'))
        buffers=channel.kernel_buffers
    finally:
        if peer is not None and peer.poll()is None:peer.terminate();peer.wait(timeout=5)
        channel.close()
    reject('closed_channel',lambda:channel.send(frame))
    huge=transport.FrameChannel(maximum_frames=1)
    try:
        reject('frame_size_cap',lambda:huge.send(dict(data='x'*(1024**2))))
        reject('poisoned_after_failed_frame',lambda:huge.send(frame))
    finally:huge.close()
    foreign=transport.FrameChannel(maximum_frames=1)
    try:
        pid=foreign.pid;foreign.pid=-1
        reject('foreign_owner',lambda:foreign.send(frame));foreign.pid=pid
    finally:foreign.close()
    assert sha(source)==source_sha and sha(path)==boundary_sha
    value=dict(closed=True,software_passed=True,saved_input_source_sha256=source_sha,actual_two_frame_byte_SHA_equal=True,
               sent_frames=sent,total_transport_bytes=sum(x['bytes']for x in sent),kernel_socket_buffers=buffers,
               persistent_map_transport_file_bytes=0,original_output_boundary_unchanged=True,negative_cases=rejected,
               new_production_peer_qualified=False,persistent_optimizer_qualified=False,formal_method_admitted=False,
               models=0,optimizer_calls=0,physics=0,replay=0,formal_slots=0,
               source_hashes={str(p.relative_to(R)):sha(p)for p in [C/'channel.py',C/'qualify_software.py',path,source]})
    (O/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))

if __name__=='__main__':main()
