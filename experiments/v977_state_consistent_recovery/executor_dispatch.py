"""Pinned ROS callback executor: drain submitted handlers before guard destruction."""
import json
from pathlib import Path
class ConcurrentSpin:
    def __init__(self,rclpy,workers=3):
        from rclpy.executors import MultiThreadedExecutor
        if workers!=3:raise ValueError('FIXED_THREE_ROS_WORKERS')
        self.rclpy=rclpy;self.executor=MultiThreadedExecutor(num_threads=workers);self.original=None;self.node=None;self.closed=False
    def __enter__(self):
        self.original=self.rclpy.spin_once;self.rclpy.spin_once=self.spin_once;return self
    def spin_once(self,node,executor=None,timeout_sec=None):
        if self.closed:raise RuntimeError('DISPATCH_ALREADY_CLOSED')
        if executor is not None:raise RuntimeError('EXTERNAL_EXECUTOR_NOT_ALLOWED')
        if self.node is None:self.node=node;self.executor.add_node(node)
        if node is not self.node:raise RuntimeError('ONE_BRIDGE_NODE_ONLY')
        self.executor.spin_once(timeout_sec=timeout_sec)
    def close(self):
        if self.closed:return
        self.closed=True
        if self.original is not None:self.rclpy.spin_once=self.original
        # The pinned installed rclpy destroys its guard inside base shutdown,
        # before MultiThreadedExecutor joins submitted handlers. Let those
        # handlers finish while the node and guard are still alive.
        self.executor._executor.shutdown(wait=True)
        failures=[];completed=0
        for future in self.executor._futures:
            if future.done():
                completed+=1
                error=future.exception()
                if error is not None:failures.append(repr(error))
        closed=self.executor.shutdown(timeout_sec=2.,wait_for_threads=True)
        self.shutdown_report=dict(passed=closed and not failures,submitted_handlers_drained_before_guard=True,
                                  completed_futures_checked=completed,callback_errors=failures,models=0,integrations=0)
        if self.node is not None and hasattr(self.node,'motion'):
            (Path(self.node.motion.out)/'DISPATCH_SHUTDOWN.json').write_text(json.dumps(self.shutdown_report,indent=2)+'\n')
        if not self.shutdown_report['passed']:raise RuntimeError('ROS_CALLBACK_SHUTDOWN_FAILURE '+str(failures))
    def __exit__(self,*args):self.close()
