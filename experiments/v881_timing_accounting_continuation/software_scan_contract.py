"""Only synthetic/stationary SOFTWARE fixtures: continuous20Hz source, no physical sensor mutation."""
def publish_scan(last_tick,tick,last_publication,now,waiting):
 return bool(tick!=last_tick or waiting or now-last_publication>=.05)
