# 第 24 章　常用 API 与术语速查

[上一章](23_独立开发训练与毕业考核.md) · [总目录](00_阅读地图与学习方法.md) · [下一章](25_练习提示与参考思路.md)

这一章用于“我知道要做什么，但忘了该找谁”。表中的签名是常用调用形式，不是所有重载。`None` 表示通常不返回业务结果；许多异步方法只发起操作，真正结果由之后的信号给出。完整重载、所有权、线程约束及版本变化需要查对应版本文档。

## 24.1 先分清五种东西

| 名称 | 例子 | 怎样使用 |
|---|---|---|
| 模块 | `PyQt6.QtWidgets` | 从模块导入类，不是窗口对象 |
| 类 | `QPushButton` | 调用构造方法得到对象 |
| 实例方法 | `button.setText("保存")` | 让一个对象现在执行操作 |
| 信号 | `button.clicked` | 用 `.connect(...)` 订阅，事情发生时接收通知 |
| 事件处理方法 | `closeEvent(self, event)` | 在子类中重写，由 Qt 分发事件后调用 |

`pyqtSignal` 是创建自定义信号描述的工具，通常作为 `QObject` 子类的类属性声明；`pyqtSlot` 是装饰器，给方法声明 Qt 槽签名。普通 Python 方法也常能连接信号，但跨线程接收建议使用正确线程中的 `QObject` 槽，明确对象归属。

## 24.2 窗口与布局

下表的 `box` 指 `QVBoxLayout` 或 `QHBoxLayout`，`stack` 指 `QStackedWidget`。网格布局的 `addWidget()` 还需要行列位置，表单布局通常使用 `addRow()`；不能把某一种布局的方法签名套到所有布局上。

| 常用形式 | 输入与结果 | 注意点 |
|---|---|---|
| `QApplication(argv)` | 参数列表 → 应用对象 | 创建 QWidget 前创建，进程内保持一个应用实例 |
| `app.exec()` | 无额外参数 → 整数退出码 | 进入事件循环，退出后返回，不是永不结束 |
| `widget.show()` / `hide()` | 显示/隐藏，通常返回 None | 隐藏不等于删除 |
| `widget.close()` | 请求关闭 → bool | 可被关闭事件拒绝；接受关闭不一定销毁对象 |
| `resize(width, height)` | 两个整数 → None | 改变当前尺寸，不锁定尺寸；受布局和尺寸约束影响 |
| `setMinimumSize(w, h)` | 下限 → None | 比固定所有尺寸更适合适配 |
| `setEnabled(bool)` | 可用状态 → None | 禁用不等于隐藏 |
| `QVBoxLayout(parent_widget)` | 容器 → 布局对象 | 会把布局安装到该容器，不再重复 setLayout |
| `box.addWidget(widget, stretch=0)` | 控件和伸展比例 → None | 伸展分配还受最小尺寸与 sizePolicy 影响 |
| `box.addLayout(child_layout)` | 子布局 → None | 嵌套布局描述区域关系 |
| `box.addStretch(1)` | 伸展项 → None | 常用来把按钮推到一端 |
| `setContentsMargins(l,t,r,b)` | 四个边距 → None | 区别于控件之间的 spacing |
| `QFormLayout.addRow(label, field)` | 标签和字段 → None | 表单常比手算坐标更适合 |
| `main.setCentralWidget(widget)` | 中央容器 → None | QMainWindow 自己已有专用布局 |
| `stack.addWidget(page)` | 页面 → 页面索引 int | 切换后并非销毁其他页面 |
| `stack.setCurrentIndex(index)` | 页面索引 → None | 索引需要与你的导航映射一致 |

## 24.3 输入、输出和信号

| 类与方法 | 取得/设置的值 | 常用信号与陷阱 |
|---|---|---|
| `QLineEdit.text()` / `setText(str)` | 字符串 | `textChanged(str)` 含代码修改；`textEdited(str)` 主要针对用户编辑 |
| `QLineEdit.setPlaceholderText(str)` | 输入提示 | 提示不是实际值，仍需读 text |
| `QLineEdit.returnPressed` | 回车通知，无参数 | 安装验证器时，输入状态会影响发送 |
| `QLabel.setText(str)` | 展示文本 | 默认可能按富文本推断；显示不可信纯文本时设 PlainText |
| `QPushButton.clicked` | 点击通知，通常带 bool | `connect(handler)`，不要写 `handler()` |
| `QCheckBox.isChecked()` | bool | 三态时如需区分中间态，使用 checkState |
| `QCheckBox.toggled(bool)` | 是否勾选 | 程序 setChecked 也可能触发 |
| `QComboBox.currentText()` | 展示文字 str | 业务身份最好取 currentData |
| `QComboBox.addItem(text, userData)` | 加选项 | `currentIndexChanged(int)` 包括代码改动 |
| `QSpinBox.value()` | int | `setRange(min,max)` 限制整数范围；`valueChanged(int)` |
| `QDoubleSpinBox.value()` | float | 精度、范围与显示小数位需明确 |
| `QPlainTextEdit.toPlainText()` | 完整文本 str | 大日志可限制最大块数，避免无限增长 |
| `appendPlainText(str)` | 追加段落 → None | 会增加段落边界，不适合精确保留每个输出分片 |
| `QProgressBar.setValue(int)` | 进度数值 | 先设范围；进度未知可以用忙碌指示 |

