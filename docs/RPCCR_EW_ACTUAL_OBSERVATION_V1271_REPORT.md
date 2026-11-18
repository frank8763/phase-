# V1271 EW槽17实际观测交接开发

主任务及完整重复全门通过=True；停止原因=JOINT_PHASE_18_19_MAIN_REPEATS_COMPLETE。
仅原18/19联合开发，科学修订为完整安全观察位置交接后，使用本轮实际雷达刷新原因果域再准入全程。原静态驾驶/发现/完整刹停、模型、课程与物理门不改；若新域仍拒绝，保持已证停车并完整重放/独审。
新90分钟双时钟为助手按既有有界惯例选择；旧V1248失败和旧截止不延，前16旧成功不计本批新确认。18–24与固定确认重复均未在本批执行。

|任务|功能|独审|实际原生|自身重放|错误/拒绝|
|---|---|---|---:|---:|---|
|slot18_main|True|True|51308|51308|None|
|slot18_repeat|True|True|51308|51308|None|
|slot19_main|True|True|51683|51683|None|
|slot19_repeat|True|True|51683|51683|None|

完整重复：`{"slot18": {"passed": true, "maximum_complete_state_ctrl_error": 0.0, "same_lengths": true, "initial_same": true, "model_same": true, "sensors_contacts_same": true}, "slot19": {"passed": true, "maximum_complete_state_ctrl_error": 0.0, "same_lengths": true, "initial_same": true, "model_same": true, "sensors_contacts_same": true}}`。
未执行：[]。
实际与未知计数：`{"models": 4, "historical_reconstruction_native": 0, "new_actual_native": 205982, "total_actual_model_native": 205982, "own_replay_native": 205982, "analytical_cpp_native": null, "analytical_python_native": null}`。普通预测未完整插桩，未知不填0。
CPU2idle/单实例/CPU OSMesa/GPU隐藏/2GiB，训练/Stage/实机0。REVIEW_PENDING恢复；原件远端未核验不删。有限已暴露课程开发不证明未见泛化、任意遮挡、多actor、实时或RAS优势。
