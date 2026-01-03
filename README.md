# HA Host Monitor

一个基于 Docker 的 Linux 系统监控工具，可以通过 REST API 将各种系统指标报告到 Home Assistant。在 Home Assistant 中集中监控 CPU 使用率、内存、磁盘空间、网络活动等系统信息。

**本项目由 Manus AI 完成开发。**

## 功能特性

- **实时系统监控**：采集 CPU、内存、磁盘、网络和系统负载等指标
- **Home Assistant 集成**：将指标作为传感器报告到 Home Assistant
- **灵活配置**：基于 YAML 的配置文件，易于自定义
- **单个指标频率控制**：为不同指标设置不同的更新频率
- **自动启动测试**：测试系统上哪些指标可用
- **错误日志**：详细的错误日志便于故障排查
- **Docker 支持**：在 Docker 容器中运行，正确挂载宿主机文件系统
- **轻量级**：基于 Python 3.11-slim 镜像

## 支持的指标

- **CPU**：使用率百分比、核心数
- **内存**：使用率百分比、可用内存
- **磁盘**：指定路径的使用率百分比
- **网络**：I/O 统计（发送/接收字节数、数据包、错误等）
- **系统**：平均负载、运行时间、启动时间、进程数
- **温度**：CPU 温度（如果系统支持）

## 前置要求

- 已安装 Docker 和 Docker Compose
- Home Assistant 实例正在运行且可访问
- Home Assistant 长期访问令牌

### 获取 Home Assistant 令牌

1. 打开 Home Assistant 网页界面
2. 点击左下角的个人资料图标
3. 向下滚动到"长期访问令牌"
4. 点击"创建令牌"
5. 输入名称（例如"Host Monitor"）
6. 复制令牌（之后无法再次查看）

## 安装

### 1. 克隆或下载项目

```bash
git clone https://github.com/neon9809/ha-host-monitor.git
cd ha-host-monitor
```

### 2. 配置应用

复制配置示例：

```bash
cp config/config.yml.example config/config.yml
```

编辑 `config/config.yml`，填入你的 Home Assistant 信息：

```yaml
home_assistant:
  url: "http://192.168.1.100:8123"  # 你的 Home Assistant 地址
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # 你的令牌
  verify_ssl: true

update_frequency: 60  # 全局更新频率（秒）

metrics:
  cpu_percent:
    enabled: true
    frequency: 60
  memory_percent:
    enabled: true
    frequency: 60
  # ... 配置其他指标
```

### 3. 使用 Docker Compose 运行

```bash
docker-compose up -d
```

这将：
- 构建 Docker 镜像
- 启动容器
- 挂载宿主机的 `/proc` 和 `/sys` 目录（只读）
- 挂载 `config` 目录用于配置和错误日志

### 4. 查看日志

```bash
docker-compose logs -f ha-host-monitor
```

### 5. 首次运行

首次运行时，应用将：
1. 加载或创建默认配置
2. 测试所有可用指标并报告哪些可用
3. 开始监控并向 Home Assistant 报告

查看输出中是否有指标加载失败。这些错误也会被记录到 `config/error.log`。

## 配置指南

### Home Assistant 设置

```yaml
home_assistant:
  url: "http://localhost:8123"        # Home Assistant 地址
  token: "YOUR_TOKEN_HERE"             # 长期访问令牌
  verify_ssl: true                     # 自签名证书时设为 false
```

### 全局设置

```yaml
update_frequency: 60                   # 默认更新频率（秒）
host_identifier: "auto"                # 主机标识符（"auto" 或自定义名称）
```

### 多服务器配置

如果你有多个 Linux 服务器需要监控，每个服务器都需要有唯一的 `host_identifier`：

**方法 1：自动使用主机名（推荐）**

```yaml
host_identifier: "auto"  # 自动使用主机的 hostname
```

结果：
- 服务器 hostname 为 `web-server`：`sensor.web_server_monitor_cpu_percent`
- 服务器 hostname 为 `db-server`：`sensor.db_server_monitor_cpu_percent`

**方法 2：手动指定标识符**

```yaml
host_identifier: "web-server-01"  # 自定义名称
```

结果：`sensor.web_server_01_monitor_cpu_percent`

**注意**：如果多个服务器使用相同的 `host_identifier`，它们的数据会互相覆盖！

### 指标配置

每个指标都可以单独配置：

```yaml
metrics:
  cpu_percent:
    enabled: true                      # 启用/禁用此指标
    frequency: 60                      # 更新频率（秒）
```

### 可用指标

| 指标 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `cpu_percent` | 浮点数 | % | CPU 使用率 0-100 |
| `cpu_count` | 整数 | 核 | 逻辑核心数 |
| `memory_percent` | 浮点数 | % | 内存使用率 0-100 |
| `memory_available` | 整数 | B | 可用内存字节数 |
| `disk_usage` | 字典 | % | 指定路径的磁盘使用率 |
| `network_io` | 字典 | B | 网络统计 |
| `load_average` | 字典 | load | 1、5、15 分钟平均负载 |
| `uptime` | 整数 | s | 系统运行时间（秒） |
| `boot_time` | 字符串 | ISO | 系统启动时间 |
| `process_count` | 整数 | 进程 | 运行中的进程数 |
| `cpu_temp` | 字典 | °C | CPU 温度（如果可用） |

## Home Assistant 集成

运行后，传感器将自动出现在 Home Assistant 中。传感器命名格式为：

`sensor.{hostname}_monitor_{metric_name}`

例如，如果主机名为 `web-server`：