控件的验证器用于限制编辑过程，提交时仍要执行业务验证。例如“两个端口不能相同”不是单个 `QSpinBox` 的范围设置可以解决的。

## 24.4 对话框、动作和设置

| 常用形式 | 返回或通知 | 需要记住 |
|---|---|---|
| `QFileDialog.getOpenFileName(...)` | `(文件名, 过滤器)` | 取消通常得到空文件名，先判断再读文件 |
| `QFileDialog.getSaveFileName(...)` | `(文件名, 过滤器)` | 返回路径不代表已经保存成功 |
| `QMessageBox.question(...)` | `StandardButton` | 显式设置按钮集合与安全默认按钮 |
| `dialog.exec()` | `DialogCode` 对应的整数结果 | 模态并进入局部事件循环；检查 Accepted/Rejected |
| `dialog.open()` | 立即返回 | 异步模态使用 finished/accepted 等信号；保留对象 |
| `dialog.show()` | 立即返回 | 通常用于非模态；模态性还取决于窗口设置 |
| `QAction(text, parent)` | 可复用操作对象 | 从 QtGui 导入，可放菜单和工具栏 |
| `action.triggered` | 通常带 bool | 不是默认没有参数的信号 |
| `QSettings.value(key, default, type=...)` | 读取值 | 明确类型，例如 bool，避免字符串真假混乱 |
| `QSettings.setValue(key, value)` | 提交设置 | 必要时 sync 后检查 status；不等于事务数据库 |
| `QStandardPaths.writableLocation(type)` | 路径字符串 | 可能为空，目录可能尚未创建，按平台处理 |

## 24.5 列表与模型

| API | 作用 | 返回/使用边界 |
|---|---|---|
| `QListWidget.currentItem()` | 当前条目 | 可能是 None |
| `item.setData(UserRole, value)` | 存业务编号等额外数据 | 不要从显示文字反向解析身份 |
| `QTableWidget.item(row,col)` | 取表格条目 | 单元格可能尚未创建，返回 None |
| `view.setModel(model)` | 设置数据来源 | 模型对象要保持有效，不等于视图接管全部所有权 |
| `index.isValid()` | 判断模型索引是否有效 | 不保证删除/重置后旧索引永远可用 |
| `model.rowCount(parent)` | 提供行数 | 平面表对有效 parent 通常返回 0 |
| `model.columnCount(parent)` | 提供列数 | 同上，需要符合模型层次约定 |
| `model.data(index, role)` | 返回指定用途的数据 | 未支持的 role 通常返回 None |
| `model.setData(index,value,role)` | 尝试写入 → bool | 成功后发 dataChanged，不能只改 Python 列表 |
| `model.flags(index)` | 可选、可用、可编辑等标志 | 仅返回可编辑标志还不够，仍需 setData |
| `beginInsertRows(...)` / `endInsertRows()` | 通知结构插入 | 把真正数据变更夹在这两个调用之间 |
| `beginRemoveRows(...)` / `endRemoveRows()` | 通知结构删除 | 行号必须对应源模型当前状态 |
| `proxy.mapToSource(index)` | 代理索引 → 源模型索引 | 排序筛选后操作源数据前常需要它 |
| `proxy.mapFromSource(index)` | 源索引 → 代理索引 | 被过滤记录可能没有有效代理索引 |

`DisplayRole` 告诉视图怎样展示，`EditRole` 提供编辑使用的值，`CheckStateRole` 提供勾选状态，`UserRole` 及后续角色可存应用自己的数据。角色是“用途”，不是另外一张数据表。

## 24.6 事件、线程、进程和网络

