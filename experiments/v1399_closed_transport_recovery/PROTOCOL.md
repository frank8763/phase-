# V1399 闭合旧归档运输备份与精确清理

零模型I/O轮，不重启任何旧storage/delivery worker，不push任何旧科学批。仅原Phase已闭合gzip archive分块，原件未核不删。新同仓库Release `phase-closed-transport-recovery-20261120` 绑定已经远端核验的f35e30a01d64e9373f52566e4e1817e9d2783b6d，明确备份而非新科学成功。原旧归档index/CLAIM/ERROR/FINALIZED均不改。

每组先冻结原index/全部part SHA、mtime、inode，保护当前冻结来源和Git跟踪路径/同inode；只创建唯一组名前缀硬链接（不额外复制内容）。复用V1389有限只读/幂等上传/4MiB Range传输预算，每次最大32MiB下载，全部块实际下载SHA、gzip流全成员/链接文本与整流SHA、恢复index下载过才新proof。原完整成员SHA从旧本地归档index引用，不用当前原件替代归档原字节。

每组proof完成后执行锁内复核无活动轮/REVIEW_PENDING原字节/全部受保护source SHA/逐运输path的SHAmtimeinode与未跟踪清单，然后只删除该组已核重复运输part与对应硬链接；所有物理raw、预测数据、当前锚点、旧失败和恢复index保留。不得删除任何未核raw；本轮不会单独解决全部整路空间，完成后实际重算。root截止周一09:00、I/O单轮最多3h；本轮不新增科学模型预算。

实际启动前冻结计划/源码、流式gzip跨块及成员错SHA拒绝资格；单次后台CLAIM，CPU5/nice19/线程1/GPU隐藏、低I/O。网络有限恢复失败保存ERROR与未核原件，旧错误不追认。后台自行持有双钟截止，不依赖下次AI在线。
