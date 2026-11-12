"""Reuse qualified single-repeat driver; add explicit current-boot identity."""
from pathlib import Path

R = Path(__file__).resolve().parents[2]
ORIGINAL = R/'experiments/v1086_ns_complete_repeat/campaign.py'

def patched_source():
    s = ORIGINAL.read_text()
    old = 'wall, mono = time.time(), time.monotonic()'
    assert s.count(old) == 1
    s = s.replace(old, "boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()\n    "+old)
    s = s.replace('duration_s=5400, old_windows_unchanged=True)', 'duration_s=5400, old_windows_unchanged=True, boot_id=boot)')
    old = "return min(window['absolute_deadline_unix']-time.time(), window['hard_stop_monotonic']-time.monotonic())"
    assert s.count(old) == 1
    s = s.replace(old, "assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == window['boot_id'], 'CROSS_BOOT_AUTHORITY_REJECTED'\n        "+old)
    s = s.replace('很好，下一步开始，加油', '好，开始').replace('V1086', 'V1087')
    return s

if __name__ == '__main__':
    exec(compile(patched_source(), str(ORIGINAL), 'exec'),
         dict(__name__='__main__', __file__=str(ORIGINAL)))