- `sensor.web_server_monitor_cpu_percent`
- `sensor.web_server_monitor_memory_percent`
- `sensor.web_server_monitor_disk_usage`
- `sensor.web_server_monitor_network_io`
- `sensor.web_server_monitor_load_average`
- `sensor.web_server_monitor_uptime`
- `sensor.web_server_monitor_boot_time`
- `sensor.web_server_monitor_process_count`
- 等等

如果你自定义了 `host_identifier`，则使用你指定的名称。

你可以在以下地方使用这些传感器：
- 自动化
- 模板
- 仪表板
- 历史统计
- 等等

### 示例：创建仪表板卡片

```yaml
type: entities
title: 主机监控 - Web 服务器
entities:
  - entity: sensor.web_server_monitor_cpu_percent
    name: CPU 使用率
  - entity: sensor.web_server_monitor_memory_percent
    name: 内存使用率
  - entity: sensor.web_server_monitor_disk_usage
    name: 磁盘使用率
  - entity: sensor.web_server_monitor_load_average
    name: 系统负载
```

**注意**：将 `web_server` 替换为你的实际主机名或自定义标识符。

## Docker Compose 选项

### 自定义路径

要监控不同的根路径的磁盘使用情况，编辑 `docker-compose.yml`：

```yaml
environment:
  - DISK_PATH=/home
```

### 资源限制

在 `docker-compose.yml` 中取消注释并调整：

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
```

### 网络配置

如果 Home Assistant 在不同的网络上：

```yaml
networks:
  - default
  - home_assistant_network

networks:
  home_assistant_network:
    external: true
```

## 故障排查

### 无法连接到 Home Assistant

1. 检查 Home Assistant 地址和端口是否正确
2. 验证长期令牌是否有效
3. 查看 `config/error.log` 中的详细错误信息
4. 如果使用自签名证书，尝试设置 `verify_ssl: false`

### 传感器未出现

1. 检查 `config/config.yml` 中指标是否启用
2. 查看 `config/error.log` 中的指标采集错误
3. 检查容器日志：`docker-compose logs ha-host-monitor`
4. 确保 `/proc` 和 `/sys` 已正确挂载

### CPU 温度不工作

CPU 温度需要：
- 硬件传感器（虚拟机或容器中通常不可用）
- 正确的权限读取传感器数据
- 在虚拟机上无法工作是正常的

### 权限拒绝错误

容器以 root 身份运行以访问系统文件。如果看到权限错误：

1. 确保 `/proc` 和 `/sys` 可读
2. 检查宿主机上的文件权限
3. 尝试以提升的权限运行

## 手动 Docker 运行

如果不想使用 Docker Compose：

```bash
docker build -t ha-host-monitor .

docker run -d \
  --name ha-host-monitor \
  --restart unless-stopped \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v $(pwd)/config:/app/config \
  ha-host-monitor
```

## 开发

### 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 直接运行（需要 /proc 和 /sys 访问权限）
python -m ha_host_monitor.main
```

### 项目结构

```
ha-host-monitor/
├── ha_host_monitor/
│   ├── __init__.py           # 包初始化
│   ├── main.py               # 主程序入口
│   ├── collector.py          # 系统指标采集
│   ├── hass.py               # Home Assistant API 集成
│   └── config.py             # 配置管理
├── config/
│   └── config.yml.example    # 配置模板
├── Dockerfile                # Docker 镜像定义
├── docker-compose.yml        # Docker Compose 配置
├── requirements.txt          # Python 依赖
└── README.md                 # 本文件
```

## API 参考

### MetricsCollector

系统指标采集的主类：

```python
from ha_host_monitor.collector import MetricsCollector

collector = MetricsCollector()
cpu = collector.get_cpu_percent()
memory = collector.get_memory_percent()
```

### HomeAssistantNotifier

Home Assistant API 客户端：

```python
from ha_host_monitor.hass import HomeAssistantNotifier

notifier = HomeAssistantNotifier(
    url="http://localhost:8123",
    token="your_token"
)

notifier.update_sensor(
    entity_id="sensor.test",
    state=42,
    attributes={"unit_of_measurement": "%"}
)
```

## 性能

- 内存使用：~50-100 MB
- CPU 使用：最小（空闲时 < 1%）
- 网络：最小（仅发送更新）
- 磁盘：可忽略不计（仅日志）

## 限制

- CPU 温度在虚拟机上可能无法工作
- 某些指标在不同的 Linux 发行版上可能不可用
- 容器必须有 `/proc` 和 `/sys` 的读取权限

## 许可证

MIT 许可证 - 详见 LICENSE 文件

## 贡献

欢迎贡献！请随时提交问题或拉取请求。

## 支持

如有问题、疑问或建议：
1. 查看上面的故障排查部分
2. 查看 `config/error.log` 中的错误详情
3. 在 GitHub 上提交 issue，包括：
   - 系统信息
   - 配置（不含敏感数据）
   - 错误日志
   - Docker 版本

## 更新日志

### v0.1.0（初始版本）
- 初始版本，包含核心监控功能
- 支持 CPU、内存、磁盘、网络和系统指标
- Home Assistant REST API 集成
- YAML 配置
- Docker 支持

## 致谢

使用的技术：
- [psutil](https://github.com/giampaolo/psutil) - 系统和进程工具
- [requests](https://github.com/psf/requests) - HTTP 库
- [PyYAML](https://github.com/yaml/pyyaml) - YAML 解析器
- [Home Assistant](https://www.home-assistant.io/) - 开源家庭自动化平台

---

**开心监控！** 🚀

**项目开发者**：Manus AI
