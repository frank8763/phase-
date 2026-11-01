# V694唯一初始化接续

原V694固定状态验证因预先out.mkdir而与冻结factory内部mkdir(exist_ok=False)冲突，在任何重放/私有预测前FileExistsError，原ERROR/COMPLETION保留。唯一修复去掉诊断预建目录，改名fixed73_setup_final，让原factory创建输出根；其他源/算法/门槛均相同。另立development02_setup_once，原V694开始和V69322:17:54.814截止、开发02计数均不改，记录wrapperSHA。候选源码仍冻结，不覆盖原失败。若实际前置失败，停止依赖导航并诊断，不再追加初始化修复。
