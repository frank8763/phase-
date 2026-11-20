# V1389 GitHub读重试与上传结果核对的纯I/O接续

V1388已核清理12组，实际runs约13.13GB；在v1217新资产上传前gh读取Release tag遇EOF后按旧合同退出，未核原件保持。旧源/CLAIM/ERROR与成功清理不变。此为传输修订，0科学轮/候选/模型/物理。

本版仅增加两项有界操作：只读GitHub API的明确EOF/TLS/超时/连接等瞬态错误最多3次尝试、退避2/4秒；上传调用不盲目重试，未知返回后先分页读取完整资产表，若同名size/SHA吻合则确认完成且不第二POST，若冲突立即拒绝，只有已核远端确实无该资产才最多第二次上传。第二次仍失败停止。单次API120s/上传300s与周一09点根限制不变，原Git一次push规则不变，不重试旧物理同步。

6项无网络写资格通过：只读EOF后成功/耗尽3次、写不盲试、未知POST但资产已存在则确认且不再上传、远端digest冲突拒绝、确认缺失后最多2POST。真实分页API列举及既有v1275.INDEX的远端size/digest核通过，无新写。

V1388的download/preserve/main/assets函数AST完全相同，沿用已验证4MiB 206/Content-Range、完整块SHA、全组重组/解压成员/恢复index、执行锁/源码SHA/REVIEW_PENDING/无活动轮、原SHA/mtime/inode/Git未跟踪清单清理门；不降低TLS验证/任何科学或内容门，不重下已核块、不重传已核资产，未核原件保留。当前唯一新增后台一次claim，不重启旧worker。全部结束才storage/FINALIZED及父storage_ready，10GiB减512MiB预留门仍硬守。CPU5/nice19线程1/GPU隐藏/低I/O、Stage隔离。
