# HA Host Monitor 使用说明

## 🚀 快速开始 (推荐)

使用 Docker Compose 是最简单、最推荐的部署方式。

### 步骤 1: 创建目录和配置文件

```bash
# 1. 创建项目目录并进入
mkdir ha-host-monitor && cd ha-host-monitor

# 2. 创建配置子目录
mkdir config

# 3. 下载配置文件示例
wget -O config/config.yml https://raw.githubusercontent.com/neon9809/ha-host-monitor/master/config/config.yml.example
```

### 步骤 2: 编辑配置文件

打开 `config/config.yml` 并填入你的 Home Assistant URL 和令牌。

```yaml
home_assistant:
  url: "http://your-home-assistant-ip:8123"
  token: "YOUR_LONG_LIVED_TOKEN_HERE"
```

### 步骤 3: 创建 `docker-compose.yml`

在项目根目录 (`ha-host-monitor/`) 创建 `docker-compose.yml` 文件：

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

### 步骤 4: 启动

```bash
docker-compose up -d
```

--- 

## 🐳 其他部署方式

### 使用 `docker run`

如果你不想使用 Docker Compose，也可以直接使用 `docker run`。

```bash
# 1. 创建并进入目录
mkdir -p ~/ha-host-monitor/config
cd ~/ha-host-monitor

# 2. 下载并编辑配置
wget -O config/config.yml https://raw.githubusercontent.com/neon9809/ha-host-monitor/master/config/config.yml.example
nano config/config.yml

# 3. 运行容器
docker run -d \
  --name ha-host-monitor \
  --restart unless-stopped \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v $(pwd)/config:/app/config \
  ghcr.io/neon9809/ha-host-monitor:latest
```

### 从源码构建

如果你想修改代码并自行构建镜像。

```bash
# 1. 克隆仓库
git clone https://github.com/neon9809/ha-host-monitor.git
cd ha-host-monitor

# 2. 配置
cp config/config.yml.example config/config.yml
nano config/config.yml

# 3. 构建并运行
docker-compose up -d --build
```

## 🔄 更新镜像

如果你使用了 `latest` 标签，可以轻松更新到最新版本。

```bash
# 1. 拉取最新镜像
docker-compose pull

# 2. 重启容器以应用更新
docker-compose up -d
```

如果未使用 Docker Compose:

```bash
docker pull ghcr.io/neon9809/ha-host-monitor:latest
docker stop ha-host-monitor
docker rm ha-host-monitor
# ...然后重新运行你的 docker run 命令
```

---

**本项目由 Manus AI 完成开发。**
