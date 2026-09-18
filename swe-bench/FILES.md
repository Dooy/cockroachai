# 项目文件说明

## 核心文件

| 文件 | 用途 |
|------|------|
| [run_swe_agent.py](run_swe_agent.py) | 主测试脚本，调用 sweagent CLI |
| [Dockerfile](Dockerfile) | Docker 镜像定义，安装 sweagent 和依赖 |
| [docker-compose.yml](docker-compose.yml) | Docker Compose 配置 |
| [requirements.txt](requirements.txt) | Python 依赖列表 |

## 配置文件

| 文件 | 用途 |
|------|------|
| [.env.example](.env.example) | 环境变量模板（需复制为 .env） |
| [.env](.env) | 实际配置（需自己创建，包含 API key） |
| [.gitignore](.gitignore) | Git 忽略规则 |
| [.dockerignore](.dockerignore) | Docker 构建忽略规则 |

## 脚本文件

| 文件 | 用途 |
|------|------|
| [deploy.sh](deploy.sh) | 一键部署脚本 |
| [test_setup.sh](test_setup.sh) | 环境检查脚本 |

## 文档文件

| 文件 | 用途 |
|------|------|
| [README.md](README.md) | 项目主文档，架构和详细说明 |
| [QUICKSTART.md](QUICKSTART.md) | 快速开始一页速查 |
| [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) | Ubuntu 服务器部署完整指南 |
| [FILES.md](FILES.md) | 本文件，项目文件说明 |

## 运行时生成

| 目录/文件 | 说明 |
|-----------|------|
| `results/` | 测试结果输出目录（自动创建） |
| `results/trajectories/` | 每个任务的完整对话记录 |
| `results/patches/` | 生成的代码修改 |
| `results/summary.json` | 总体统计信息 |
| `cache/` | sweagent 缓存目录（可选） |

## 使用流程

```
┌─────────────────┐
│  .env.example   │  复制并编辑
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      .env       │  填入 API key
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ test_setup.sh   │  检查环境（可选）
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   deploy.sh     │  一键部署
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ docker-compose  │  构建和启动容器
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ run_swe_agent.py│  运行 sweagent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   results/      │  输出结果
└─────────────────┘
```

## 如何阅读

### 第一次使用
1. [QUICKSTART.md](QUICKSTART.md) - 快速上手
2. [README.md](README.md) - 了解架构
3. [run_swe_agent.py](run_swe_agent.py) - 查看实现

### 部署到服务器
1. [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) - 完整部署步骤
2. [test_setup.sh](test_setup.sh) - 验证环境
3. [deploy.sh](deploy.sh) - 运行

### 自定义配置
1. [.env.example](.env.example) - 可配置的选项
2. [run_swe_agent.py](run_swe_agent.py) - 修改 sweagent 参数
3. [docker-compose.yml](docker-compose.yml) - 调整资源限制

## 关键参数位置

### 修改任务数量
- **环境变量**: `.env` 中的 `NUM_TASKS=2`
- **代码**: [run_swe_agent.py:43](run_swe_agent.py#L43) 的 `--instances.slice`

### 修改模型
- **环境变量**: `.env` 中的 `MODEL=claude-opus-5`
- **代码**: [run_swe_agent.py:40](run_swe_agent.py#L40) 的 `--agent.model.name`

### 修改成本限制
- **代码**: [run_swe_agent.py:41](run_swe_agent.py#L41) 的 `--agent.model.per_instance_cost_limit`

### 修改输出目录
- **代码**: [run_swe_agent.py:44](run_swe_agent.py#L44) 的 `--output_dir`
- **挂载**: [docker-compose.yml:10](docker-compose.yml#L10) 的 volumes

## 权限要求

```bash
# 需要执行权限的脚本
chmod +x deploy.sh
chmod +x test_setup.sh

# 需要保护的文件（包含密钥）
chmod 600 .env
```

## 依赖关系

```
Dockerfile
  ├── requirements.txt (Python 依赖)
  └── sweagent (从 PyPI 安装)

docker-compose.yml
  ├── Dockerfile (构建镜像)
  ├── .env (环境变量)
  └── volumes (挂载目录)

run_swe_agent.py
  ├── rich (进度显示)
  └── sweagent CLI (实际执行)

deploy.sh
  └── docker-compose.yml (启动容器)
```
