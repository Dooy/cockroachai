# 快速开始 - 一页速查

## 最简部署（3 步）

```bash
# 1. 配置
cp .env.example .env
nano .env  # 填入 ANTHROPIC_API_KEY

# 2. 测试（可选）
./test_setup.sh

# 3. 运行
./deploy.sh
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ANTHROPIC_API_KEY` | 必填 | Anthropic API 密钥 |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | API 端点 |
| `MODEL` | `claude-opus-5` | 模型名称 |
| `NUM_TASKS` | `2` | 测试任务数量 |

## 常用命令

```bash
# 构建镜像
docker compose build

# 启动（前台）
docker compose up

# 启动（后台）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down

# 完全清理
docker compose down -v
```

## 调整任务数

编辑 `.env`：
```bash
NUM_TASKS=10  # 运行前 10 个任务
```

对应的命令行参数：
```bash
--instances.slice :10
```

## 查看结果

```bash
# 查看目录
ls -lh results/

# 查看统计（需要 jq）
cat results/summary.json | jq '.'

# 查看成功率
cat results/summary.json | jq '.resolve_rate'
```

## 后台运行（推荐）

### 使用 tmux
```bash
# 创建会话
tmux new -s swe

# 运行测试
./deploy.sh

# 断开: Ctrl+B, 然后按 D
# 重连: tmux attach -t swe
```

### 使用 screen
```bash
# 创建会话
screen -S swe

# 运行测试
./deploy.sh

# 断开: Ctrl+A, 然后按 D
# 重连: screen -r swe
```

## 性能参考

### 单个任务

- **时间**: 5-20 分钟
- **对话轮数**: 10-30 轮
- **成本**: $0.50-2.00
- **Token**: 50K-150K

### 完整 SWE-bench Lite (300 任务)

- **时间**: 25-100 小时
- **成本**: $150-600
- **磁盘**: ~10GB (结果和缓存)
- **内存**: 8GB 推荐

## 实时监控

```bash
# 资源使用
docker stats

# 容器日志
docker logs swe-agent-lite -f

# 系统资源
htop  # 需要: sudo apt install htop
```

## 故障排除

### Docker 权限错误
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### API 连接测试
```bash
curl -v https://api.anthropic.com
```

### 清理磁盘空间
```bash
# 清理 Docker
docker system prune -a

# 清理旧结果
rm -rf results/old_*
```

### 查看 sweagent 版本
```bash
docker compose run --rm swe-agent pip show sweagent
```

## 高级配置

### 修改成本限制

编辑 [run_swe_agent.py](run_swe_agent.py:41):
```python
"--agent.model.per_instance_cost_limit", "10.0",  # 改为你的值
```

### 选择特定任务

```bash
# 前 10 个
--instances.slice :10

# 第 10-20 个
--instances.slice 10:20

# 最后 10 个
--instances.slice -10:
```

### 添加代理

编辑 `.env`:
```bash
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

## 文件结构

```
swe-bench/
├── .env                  # 配置（需创建）
├── .env.example         # 配置模板
├── deploy.sh            # 一键部署
├── test_setup.sh        # 环境检查
├── docker-compose.yml   # Docker 配置
├── Dockerfile           # 镜像定义
├── run_swe_agent.py     # 主脚本
├── requirements.txt     # Python 依赖
└── results/            # 结果输出（自动创建）
    ├── trajectories/   # 每个任务的对话记录
    ├── patches/        # 生成的代码修改
    └── summary.json    # 总体统计
```

## 参考链接

- [完整 README](README.md) - 详细架构和说明
- [部署指南](DEPLOY_GUIDE.md) - Ubuntu 服务器部署
- [SWE-agent GitHub](https://github.com/princeton-nlp/SWE-agent)
- [SWE-bench Lite 数据集](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite)
