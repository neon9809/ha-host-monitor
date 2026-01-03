_本项目由 [Manus AI](https://manus.im) 完成开发。_

# HA Host Monitor - Home Assistant 主机监控

一个基于 Docker 的 Linux 系统监控工具，可以将各种系统指标（CPU、内存、磁盘、网络、负载等）实时上报到 [Home Assistant](https://www.home-assistant.io/)。

![HA Host Monitor](https://user-images.githubusercontent.com/12345/67890.png) <!--- Placeholder for a future screenshot -->

## ✨ 功能特性

- **多架构支持**: 支持 `linux/amd64` (x86-64) 和 `linux/arm64` (aarch64) 架构。
- **实时系统监控**: 采集 12 项核心系统指标。
- **Home Assistant 集成**: 自动创建和更新传感器实体。
- **多服务器支持**: 通过自动主机名检测，轻松监控多个服务器而不会冲突。
- **灵活配置**: 使用 YAML 文件进行配置，可独立控制每个指标的开关和更新频率。
- **错误处理**: 启动时自动测试，并将错误写入日志文件。
- **轻量级**: 基于 `python:3.11-slim` 的轻量级 Docker 镜像。
- **自动化**: 通过 GitHub Actions 自动构建和发布多架构镜像。

## 🚀 快速开始

### 步骤 1: 环境配置

本工具支持两种上报模式，请根据你的需求选择一种。

#### 模式 1: REST API (默认)

**优点**: 配置简单，无需额外服务。
**缺点**: 实体没有 `unique_id`，无法在 Home Assistant UI 中管理。

1.  **创建目录**: 在主机上创建一个目录用于存放配置。
    ```bash
    mkdir -p ha-host-monitor/config
    cd ha-host-monitor
    ```

2.  **下载配置文件**:
    ```bash
    wget -O config/config.yml https://raw.githubusercontent.com/neon9809/ha-host-monitor/master/config/config.yml.example
    ```

3.  **编辑配置文件**: 打开 `config/config.yml`，填入你的 Home Assistant URL 和长期访问令牌。
    ```yaml
    home_assistant:
      report_mode: "rest_api"
      url: "http://your-home-assistant-ip:8123"
      token: "YOUR_LONG_LIVED_TOKEN_HERE"
    ```

#### 模式 2: MQTT Discovery

**优点**: 实体有 `unique_id`，可以在 UI 中管理。
**缺点**: 需要 MQTT Broker。

1.  **前提条件**:
    -   **MQTT Broker**: 确保你有一个正在运行的 MQTT Broker (例如 [Mosquitto](https://mosquitto.org/))。
    -   **Home Assistant MQTT 集成**: 在 Home Assistant 中设置好 MQTT 集成。

2.  **创建并编辑配置文件**: 按照模式 1 的步骤创建配置文件，然后修改 `config/config.yml` 如下：
    ```yaml
    home_assistant:
      report_mode: "mqtt"

    mqtt:
      broker: "your-mqtt-broker-ip"
      port: 1883
      username: "your-mqtt-username" # (可选)
      password: "your-mqtt-password" # (可选)
    ```

### 步骤 2: Docker 配置

在项目根目录（`ha-host-monitor/`）下创建一个 `docker-compose.yml` 文件。

```yaml
version: '3.8'

services:
  ha-host-monitor:
    image: ghcr.io/neon9809/ha-host-monitor:latest
    container_name: ha-host-monitor
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - ./config:/app/config
```

### 步骤 3: 启动容器

在 `docker-compose.yml` 文件所在的目录中，运行以下命令：

```bash
docker-compose up -d
```

现在，容器已经开始在后台运行，并向你的 Home Assistant 发送数据了！

## ⚙️ 配置详解

配置文件位于 `config/config.yml`。

### 格式化选项

你可以在 `formatting` 部分自定义单位和精度：

```yaml
formatting:
  disk_unit: "GB"      # B, KB, MB, GB, TB
  memory_unit: "GB"    # B, KB, MB, GB
  network_unit: "MB"   # B, KB, MB, GB
  decimal_places: 2    # 小数位数
```

### 全局设置

```yaml
update_frequency: 60                   # 默认更新频率（秒）
host_identifier: "auto"                # 主机标识符（"auto" 或自定义名称）
```

### 禁用单个指标

如果你不需要某个特定的指标，**建议将其 `enabled` 设置为 `false`**，而不是直接删除对应的配置块。

```yaml
metrics:
  cpu_temp:
    enabled: false
    frequency: 60
```

### 多服务器配置

如果你有多个 Linux 服务器需要监控，`host_identifier` 字段可以帮助你区分它们。

- **自动模式 (推荐)**: `host_identifier: "auto"` 会自动使用主机的 `hostname` 作为标识。
- **手动模式**: 你可以为每个服务器设置一个唯一的名称，如 `host_identifier: "web-server-01"`。

**注意**：如果多个服务器使用相同的 `host_identifier`，它们的数据会在 Home Assistant 中互相覆盖！

## 📊 可用指标

| 指标名称 | 单位 | 描述 |
|---|---|---|
| `cpu_percent` | % | CPU 使用率 |
| `cpu_count` | 个 | CPU 核心数 |
| `memory_percent` | % | 内存使用率 |
| `memory_available` | Bytes | 可用内存 |
| `disk_usage` | % | 根分区磁盘使用率 |
| `network_io` | 字典 | 网络 I/O 统计 |
| `load_average` | 字典 | 系统平均负载 (1, 5, 15分钟) |
| `uptime` | 秒 | 系统运行时间 |
| `boot_time` | ISO 格式 | 系统启动时间 |
| `process_count` | 个 | 运行中的进程数 |
| `cpu_temp` | °C | CPU 温度 (如果可用) |

## 🏠 Home Assistant 集成

运行后，传感器将自动出现在 Home Assistant 中。传感器命名格式为：

`sensor.{hostname}_monitor_{metric_name}`

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

## 🪵 查看日志

如果遇到问题，可以查看容器的日志。

```bash
docker-compose logs -f
```

错误日志也会被写入到 `config/error.log` 文件中。

## 🤝 贡献

欢迎提交 Pull Requests 或在 Issues 中报告问题。

## 📄 许可证

本项目使用 [MIT 许可证](LICENSE)。
