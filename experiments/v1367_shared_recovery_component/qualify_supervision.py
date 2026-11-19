"""Exercise both peer-exit paths without workers, models or real waiting."""
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from component_context import *
import worker_monitor as worker


class Peer:
    def __init__(self, exited):self.returncode=0 if exited else None;self.pid=-1
    def poll(self):return self.returncode


def main():
    clock=[0.];clock_api=worker.time
    records=[]
    try:
        for first in ['ros','native']:
            ros,native=Peer(first=='ros'),Peer(first=='native')
            with TemporaryDirectory(dir=O,prefix='monitor_fixture_') as folder:
                out=Path(folder)
                def sleep(_):
                    expected=out/('STOP_AFTER_CURRENT_PREFIX.json' if first=='ros' else 'PEER_STOP_REQUEST.json')
                    assert expected.exists(),'WRONG_PEER_EXIT_HANDOFF'
                    assert not (out/('PEER_STOP_REQUEST.json' if first=='ros' else 'STOP_AFTER_CURRENT_PREFIX.json')).exists()
                    clock[0]+=.15;ros.returncode=native.returncode=0
                worker.time=SimpleNamespace(monotonic=lambda:clock[0],sleep=sleep)
                proof=worker.monitor([ros,native],out,remaining=lambda:100.,storage_check=lambda:True)
                assert proof['drain_requested']==(first=='ros')
                assert proof['cooperative_ros_close_requested']==(first=='native')
                records.append(dict(first_exit=first,passed=True,proof=proof))
        tree=ast.parse((C/'campaign.py').read_text())
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='monitor']
        assert len(calls)==1 and ast.unparse(calls[0].args[0])=='[peer, native]'
    finally:worker.time=clock_api
    proof=dict(passed=True,checks=records,production_caller_uses_ros_native_order=True,models=0,physical_native=0)
    dump(O/'SUPERVISION_QUALIFICATION.json',proof);print(json.dumps(proof))


if __name__=='__main__':main()
