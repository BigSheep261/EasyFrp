# EasyFrp

A Windows desktop manager for FRP, built with Python and PyQt6.

EasyFrp 是一个基于 Python 和 PyQt6 开发的 Windows 桌面工具，用于管理 FRP 客户端（frpc）与服务端（frps）的配置、进程启停和实时输出。

项目目前处于开发阶段，已接通基础进程控制和部分配置功能。frpc 的表单化配置、多配置选择与组合启动仍在完善，当前使用时还需要准备 TOML 配置文件。实际隧道通信由独立的 FRP 可执行文件完成。

## 当前功能

| 功能 | 当前状态 |
| --- | --- |
| frpc / frps 模式切换 | 已实现，保存设置后更新对应的侧边导航 |
| frpc / frps 启动、停止 | 已实现，使用 QProcess 异步管理子进程 |
| 进程状态与实时输出 | 已实现，展示启动、运行、停止状态及标准输出、错误输出 |
| 退出清理 | 已实现，关闭应用时终止受管的 FRP 子进程 |
| frps TOML 编辑 | 已实现，支持读取、编辑、语法校验和保存 |
| frpc 连接卡片 | 已实现，从 frpc.toml 的 proxies 条目读取并展示连接摘要 |
| frpc 添加、编辑、删除配置 | 尚未接通，当前“添加配置”按钮仅显示说明 |
| frpc JSON 配置档案 | 已有模型及读写服务，尚未接入完整的界面与启动流程 |
| 应用启动后自动运行 FRP | 已实现，按当前模式提交启动请求 |
| 开机自启动 | 仅保存设置，尚未实现系统启动项注册 |
| Dashboard | 当前为占位页面，尚未接入运行指标 |

界面中的“运行中”表示 FRP 子进程已经启动，不代表服务器连接成功或隧道已经可用。当前实时输出显示在界面中，EasyFrp 没有自动将这些输出保存到日志文件；FRP 自身的日志行为由 TOML 配置决定。

## 环境要求

- Windows 10 / 11。
- 推荐使用 Python 3.12 或更新版本；仓库现有 Conda 环境文件使用 Python 3.11，详见 [Conda 环境说明](miniconda_env/miniconda_init.md)。
- 支持 TOML 配置的 Windows 版 FRP，配置字段应与所用 FRP 版本匹配。

Python 依赖固定在 [requirements.txt](requirements.txt)：

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| PyQt6 | 6.11.0 | 桌面界面与 Qt 事件循环 |
| tomlkit | 0.15.0 | TOML 配置解析与语法校验 |
| PyInstaller | 6.21.0 | 打包 Windows 可执行程序 |

## 快速开始

以下命令在项目根目录的 PowerShell 中执行。

### 1. 创建环境并安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

也可以按照 [Conda 环境说明](miniconda_env/miniconda_init.md) 准备独立环境，或参考 [environment.yml](miniconda_env/environment.yml)。

### 2. 准备 FRP 程序

