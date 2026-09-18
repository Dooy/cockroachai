# SWE-bench Lite 测试环境

基于 Claude Opus 5 的 SWE-bench Lite 完整评估环境，支持补丁生成、应用和测试验证。

## 功能特性

- 🤖 单模型测试：claude-opus-5
- ⚙️ 环境变量配置：支持自定义 API Key 和 Base URL
- 📊 可配置任务数：默认 2 个任务
- 🐳 Docker 容器化：一键部署
- 🔍 完整评估流程：
  - 自动加载 SWE-bench Lite 数据集
  - 调用 Claude 生成代码补丁
  - 克隆仓库并应用补丁
  - 运行测试验证
- 📈 详细评分指标：
  - **Patch Generation Rate**: 成功生成补丁的比率
  - **Patch Apply Rate**: 补丁成功应用的比率
  - **Resolve Rate**: 测试通过的比率（实际解决问题）
- 💾 结果保存：JSON 格式输出详细结果和统计

## 快速开始

### 1. 环境准备

确保 Ubuntu 服务器已安装：
- Docker
- Docker Compose (插件版本)

```bash
# 安装 Docker (如果未安装)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose Plugin
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 重新登录或执行
newgrp docker
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

## 评估流程

```
1. 加载数据集
   └─ 从 HuggingFace 加载 SWE-bench Lite 测试集

2. 生成补丁
   └─ 调用 Claude API 分析问题并生成 git patch

3. 应用补丁
   ├─ 克隆目标仓库
   ├─ 切换到指定的 base commit
   ├─ 应用生成的补丁
   └─ 验证补丁是否可以成功应用

4. 运行测试
   ├─ 应用测试补丁（如果有）
   ├─ 运行仓库测试
   └─ 记录测试结果

5. 生成报告
   └─ 计算各项指标并保存结果
```

## 结果输出

测试结果保存在 `./results` 目录下，文件名格式：
```
swe_bench_results_YYYYMMDD_HHMMSS.json
```

### 结果文件结构

```json
{
  "metadata": {
    "model": "claude-opus-5",
    "num_tasks": 2,
    "timestamp": "2026-09-18T09:00:00",
    "total_tokens": {
      "input": 12450,
      "output": 28340
    }
  },
  "statistics": {
    "total": 2,
    "generated": 2,
    "applied": 1,
    "passed": 1
  },
  "scores": {
    "patch_generation_rate": 100.0,
    "patch_apply_rate": 50.0,
    "resolve_rate": 50.0
  },
  "results": [
    {
      "task_id": "django__django-12345",
      "model": "claude-opus-5",
      "patch": "diff --git a/file.py...",
      "full_response": "...",
      "usage": {
        "input_tokens": 6225,
        "output_tokens": 14170
      },
      "timestamp": "2026-09-18T09:00:00",
      "evaluation": {
        "applied": true,
        "tests_passed": true,
        "error": null
      }
    }
  ]
}
```

### 评分指标说明

- **Patch Generation Rate**: 模型成功生成有效补丁的任务比例
- **Patch Apply Rate**: 生成的补丁能够成功应用到代码库的比例
- **Resolve Rate**: 应用补丁后测试通过的比例（这是最重要的指标，代表真正解决了问题）

## 输出示例

运行时会显示实时进度和彩色输出：

```
╭──────────────────────────────────────────╮
│ SWE-bench Lite Evaluation                │
│ Model: claude-opus-5                     │
│ Tasks: 2                                 │
│ Base URL: https://api.anthropic.com      │
╰──────────────────────────────────────────╯

✓ Loaded 2 tasks from SWE-bench Lite

⠋ django__django-12345 (1/2)
Generating patch for django__django-12345...
✓ Patch applied successfully for django__django-12345

📊 Execution Statistics
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Metric                  ┃ Count ┃   Rate ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ Total Tasks             │     2 │   100% │
│ Patches Generated       │     2 │ 100.0% │
│ Patches Applied         │     1 │  50.0% │
│ Tests Passed            │     1 │  50.0% │
└─────────────────────────┴───────┴────────┘

🎯 SWE-bench Scores
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Metric                       ┃   Score ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Patch Generation Rate        │ 100.00% │
│ Patch Apply Rate             │  50.00% │
│ Resolve Rate                 │  50.00% │
└──────────────────────────────┴─────────┘

💰 Token Usage
┏━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Type         ┃   Count ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Input Tokens │  12,450 │
│ Output Tokens│  28,340 │
│ Total Tokens │  40,790 │
└──────────────┴─────────┘
```

## 目录结构

```
swe-bench/
├── .env.example          # 环境变量模板
├── .gitignore           # Git 忽略文件
├── Dockerfile           # Docker 镜像配置
├── docker-compose.yml   # Docker Compose 配置
├── requirements.txt     # Python 依赖
├── run_benchmark.py     # 主测试脚本（完整评估流程）
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
4. **Token 消耗**：每个任务约消耗 6000-10000 tokens，请注意成本
5. **磁盘空间**：每个任务会克隆一个 git 仓库（临时），确保有足够空间
6. **网络连接**：需要访问 GitHub 克隆仓库和 HuggingFace 下载数据集
7. **测试简化**：当前版本使用简化的测试流程，完整的 SWE-bench 需要 Docker 容器隔离

## 性能优化建议

- **并发处理**：修改脚本支持多任务并行处理（注意 API 限流）
- **缓存仓库**：对常见仓库进行本地缓存，避免重复克隆
- **Docker 隔离**：使用 Docker 容器运行测试，提高安全性和准确性

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

### 数据集下载失败
```bash
# 设置 HuggingFace 镜像（如果在中国）
export HF_ENDPOINT=https://hf-mirror.com
```

### 查看容器日志
```bash
docker compose logs -f
```

### Git 克隆失败
确保服务器可以访问 GitHub：
```bash
git clone --depth 1 https://github.com/django/django.git test-repo
```

## 与官方 SWE-bench 的差异

官方 SWE-bench 使用完整的 Docker 容器隔离环境运行测试，本实现为简化版：

- ✅ 支持：数据集加载、补丁生成、补丁应用
- ⚠️ 简化：测试执行（当前为占位符，不在隔离容器中运行实际测试）
- 🔄 扩展方向：可以集成 Docker SDK 来运行完整的测试环境

如需完整的测试执行，建议参考官方 SWE-bench 的 Docker 测试床实现。

## License

MIT
