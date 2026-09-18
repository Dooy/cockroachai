# SWE-bench Lite 测试环境

基于 Claude Opus 5 的 SWE-bench Lite 自动化测试环境，适用于 Ubuntu 远程部署。

## 功能特性

- 🤖 单模型测试：claude-opus-5
- ⚙️ 环境变量配置：支持自定义 API Key 和 Base URL
- 📊 可配置任务数：默认 2 个任务
- 🐳 Docker 容器化：一键部署
- 📈 结果保存：JSON 格式输出测试结果

## 快速开始

### 1. 环境准备

确保 Ubuntu 服务器已安装：
- Docker
- Docker Compose

```bash
# 安装 Docker (如果未安装)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose (如果未安装)
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

配置示例：
```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Test Configuration
NUM_TASKS=2
MODEL_NAME=claude-opus-5

# Optional: Results directory
RESULTS_DIR=./results
```

### 3. 运行测试

```bash
# 一键部署并运行
./deploy.sh
```

或者手动运行：

```bash
# 构建镜像
docker compose build

# 启动测试
docker compose up
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - | ✅ |
| `ANTHROPIC_BASE_URL` | API 基础 URL | `https://api.anthropic.com` | ❌ |
| `NUM_TASKS` | 测试任务数量 | `2` | ❌ |
| `MODEL_NAME` | 模型名称 | `claude-opus-5` | ❌ |
| `RESULTS_DIR` | 结果保存目录 | `./results` | ❌ |

## 结果输出

测试结果保存在 `./results` 目录下，文件名格式：
```
swe_bench_results_YYYYMMDD_HHMMSS.json
```

结果文件结构：
```json
{
  "metadata": {
    "model": "claude-opus-5",
    "num_tasks": 2,
    "timestamp": "2026-09-18T16:00:00",
    "total_tokens": {
      "input": 1234,
      "output": 5678
    }
  },
  "results": [
    {
      "task_id": "django__django-12345",
      "model": "claude-opus-5",
      "response": "...",
      "usage": {
        "input_tokens": 617,
        "output_tokens": 2839
      },
      "timestamp": "2026-09-18T16:00:00"
    }
  ]
}
```

## 目录结构

```
swe-bench/
├── .env.example          # 环境变量模板
├── .gitignore           # Git 忽略文件
├── Dockerfile           # Docker 镜像配置
├── docker-compose.yml   # Docker Compose 配置
├── requirements.txt     # Python 依赖
├── run_benchmark.py     # 主测试脚本
├── deploy.sh           # 一键部署脚本
├── README.md           # 说明文档
└── results/            # 测试结果目录（自动创建）
```

## 本地开发

如果需要在本地开发调试：

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export ANTHROPIC_API_KEY=sk-ant-xxxxx
export NUM_TASKS=2

# 运行测试
python run_benchmark.py
```

## 注意事项

1. **API 配额**：确保你的 Anthropic API 账户有足够的配额
2. **任务数量**：SWE-bench Lite 包含 300 个测试任务，建议从小数量开始测试
3. **费率限制**：脚本内置了请求间隔（1秒），避免触发 API 限流
4. **Token 消耗**：每个任务约消耗 3000-6000 tokens，请注意成本

## 故障排查

### Docker 权限问题
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### API 连接问题
检查网络连接和 Base URL 配置：
```bash
curl -I https://api.anthropic.com
```

### 查看容器日志
```bash
docker compose logs -f
```

## License

MIT