从 [FRP 官方 Releases](https://github.com/fatedier/frp/releases) 下载与系统架构匹配的 Windows 版本，将需要使用的程序放到：

```text
runtime/
├── frpc.exe
└── frps.exe
```

FRP 二进制文件不随 Git 仓库提供。只使用客户端或服务端时，只需准备对应的可执行文件。

### 3. 准备配置

- **frpc 模式**：启动前编辑 `config/frpc.toml`，填写服务器地址、端口、认证与代理配置。当前 frpc 配置页主要用于查看连接卡片。
- **frps 模式**：编辑 `config/frps.toml`；也可以启动界面后切换到 frps 模式，在配置页编辑并保存。
- **应用设置**：保存在 `config/config.json`，可在设置页切换模式并控制自动运行选项。

TOML 编辑器校验的是文件语法，不能保证 FRP 字段、网络连接或端口配置有效。修改运行中的 FRP 配置后，需要停止并重新启动对应进程，使其重新读取配置。

### 4. 启动界面

```powershell
.\.venv\Scripts\python.exe main.py
```

在设置页选择 `frpc 客户端` 或 `frps 服务端`，点击“应用设置”，再进入对应控制页启停进程并查看输出。启用“自动运行”后，下次打开 EasyFrp 时会自动尝试启动当前模式对应的 FRP 程序。

## 配置与数据目录

源码运行时，以下路径均相对于项目根目录；打包运行时，相对于 EasyFrp 可执行文件所在目录。

| 路径 | 用途 |
| --- | --- |
| `config/config.json` | 应用模式、开机自启动偏好、自动运行偏好 |
| `config/frpc.toml` | frpc 实际启动时读取的配置 |
| `config/frps.toml` | frps 实际启动时读取的配置 |
| `data/profile/frpc/global/` | frpc 全局 JSON 档案，包含服务器、认证、日志等配置 |
| `data/profile/frpc/connections/` | frpc 连接 JSON 档案，支持 TCP、UDP、XTCP 被访问端与访问端 |
| `runtime/` | FRP 可执行文件 |
| `logs/` | 预留日志目录，实际日志输出位置由 FRP 配置决定 |

JSON 档案目前由后端服务负责保存、读取和枚举，尚未自动组合生成启动用的 TOML。修改档案不会直接改变当前使用的 `config/frpc.toml`。

## 项目结构

```text
EasyFrp/
├── main.py                     # 程序入口，注册 src 模块搜索路径
├── requirements.txt            # Python 依赖
├── config/                     # 应用设置与 FRP TOML 配置
├── data/profile/frpc/          # JSON 配置档案，按需创建
├── docs/                       # 学习路线、PyQt6 教材及示例
├── miniconda_env/              # Conda 环境说明与环境文件
├── logs/                       # 预留日志目录
├── runtime/                    # frpc.exe、frps.exe
└── src/frp_gui/
    ├── app.py                  # 应用初始化与事件循环
    ├── backend/
    │   ├── frpc/               # 客户端配置、档案与进程服务
    │   ├── frps/               # 服务端配置与进程服务
    │   ├── models/frpc/        # 结构化配置模型与校验
    │   └── settings/           # 应用设置读写与默认值
    ├── ui/
    │   ├── main_window.py      # 主窗口、导航与退出清理
    │   ├── pages/              # Dashboard、控制页、配置页、设置页
    │   ├── panels/             # 进程控制、配置卡片与 TOML 编辑面板
    │   └── widgets/            # 可复用控件
    └── utils/                  # 路径定义与文件读写工具
```

界面通过 Qt 信号接收进程状态、输出和错误。进程控制使用 QProcess，配置读写与数据模型位于 backend，页面与功能面板位于 ui。

## 打包发布

在已安装依赖的 Windows 环境中，可使用以下命令作为单文件打包的起点：

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name EasyFrp --paths src --add-data "config:config" main.py
```

该命令将当前 `config/` 作为内置默认配置打包；发布前应检查其中的服务器地址和认证信息。`--paths src` 用于让打包器发现源码包。

输出程序为 `dist/EasyFrp.exe`。FRP 可执行文件需要另行放到它旁边的 `runtime/` 目录：

```text
dist/
├── EasyFrp.exe
├── runtime/
│   ├── frpc.exe
│   └── frps.exe
└── config/                     # 首次启动时补齐缺失的内置配置
```

程序启动时会创建配置、日志和运行目录；打包模式下还会复制缺失的内置配置，不覆盖已经存在的文件。请选择可写目录存放程序，以便保存设置、配置和档案。

此处给出的是打包方式说明，发布前仍需在目标 Windows 环境验证程序启动、资源部署、FRP 启停和退出清理。

## 后续开发方向

- 完成 frpc 配置的新增、编辑、删除与导入流程。
- 接通全局档案、连接档案选择及 TOML 生成，实现多配置管理与启动。
- 实现开机自启动设置对应的系统操作。
- 为 Dashboard 接入连接状态、流量和在线时长等信息。
- 完善日志管理、打包发布与自动化测试。
- 自动重连策略、定时启动与插件机制待进一步设计。

## 学习文档

- [学习路线](docs/学习路线.md)
- [PyQt6 模块详解与实战指南](docs/pyqt6-modules-guide/PyQt6模块详解与实战指南.md)
- [PyQt6 教材阅读地图](docs/Book/00_阅读地图与学习方法.md)
- [从教材走进 EasyFrp 源码](docs/Book/26_从教材走进EasyFrp源码.md)

## 第三方组件

- [FRP](https://github.com/fatedier/frp)：实际的内网穿透与转发程序，采用 Apache License 2.0。EasyFrp 仅提供图形化管理功能，与 FRP 官方项目无直接关联。
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)：Python 的 Qt 绑定，用于构建桌面界面。
- [tomlkit](https://github.com/python-poetry/tomlkit)：TOML 解析与读写库，采用 MIT License。
- [PyInstaller](https://pyinstaller.org/)：将 Python 应用打包为独立程序的工具。

## 贡献指南

欢迎提交 Bug Report、Feature Request 和 Pull Request。提交 Issue 前请先搜索已有问题，并提供：

- Windows、Python、FRP 版本及运行方式（源码或打包程序）。
- 复现步骤、预期行为和实际结果。
- 相关错误输出，以及移除 token、secretKey 等认证信息后的必要配置片段。

## License

本项目采用 [Apache License 2.0](LICENSE)。第三方组件遵循各自的许可证。

Copyright (c) 2026 大羊
