# EasyFrp

A modern FRP desktop client built with PyQt6.

一个基于 PyQt6 开发的 FRP 图形化管理客户端。

EasyFrp 旨在为 FRP 提供一个简洁、易用的 Windows 桌面管理界面，让用户无需手动编辑配置文件即可完成 FRP 的配置、启动、停止和状态查看。

---

## 功能特性

* 图形化配置管理
* FRP 启动 / 停止 / 重启
* 实时日志查看
* Material Design 深色主题
* 多配置文件管理（规划中）
* 系统托盘支持（规划中）

---

## 项目结构

```text
EasyFrp
│
├── config/
├── docs/
├── logs/
├── runtime/
├── resources/
│   ├── icons/
│   └── qss/
│
└── src/
    └── frp_gui/
        ├── core/
        ├── models/
        ├── utils/
        └── ui/
```

---

## 环境要求

* Python 3.12+
* PyQt6
* qt-material
* Windows 10 / 11
* FRP 0.6x+

---

## 安装依赖

```bash
pip install -r requirements.txt
```

---

## 启动项目

```bash
python main.py
```

---

## 打包发布

使用 PyInstaller：

```bash
pyinstaller -F -w main.py
```

生成文件位于：

```text
dist/
```

---

## 开发计划

### V1.0

* [x] 项目初始化
* [ ] 配置文件管理
* [ ] FRP启动与停止

### V1.1

* [ ] 多配置文件支持
* [ ] 系统托盘

### V1.2

* [ ] 实时日志显示
* [ ] 服务器端界面支持

### V1.3

* [ ] 状态监控
* [ ] 自动重连

### V1.4

* [ ] 流量统计
* [ ] 在线时长统计

### V1.5

* [ ] 插件系统（待定）
* [ ] 定时启动

---

## 第三方组件

本项目依赖以下开源项目：

### FRP

Official Repository:

https://github.com/fatedier/frp

License:

Apache License 2.0

EasyFrp 仅提供图形化管理功能，与 FRP 官方项目无直接关联。

### qt-material

Official Repository:

https://github.com/UN-GCPDS/qt-material

License:

BSD 2-Clause License

qt-material 用于为 PyQt6 界面提供 Material Design 主题。

---

## 贡献指南

欢迎提交：

* Bug Report
* Feature Request
* Pull Request

提交 Issue 前请确认：

* 已阅读 README
* 已搜索现有 Issue
* 提供完整日志信息

---

## License

Apache License 2.0

Copyright (c) 2026 大羊
