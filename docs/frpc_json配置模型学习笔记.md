# frpc JSON 配置模型学习笔记

## 2026-06-21

### 讨论主题

在 model 层新增 frpc 配置数据结构，并把配置档案以 JSON 形式保存到 `data/profile/frpc`。

### 当前确认的需求

- 全局配置独立建模，例如服务端地址、端口、认证方式、认证 token。
- 连接配置按连接方式分别建模，例如 TCP 配置类、UDP 配置类。
- TCP、UDP 等连接配置类保持同级关系，不抽象公共基类。
- JSON 文件名使用用户自定义配置名称。
- JSON 内容中保留连接类型字段，读取时通过该字段判断应解析成哪种连接配置类。
- 本轮先新增功能，不改动现有 `config/frpc.toml` 文本编辑和启动流程。
- 当前运行配置仍以 TOML 为准；未来计划是在服务启动前读取选定 JSON，再生成 TOML，最后启动 frpc。

### 已确认的结构选择

- 一个连接配置 JSON 只代表一个单独连接，例如一个 TCP 连接或一个 UDP 连接。
- 全局配置另存为独立 JSON，不和连接配置放在同一个文件中。
- 这样设计是为了支持后续“已配置但本次不启动”的场景：启动前只读取被勾选启用的连接配置，再组合生成最终 TOML。
- 单个连接配置 JSON 不保存 `enabled` 字段；启用状态属于界面选择或启动方案，不属于连接本身。

### 需要继续确认

- 全局配置 JSON 的文件名和是否允许存在多个全局配置档案。
- 配置名称是否只来自文件名，还是 JSON 内部也需要保存一份 `name` 字段。

### 架构关注点

- model 层只表达数据结构，不直接负责磁盘路径。
- 持久化读写更适合放在 core/service 层，避免 UI 或 model 直接操作文件系统。
- 未来启动流程应拆成三步：读取全局配置、读取被选中的连接配置、生成 TOML 并启动 frpc。
- JSON 到 TOML 的转换应单独封装，避免和读取、保存逻辑混在一起。

### 用户当前理解

- model 层声明各个连接类型的数据结构，保存连接对应的配置字段、名称等自定义字段。
- model 层还会包含一份全局配置数据结构，用于保存 frpc 公共配置，例如 frps 地址、日志配置、身份验证。
- core 层负责按照 model 结构保存和解析配置。
- core 层未来还会负责把解析后的配置组合并写入 TOML。

### 本轮校准

- 这个理解整体正确。
- 需要注意：model 只描述数据，不直接关心文件路径、JSON 读写或 TOML 写入。
- JSON 保存/读取和 TOML 生成建议拆成不同 service，避免一个类同时承担太多职责。

### 已实现的第一阶段结构

- `src/frp_gui/models/frpc/global_config.py`
  - `FrpcGlobalConfig` 保存服务器地址、端口、认证方式、token 和日志配置。
  - `FrpcLogConfig` 保存日志等级、输出位置和保留天数。
- `src/frp_gui/models/frpc/tcp_proxy_config.py`
  - `TcpProxyConfig` 保存单个 TCP 连接配置。
- `src/frp_gui/models/frpc/udp_proxy_config.py`
  - `UdpProxyConfig` 保存单个 UDP 连接配置。
- `src/frp_gui/models/frpc/proxy_type.py`
  - `FrpcProxyType` 统一保存支持的连接类型字符串。
- `src/frp_gui/core/frpc_profile_service.py`
  - `FrpcProfileService` 负责 JSON 保存、读取、文件名校验和按 `type` 解析连接配置。

### 当前保存目录

- 全局配置：`data/profile/frpc/global/<配置名称>.json`
- 连接配置：`data/profile/frpc/connections/<配置名称>.json`

### 本阶段暂不处理

- 不改动当前 `config/frpc.toml` 文本编辑器。
- 不改动当前 frpc 启动流程。
- 不生成 TOML。
- 不保存 `enabled` 字段；启用状态未来由 UI 或启动方案管理。

### Python 模型层概念

- `@dataclass(slots=True)` 用来让类更适合表达“数据结构”：自动生成初始化方法，并限制实例只能拥有声明过的字段。
- `validate(self) -> None` 是模型自己的数据校验方法，负责判断当前对象字段是否合法；成功时不返回内容，失败时抛出异常。
- `@classmethod` 让方法接收类本身 `cls`，适合写 `from_dict` 这种“从字典创建模型对象”的工厂方法。
