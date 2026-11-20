# V1405 旧zstd归档与淘汰资格缓存恢复清理

新零模型I/O计划，旧V1382/86/87/88/89/1399/1400/1401 worker均不重启，所有错误/冻源保持。仅V1122/V1121已闭合本地zstd归档与其已纳入完整归档的V1122/offline淘汰软件资格缓存，保护当前所有freeze、Git跟踪路径/同inode、当前输入和最后失败/成功物理锚点。新增本地计划按每文件SHA/mtime/inode冻结；任何raw不在该归档inventory或SHA不一致则不纳入，不搜索其它目录扩大清理。

32MiB原part上传同Phase新Release phase-closed-zstd-cache-recovery-20261121，绑定已确认远端17813a5f，不重push旧轮。复用V1389有限幂等上传/范围传输；每资产正确已在则size/digest核后跳过，不覆盖。逐32MiB实际下载SHA送原zstd流验证器，全部解压成员SHA、整流重组SHA与恢复index下载SHA通过，锁内再核父无active_round/REVIEW_PENDING原字节/保护源SHA/逐文件清单和未跟踪后，才精确清对应旧运输与淘汰offline软件资格缓存；不触碰物理raw/当前锚点或未核原件。每次最多32MiB下载+4MiB范围scratch，全部临时计10GiB。

原zstd恢复函数沿用旧本地归档实际资格版本，先对真实zstd跨part/成员及改SHA负例资格，0模型；新worker一次后台CLAIM，CPU5/nice19/低I/O，最多3h双钟/root周一09:00。网络在原有限预算内自恢复静默，无法恢复保留未核原件并停止，不自动无限接续。
