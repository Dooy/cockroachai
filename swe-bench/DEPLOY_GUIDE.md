# Ubuntu 部署指南

## 系统要求

- Ubuntu 20.04+ (或其他支持 Docker 的 Linux 发行版)
- Docker 20.10+
- Docker Compose v2+
- 至少 8GB RAM
- 至少 20GB 可用磁盘空间

## 快速部署

### 1. 安装 Docker

如果尚未安装 Docker：

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户添加到 docker 组（避免每次都用 sudo）
sudo usermod -aG docker $USER

# 重新登录使组权限生效
newgrp docker

# 验证安装
docker --version
docker compose version
```

### 2. 克隆/上传项目

```bash
cd /opt  # 或你喜欢的目录
# 如果是从 git 克隆
git clone <your-repo-url>
cd cockroachai/swe-bench

# 或者直接上传整个 swe-bench 目录到服务器
```

### 3. 配置环境变量

```bash
cp .env.example .env
nano .env  # 或 vim .env
```

填入你的配置：
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_BASE_URL=https://api.anthropic.com
MODEL=claude-opus-5
NUM_TASKS=2
```

保存并退出 (Ctrl+X, Y, Enter)

### 4. 运行

```bash
chmod +x deploy.sh
./deploy.sh
```

## 后台运行

如果需要在后台运行（即使 SSH 断开连接也继续）：

### 方法 1: 使用 nohup

```bash
nohup ./deploy.sh > swe-agent.log 2>&1 &

# 查看日志
tail -f swe-agent.log

# 查看进程
ps aux | grep docker

# 停止
docker compose down
```

### 方法 2: 使用 screen

```bash
# 安装 screen（如果没有）
sudo apt-get install screen

# 创建新 session
screen -S swe-agent

# 在 screen 中运行
./deploy.sh

# 断开 session: Ctrl+A, 然后按 D
# 重新连接: screen -r swe-agent
# 列出所有 sessions: screen -ls
```

### 方法 3: 使用 tmux

```bash
# 安装 tmux（如果没有）
sudo apt-get install tmux

# 创建新 session
tmux new -s swe-agent

# 在 tmux 中运行
./deploy.sh

# 断开 session: Ctrl+B, 然后按 D
# 重新连接: tmux attach -t swe-agent
# 列出所有 sessions: tmux ls
```

## 查看结果

```bash
# 查看结果目录
ls -lh results/

# 查看统计摘要
cat results/summary.json | jq '.'

# 查看成功率
cat results/summary.json | jq '.resolve_rate'

# 查看具体任务的轨迹
ls results/trajectories/

# 下载结果到本地（在本地机器上运行）
scp -r user@server:/opt/cockroachai/swe-bench/results ./
```

## 资源监控

### 监控 Docker 容器资源使用

```bash
# 实时监控
docker stats

# 查看容器日志
docker compose logs -f

# 查看特定容器日志
docker logs swe-agent-lite -f
```

### 系统资源监控

```bash
# CPU 和内存
htop  # 需要安装: sudo apt-get install htop

# 磁盘使用
df -h

# Docker 磁盘使用
docker system df

# 清理未使用的 Docker 资源
docker system prune -a
```

## 故障排除

### 问题 1: Docker socket 权限错误

```bash
# 错误: permission denied while trying to connect to Docker daemon
sudo chmod 666 /var/run/docker.sock

# 或重启 Docker
sudo systemctl restart docker
```

### 问题 2: 内存不足

编辑 `docker-compose.yml` 限制内存：
```yaml
services:
  swe-agent:
    ...
    deploy:
      resources:
        limits:
          memory: 4G
```

### 问题 3: 磁盘空间不足

```bash
# 清理 Docker 资源
docker system prune -a --volumes

# 清理旧的测试结果
rm -rf results/old_*
```

### 问题 4: 网络连接问题

如果无法访问 Anthropic API：

```bash
# 测试网络连接
curl -I https://api.anthropic.com

# 如果需要代理，在 .env 中添加
HTTPS_PROXY=http://your-proxy:port
HTTP_PROXY=http://your-proxy:port
```

### 问题 5: SWE-agent 克隆失败

如果 GitHub 访问受限，预先克隆：

```bash
cd swe-bench
git clone https://github.com/princeton-nlp/SWE-agent.git

# 然后修改 Dockerfile，将这一行：
# RUN git clone https://github.com/princeton-nlp/SWE-agent.git /swe-agent
# 改为：
# COPY SWE-agent /swe-agent
```

## 性能优化

### 1. 增加并行度

如果机器性能强，可以运行多个实例：

```bash
# 复制配置
cp .env .env.batch1
cp .env .env.batch2

# 编辑不同的任务范围
# .env.batch1: NUM_TASKS=0-100
# .env.batch2: NUM_TASKS=100-200

# 在不同目录运行
```

### 2. 使用本地缓存

SWE-agent 会缓存克隆的仓库，确保持久化：

```yaml
volumes:
  - ./results:/app/results
  - ./cache:/root/.cache  # 添加缓存持久化
```

### 3. 提前拉取依赖

```bash
# 预先构建镜像（避免每次都重新下载）
docker compose build

# 保存镜像以便后续使用
docker save swe-bench-swe-agent > swe-agent-image.tar

# 在其他机器加载
docker load < swe-agent-image.tar
```

## 安全建议

1. **保护 API Key**
   ```bash
   chmod 600 .env
   ```

2. **限制 Docker 容器权限**
   - 如果不需要 Docker-in-Docker，移除 `privileged: true`

3. **设置防火墙**
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   ```

4. **定期更新**
   ```bash
   docker compose pull
   docker compose build --no-cache
   ```

## 成本控制

设置每个任务的最大成本（在 `config/default.yaml`）：

```yaml
model:
  per_instance_cost_limit: 5.0  # 每个任务最多 $5
```

监控总成本：

```bash
# 从结果中统计
cat results/summary.json | jq '.total_cost'
```

## 完整运行流程

```bash
# 1. 确保在 swe-bench 目录
cd /opt/cockroachai/swe-bench

# 2. 验证配置
cat .env

# 3. 启动（推荐用 tmux）
tmux new -s swe-agent
./deploy.sh

# 4. 断开 tmux (Ctrl+B, D)

# 5. 稍后重新连接查看进度
tmux attach -t swe-agent

# 6. 完成后查看结果
ls -lh results/
cat results/summary.json | jq '.'
```
