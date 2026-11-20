# V1386 有界纯I/O断点接续

原V1382 storage worker首块32MiB回读300s下载29882944B后超时，原ERROR/CLAIM/源/PLAN与全部原始证据保持。不能重启原worker。本版只接续同PLAN、同Release；先核资产大小/服务器SHA和本地已完整块，完整块不再下，已上传正确块不再传。原部分块以HTTP Range接续，单资产最多一次900s，无无限重试；最多3并发下载，CPU5/nice19，不模型。

实际首块Range接续成功，33554432B完整SHA通过；完整错误SHA、过长本地块、既有远端冲突3负例零网络拒绝。每组只有全部块实际下载SHA、全解压成员SHA、重组SHA和恢复index下载SHA通过，才拿Phase执行锁、复核新旧冻源、确认REVIEW_PENDING及无活动轮、逐文件SHA/mtime/inode和Git未跟踪核后按原清单清理。来源/current/runtime/新执行输入均受原PLAN及本轮freeze保护。归档副本/下载副本仅验证后删；旧超时证据保留。

当前根截止2026-11-23 09:00/1795395600，依原V1382总授权，不新科学候选/不物理。目标runs<=8GiB，少于10GiB预留512MiB后写原尚不存在storage/FINALIZED和父storage_ready；这只存储准入，不是科学通过或自动launch。断点再失败则保留全部未核原件并暂停新物理。
