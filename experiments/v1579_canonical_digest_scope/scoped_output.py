"""Compose original bounded writers without exposing writable descriptors.

Child admission is charged to both the original root and child counters. The
root interceptor is paused only while the original child interceptor owns I/O.
Persistent child handles cannot write outside that owned activation.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import threading
from types import MethodType

R = Path(__file__).resolve().parents[2]
ORIGINAL = R/'experiments/v1436_pathlib_control_rename'


class Scope:
    def __init__(self, *, parent, folder, writers, io, maximum_bytes, source_identity):
        assert parent.saved is not None and not parent.busy
        assert Path(type(parent).__enter__.__code__.co_filename).resolve() == ORIGINAL/'bounded_io.py'
        assert Path(writers.WriterBudget.reserve.__code__.co_filename).resolve() == ORIGINAL/'writer_budget.py'
        assert Path(io.OutputBoundary.__enter__.__code__.co_filename).resolve() == ORIGINAL/'bounded_io.py'
        self.parent = parent
        self.folder = Path(folder).resolve()
        assert self.folder.is_relative_to(parent.output) and self.folder.is_dir()
        assert not Path(folder).is_symlink()
        self.owner = os.getpid(), threading.get_ident()
        self.depth = 0
        self.failed = False
        # Original counters/lock are created under the trusted constructor,
        # never by handing an unknown writer a raw descriptor. Their initial
        # metadata allocation is debited before the constructor runs.
        self._root_charge(self.folder/'WRITER_PLANNER_BYTES.json', 32768)
        parent.busy = True
        try:
            self.writer = writers.WriterBudget(self.folder, role='PLANNER',
                maximum_bytes=maximum_bytes, source_identity=source_identity)
        finally:
            parent.busy = False
        scope = self
        def reserve(writer, path, size):
            assert scope.depth > 0 and scope.owner == (os.getpid(), threading.get_ident()), 'CHILD_SCOPE_NOT_ACTIVE'
            assert not scope.failed, 'CHILD_SCOPE_POISONED'
            try:
                # Counter replacement writes bypass the child interceptor's
                # recursion guard. Account an upper bound at the root before
                # invoking the unchanged original counter implementation.
                counter_size = writer.path.stat().st_size
                assert counter_size <= 128*1024, 'CHILD_COUNTER_METADATA_CAP'
                scope._root_charge(Path(path), int(size) + 2*counter_size + 16384)
                return writer.reserve(path, size)
            except BaseException:
                scope.failed = True
                raise
        self.boundary = io.OutputBoundary(self.folder, MethodType(reserve, self.writer))

    def _root_charge(self, path, size):
        assert self.owner == (os.getpid(), threading.get_ident())
        previous = self.parent.busy
        self.parent.busy = True
        try:
            self.parent.path(path)
            return self.parent.reserve(path, size)
        finally:
            self.parent.busy = previous

    @contextmanager
    def activate(self):
        assert self.owner == (os.getpid(), threading.get_ident()), 'CHILD_SCOPE_OWNER_CHANGED'
        assert not self.failed, 'CHILD_SCOPE_POISONED'
        if self.depth:
            self.depth += 1
            try:
                yield self.boundary
            finally:
                self.depth -= 1
            return
        assert self.parent.saved is not None and not self.parent.busy, 'SIBLING_SCOPE_OR_INACTIVE_ROOT'
        self.parent.busy = True
        self.depth = 1
        try:
            with self.boundary:
                yield self.boundary
        finally:
            self.depth = 0
            self.parent.busy = False


def scoped(method):
    """Apply an existing Scope around a sink callback, including nested saves."""
    def call(self, *args, **kwargs):
        with self.scope.activate():
            return method(self, *args, **kwargs)
    return call
