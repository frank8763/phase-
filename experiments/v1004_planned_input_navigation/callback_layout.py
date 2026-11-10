"""Explicit ownership: serial reader; serial admission; independent diagnostics."""


class CallbackLayout:
    def __init__(self):
        from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
        self.observation = MutuallyExclusiveCallbackGroup()
        self.command = MutuallyExclusiveCallbackGroup()
        self.telemetry = MutuallyExclusiveCallbackGroup()
