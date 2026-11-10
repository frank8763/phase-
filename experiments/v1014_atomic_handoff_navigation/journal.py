"""Bounded ordered snapshots; bulky JSON serialization never blocks ROS callbacks."""
import concurrent.futures,json
from pathlib import Path
class Journal:
    def __init__(self,path):self.path=Path(path);self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1);self.jobs=[]
    def _write(self,rows):
        temp=self.path.with_suffix('.tmp')
        with temp.open('w')as stream:json.dump(rows,stream,indent=2);stream.write('\n')
        temp.replace(self.path)
    def submit(self,rows):
        self.check();assert len(self.jobs)<32,'JOURNAL_FIXED_QUEUE_EXHAUSTED'
        # Row updates replace top-level fields. Nested plans/packets are immutable
        # after creation; snapshots therefore keep each submitted record version.
        self.jobs.append(self.pool.submit(self._write,[dict(row)for row in rows]))
    def check(self):
        for job in self.jobs:
            if job.done():job.result()
    def close(self):
        try:
            for job in self.jobs:job.result(timeout=5.)
        finally:self.pool.shutdown(wait=False,cancel_futures=True)
