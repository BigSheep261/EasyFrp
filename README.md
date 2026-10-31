# EasyFrp

A Windows desktop controller for FRP, built with Python and PyQt6.

EasyFrp 仅提供 frpc 客户端和 frps 服务端的手动进程控制。两个控制页通过左侧标签切换，各自展示进程状态并提供启停按钮。实际隧道通信由独立的 FRP 可执行文件完成。

## 当前功能

- 手动启动、停止 frpc 和 frps。
- 展示未运行、启动中、运行中和停止中状态。
- 在对应页面的状态标签中提示启动失败、异常退出等进程错误。
- 关闭主窗口时停止应用管理的 FRP 进程。

界面中的“运行中”表示 FRP 子进程已经启动，不代表服务器连接成功或隧道已经可用。EasyFrp 不编辑或校验 TOML 配置，也不自动启动 FRP；配置需要使用外部编辑器准备。应用不采集、展示或保存进程输出，`logs/` 文件夹保留。FRP 自身的文件日志仍由 TOML 配置决定。

## 环境要求

- Windows 10 / 11。
- 推荐使用 Python 3.12 或更新版本；也可以参考 [Conda 环境说明](miniconda_env/miniconda_init.md)。
- 支持 TOML 配置的 Windows 版 FRP，配置字段应与 FRP 版本匹配。

Python 依赖见 [requirements.txt](requirements.txt)：

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| PyQt6 | 6.11.0 | 桌面界面、Qt 事件循环和异步进程控制 |
| PyInstaller | 6.21.0 | 打包 Windows 可执行程序 |

## 快速开始

以下命令在项目根目录的 PowerShell 中执行。

### 1. 创建环境并安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

也可以参考 [environment.yml](miniconda_env/environment.yml) 准备 Conda 环境。

### 2. 准备 FRP 程序和配置

从 [FRP 官方 Releases](https://github.com/fatedier/frp/releases) 下载匹配系统架构的 Windows 版本，将程序和配置放到：

```text
runtime/
├── frpc.exe
└── frps.exe
config/
├── frpc.toml
└── frps.toml
```

FRP 可执行文件不随 Git 仓库提供。只使用其中一个控制页时，只需准备对应的程序和配置。

首次启动 EasyFrp 会创建缺失的运行目录和空 TOML 文件，已有文件不会被覆盖。请用外部编辑器填写配置后，再在控制页点击启动按钮。空文件只用于占位，不表示 FRP 已配置完成。

### 3. 启动并手动控制

```powershell
.\.venv\Scripts\python.exe main.py
```

在左侧标签中选择“frpc 控制”或“frps 控制”，点击“启动 frpc”或“启动 frps”。进程启动后，按钮变为停止入口。修改运行中的 TOML 配置后，需要停止并重新启动对应进程。

两个页面的进程独立管理；切换页面不会停止已启动的进程。

## 路径约定

源码运行时，路径相对于项目根目录；打包运行时，相对于 EasyFrp 可执行文件所在目录。

| 路径 | 用途 |
| --- | --- |
| `runtime/frpc.exe` | frpc 可执行文件 |
| `runtime/frps.exe` | frps 可执行文件 |
| `config/frpc.toml` | 通过 `-c` 参数交给 frpc 的配置文件 |
| `config/frps.toml` | 通过 `-c` 参数交给 frps 的配置文件 |
| `logs/` | 保留的预留目录，应用不向其中写入日志 |

FRP 子进程的工作目录设为对应可执行文件所在目录，因此 TOML 中的相对路径应按该目录理解。

## 项目结构

```text
src/frp_gui/
├── app.py                       # 初始化运行目录与 Qt 应用
├── backend/
│   ├── frpc/process_service.py   # frpc 进程生命周期、状态和错误提示
│   └── frps/process_service.py   # frps 进程生命周期、状态和错误提示
├── ui/
│   ├── main_window.py           # 两个固定控制入口和退出清理
│   └── pages/
│       ├── frpc_control_view.py # 客户端手动控制和状态展示
│       └── frps_control_view.py # 服务端手动控制和状态展示
└── utils/paths.py               # 应用路径与空 TOML 初始化
```

页面直接组织 Qt 原生控件，通过后端服务操作进程。QProcess 的状态和错误信号驱动界面更新；标准输出和标准错误直接丢弃。

## 验证

启动界面后检查两个控制页的切换、启停按钮和状态标签。主窗口没有状态栏，启动失败和异常退出提示显示在对应页面的状态标签中。完整进程验证需要提前准备 FRP 程序和 TOML 配置。

## 打包发布

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name EasyFrp --paths src main.py
```

输出程序为 `dist/EasyFrp.exe`。无需打包内置配置资源；将 FRP 可执行文件放到它旁边的 `runtime/` 目录，并准备 `config/` 下的 TOML 配置。请选择可写目录存放程序。

发布前仍需在目标 Windows 环境验证程序启动、FRP 手动启停、状态提示和退出清理。

## 学习文档

- [学习路线](docs/学习路线.md)
- [PyQt6 模块详解与实战指南](docs/PyQt6模块详解与实战指南.md)
- [PyQt6 教材阅读地图](docs/Book/00_阅读地图与学习方法.md)
- [从教材走进 EasyFrp 源码](docs/Book/26_从教材走进EasyFrp源码.md)

## 第三方组件与许可证

- [FRP](https://github.com/fatedier/frp)：实际的内网穿透与转发程序，采用 Apache License 2.0。EasyFrp 仅提供图形化进程控制，与 FRP 官方项目无直接关联。
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)：桌面界面与 Qt 绑定。
- [PyInstaller](https://pyinstaller.org/)：将 Python 应用打包为独立程序。

本项目采用 [Apache License 2.0](LICENSE)。第三方组件遵循各自许可证。

Copyright (c) 2026 大羊
