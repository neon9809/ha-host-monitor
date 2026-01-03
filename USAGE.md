# HA Host Monitor 使用说明

## 快速开始

### 方法 1：使用 ghcr.io 镜像（推荐）

直接使用已发布的 Docker 镜像：

```bash
# 创建配置目录
mkdir -p ~/ha-host-monitor/config

# 下载配置示例
curl -o ~/ha-host-monitor/config/config.yml https://raw.githubusercontent.com/neon9809/ha-host-monitor/master/config/config.yml.example

# 编辑配置文件
nano ~/ha-host-monitor/config/config.yml

# 运行容器
docker run -d \
  --name ha-host-monitor \
  --restart unless-stopped \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v ~/ha-host-monitor/config:/app/config \
  ghcr.io/neon9809/ha-host-monitor:v0.1.0
```

### 方法 2：使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  ha-host-monitor:
    image: ghcr.io/neon9809/ha-host-monitor:v0.1.0
    container_name: ha-host-monitor
    restart: unless-stopped
    
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - ./config:/app/config
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

然后运行：

```bash
docker-compose up -d
```

### 方法 3：从源码构建

```bash
# 克隆仓库
git clone https://github.com/neon9809/ha-host-monitor.git
cd ha-host-monitor

# 配置
cp config/config.yml.example config/config.yml
nano config/config.yml

# 构建并运行
docker-compose up -d
```

## 配置 Home Assistant Token

1. 登录 Home Assistant
2. 点击左下角的用户头像
3. 滚动到"长期访问令牌"部分
4. 点击"创建令牌"
5. 输入名称（如"Host Monitor"）
6. 复制生成的令牌
7. 将令牌粘贴到 `config/config.yml` 中的 `token` 字段

## 查看日志

```bash
# 查看实时日志
docker logs -f ha-host-monitor

# 查看错误日志
cat ~/ha-host-monitor/config/error.log
```

## 在 Home Assistant 中使用

传感器会自动出现在 Home Assistant 中：

- `sensor.host_monitor_cpu_percent`
- `sensor.host_monitor_memory_percent`
- `sensor.host_monitor_disk_usage`
- `sensor.host_monitor_load_average`
- 等等

### 创建仪表板卡片

```yaml
type: entities
title: 服务器监控
entities:
  - entity: sensor.host_monitor_cpu_percent
    name: CPU 使用率
  - entity: sensor.host_monitor_memory_percent
    name: 内存使用率
  - entity: sensor.host_monitor_disk_usage
    name: 磁盘使用率
  - entity: sensor.host_monitor_load_average
    name: 系统负载
```

## 更新镜像

```bash
# 拉取最新镜像
docker pull ghcr.io/neon9809/ha-host-monitor:latest

# 重启容器
docker-compose down
docker-compose up -d
```

## 故障排查

### 无法连接到 Home Assistant

检查配置文件中的 URL 和 token 是否正确：

```bash
cat ~/ha-host-monitor/config/config.yml
```

### 传感器未出现

查看容器日志：

```bash
docker logs ha-host-monitor
```

查看错误日志：

```bash
cat ~/ha-host-monitor/config/error.log
```

## 支持

- GitHub Issues: https://github.com/neon9809/ha-host-monitor/issues
- 项目主页: https://github.com/neon9809/ha-host-monitor

---

**本项目由 Manus AI 完成开发。**