| API | 实际含义 | 不要误解成 |
|---|---|---|
| `QTimer.start(ms)` | 安排周期性超时 | 到点一定精确执行或自动开线程 |
| `QTimer.singleShot(ms, callback)` | 安排一次回调 | 睡眠或后台工作线程 |
| `event.accept()` / `ignore()` | 表达对当前事件的处理决定 | 所有事件都具有相同默认语义 |
| `eventFilter(obj,event)` 返回 True | 拦截本次事件 | “继续传递”；继续通常返回 False/基类结果 |
| `worker.moveToThread(thread)` | 改变对象线程归属 | 之后直接调用 worker.method 就自动跨线程 |
| `thread.start()` | 启动线程执行 | 当前行等待任务完成 |
| `requestInterruption()` | 设置协作中断请求 | 强制终止任意阻塞调用 |
| `thread.quit()` | 请求线程事件循环退出 | 中断正在执行的长槽函数 |
| `QObject.deleteLater()` | 安排延迟删除 | 立即释放，或退出后无条件保证仍能处理 |
| `QProcess.start(program,args)` | 发起启动 | 证明子进程已经成功运行 |
| `QProcess.started` / `finished` | 启动/退出通知 | 应用业务服务已完全就绪/业务一定成功 |
| `readAllStandardOutput()` | 读取当前可用字节 | 一定是一行、一个完整字符或全部最终输出 |
| `process.terminate()` / `kill()` | 请求结束/强制结束 | 子进程树所有后代都会自动彻底清理 |
| `manager.get(request)` | 立即返回 QNetworkReply | 立即返回 HTTP 正文 |
| `reply.finished` | 本次回复结束 | 一定成功；仍需检查错误和 HTTP 状态 |
| `reply.abort()` | 中止请求 | 可以立刻忘掉对象，不再收尾 |

## 24.7 常见术语翻译

| 术语 | 用简单语言理解 |
|---|---|
| 事件循环 | 不断接收和分发输入、绘制、定时、异步结果的调度过程 |
| 回调 | 把函数交给别的代码，让它在合适时机调用 |
| 对象所有权 | 谁负责在何时销毁这个对象 |
| 线程归属 | QObject 的事件和排队槽通常在哪个线程的事件循环中处理 |
| 阻塞 | 当前执行路径停着等待，不能继续处理别的事情 |
| 异步 | 先发起并返回，稍后通过回调或信号接收结果 |
| 模型 | 用统一接口向视图提供数据与变更通知 |
| 视图 | 把模型数据画出来并接受用户交互 |
| 委托 | 决定单元格怎样绘制、用什么编辑器和怎样提交编辑 |
| 代理模型 | 在原模型外面增加排序、过滤等转换的一层 |
| 序列化 | 把内存对象变成可保存、可传输的格式 |
| 依赖注入 | 创建对象时把它需要的服务传进去，便于替换和测试 |
| 重入 | 一段逻辑尚未结束时，又通过事件等途径进入相关逻辑 |
| 最小复现 | 保留导致问题的最少代码、输入和操作步骤 |

## 24.8 怎样读官方文档

先确定类属于哪个模块，再读职责描述和继承关系；然后查方法参数、返回值、信号和注意事项。只看函数名容易忽略所有权、线程或异步限制。

Qt 文档通常以 C++ 为主。`QString` 在 PyQt 中通常表现为 `str`，`QByteArray` 可转成 `bytes`，C++ 的枚举在 PyQt6 常写成完整的作用域形式，例如 `Qt.AlignmentFlag.AlignCenter`。C++ 中通过引用输出的参数，有时在 Python 中变成返回元组；不要照着 C++ 签名猜 Python 调用。

本机快速检查：

```powershell
python -c "from PyQt6.QtWidgets import QFileDialog; print(QFileDialog.getOpenFileName.__doc__)"
python -c "from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, qVersion; print(PYQT_VERSION_STR, QT_VERSION_STR, qVersion())"
```

第一条打印本机 Python 绑定的签名。第二条分别打印 PyQt 版本、构建时 Qt 版本和实际运行时 Qt 版本；它们不一定全部相等。命令使用的解释器必须与你运行程序的解释器一致。

建议收藏这些官方入口。它们是继续学习的资料入口，不代表本书覆盖其中全部内容：

- [Riverbank PyQt6 文档](https://www.riverbankcomputing.com/static/Docs/PyQt6/)：Python 绑定、信号槽、工具与差异。
- [Qt 6 类索引](https://doc.qt.io/qt-6/classes.html)：按类查职责、继承、函数和信号。
- [Qt Widgets](https://doc.qt.io/qt-6/qtwidgets-index.html)：桌面控件体系。
- [Qt 模型视图](https://doc.qt.io/qt-6/model-view-programming.html)：模型、视图、委托与索引。
- [Qt 线程与 QObject](https://doc.qt.io/qt-6/threads-qobject.html)：线程归属、事件循环与通信。
- [Qt 样式表参考](https://doc.qt.io/qt-6/stylesheet-reference.html)：支持的 QSS 选择器和属性。
- [Python 标准库](https://docs.python.org/3.12/library/)：pathlib、json、logging、unittest、sqlite3 等。
- [PyInstaller 文档](https://pyinstaller.org/en/stable/)：打包选项、运行环境与常见故障。

当文档与网上例子冲突时，先核对 PyQt5/PyQt6、PySide/PyQt 和 Qt 版本。抄对类名但用错版本的枚举或信号，也是常见错误来源。
