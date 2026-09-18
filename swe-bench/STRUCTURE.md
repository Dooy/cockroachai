# 项目目录结构

```
swe-bench/
│
├── 📄 核心文件
│   ├── run_swe_agent.py          # 主测试脚本（使用 sweagent CLI）
│   ├── run_benchmark.py          # 备用脚本（直接 API 调用）
│   ├── Dockerfile                # Docker 镜像定义
│   ├── docker-compose.yml        # Docker Compose 配置
│   └── requirements.txt          # Python 依赖列表
│
├── ⚙️ 配置文件
│   ├── .env.example              # 环境变量模板
│   ├── .env                      # 实际配置（需自行创建）
│   ├── .gitignore                # Git 忽略规则
│   └── .dockerignore             # Docker 构建忽略规则
│
├── 🚀 脚本文件
│   ├── deploy.sh                 # 一键部署脚本（⚡ 推荐）
│   ├── test_setup.sh             # 环境检查脚本
│   └── check_project.sh          # 项目完整性检查
│
├── 📚 文档文件
│   ├── README.md                 # 项目主文档
│   ├── QUICKSTART.md             # 快速开始（一页速查）
│   ├── DEPLOY_GUIDE.md           # Ubuntu 部署指南
│   ├── FILES.md                  # 文件说明文档
│   ├── SUMMARY.md                # 项目完成总结
│   └── STRUCTURE.md              # 本文件（目录结构）
│
└── 📊 运行时生成目录
    └── results/                  # 测试结果（自动创建）
        ├── trajectories/         # 完整对话记录（JSON）
        ├── patches/              # 生成的代码修改（diff）
        └── summary.json          # 总体统计信息
```

## 文件统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 核心文件 | 5 | 实际运行的代码和配置 |
| 配置文件 | 4 | 环境变量和忽略规则 |
| 脚本文件 | 3 | 自动化部署和检查 |
| 文档文件 | 6 | 完整使用说明 |
| **总计** | **18** | 完整可用的测试环境 |

## 文件大小参考

```
核心文件:
  run_swe_agent.py        ~2 KB   (主脚本)
  run_benchmark.py        ~5 KB   (备用脚本)
  Dockerfile              ~1 KB   (镜像定义)
  docker-compose.yml      ~500 B  (Compose 配置)
  requirements.txt        ~150 B  (依赖列表)

配置文件:
  .env.example            ~300 B  (模板)
  .gitignore              ~200 B  (Git 规则)
  .dockerignore           ~300 B  (Docker 规则)

脚本文件:
  deploy.sh               ~400 B  (部署脚本)
  test_setup.sh           ~2 KB   (环境检查)
  check_project.sh        ~1.5 KB (完整性检查)

文档文件:
  README.md               ~8 KB   (主文档)
  QUICKSTART.md           ~5 KB   (快速开始)
  DEPLOY_GUIDE.md         ~15 KB  (部署指南)
  FILES.md                ~6 KB   (文件说明)
  SUMMARY.md              ~7 KB   (项目总结)
  STRUCTURE.md            ~4 KB   (本文件)

总计: ~58 KB (不含测试结果)
```

## 运行时数据大小参考

```
Docker 镜像:
  swe-bench-swe-agent     ~3-5 GB  (包含 Python、sweagent 和依赖)

测试结果 (单个任务):
  trajectory.json         ~50-200 KB (对话记录)
  patch.diff              ~1-10 KB   (代码修改)

测试结果 (300 任务):
  results/ 总计           ~10-20 GB  (包含所有对话和代码)
```

## 依赖关系图

```
┌─────────────────┐
│   用户入口       │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────────────┐
│手动   │  │check_project │
│配置   │  │    .sh       │
└───┬──┘  └──────┬───────┘
    │            │
    ▼            ▼
┌───────────────────┐
│   test_setup.sh   │ (可选)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│    deploy.sh      │ ⚡ 主入口
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ docker-compose    │
│      .yml         │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│.env    │ │Docker  │
│        │ │file    │
└────────┘ └───┬────┘
               │
               ▼
        ┌──────────────┐
        │requirements  │
        │    .txt      │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │run_swe_agent │
        │     .py      │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   sweagent   │
        │     CLI      │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │  Claude API  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   results/   │
        └──────────────┘
```

## 关键文件快速定位

### 想修改模型？
→ [.env](.env) 的 `MODEL=claude-opus-5`

### 想修改任务数？
→ [.env](.env) 的 `NUM_TASKS=2`

### 想修改成本限制？
→ [run_swe_agent.py:41](run_swe_agent.py#L41) 的 `--agent.model.per_instance_cost_limit`

### 想修改输出目录？
→ [run_swe_agent.py:44](run_swe_agent.py#L44) 的 `--output_dir`

### 想修改资源限制？
→ [docker-compose.yml](docker-compose.yml) 的 `deploy.resources`

### 想查看测试结果？
→ [results/](results/) 目录

### 想了解如何使用？
→ [QUICKSTART.md](QUICKSTART.md) 一页速查

### 想部署到服务器？
→ [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) 完整指南

## 工作流程

```
1. check_project.sh  ✓ 检查所有文件是否存在
         ↓
2. .env.example  →  复制为 .env  →  填入 API key
         ↓
3. test_setup.sh  ✓ 检查 Docker、API、磁盘、内存
         ↓
4. deploy.sh  →  启动 Docker Compose
         ↓
5. run_swe_agent.py  →  调用 sweagent CLI
         ↓
6. sweagent  →  运行测试，调用 Claude API
         ↓
7. results/  ←  保存对话记录、代码补丁、统计信息
```

## 开发时间线

1. ✅ 核心脚本 ([run_swe_agent.py](run_swe_agent.py))
2. ✅ Docker 容器化 ([Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml))
3. ✅ 自动化脚本 ([deploy.sh](deploy.sh), [test_setup.sh](test_setup.sh))
4. ✅ 配置管理 ([.env.example](.env.example), [.gitignore](.gitignore), [.dockerignore](.dockerignore))
5. ✅ 完整文档 (6 个 Markdown 文件)
6. ✅ 项目检查 ([check_project.sh](check_project.sh))
7. ✅ 备用方案 ([run_benchmark.py](run_benchmark.py))

---

🎉 **完整的 SWE-bench Lite 测试环境！**

立即开始: `./check_project.sh && cp .env.example .env && nano .env`
