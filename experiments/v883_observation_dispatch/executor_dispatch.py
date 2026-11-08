"""Dedicated ROS callback workers; original receipt freshness gates remain unchanged."""
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
        self.executor.shutdown(timeout_sec=2.,wait_for_threads=True)
    def __exit__(self,*args):self.close()
