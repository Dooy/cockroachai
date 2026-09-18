# SWE-bench Lite 远程部署指南

## 已修复的问题

✅ **源文件提取** - 自动从测试文件推断需要修复的源文件  
✅ **补丁格式** - 修复假的 index 行和 prompt 泄露问题  
✅ **真实测试** - 运行实际的 pytest 验证修复结果  

## 快速部署（Ubuntu 服务器）

### 1. 上传代码到服务器

```bash
# 从本地上传
scp -r swe-bench user@your-server:/path/to/

# 或者用 git
ssh user@your-server
cd /path/to/
git clone <your-repo-url>
cd cockroachai/swe-bench
```

### 2. 配置环境变量

```bash
cp .env.example .env
nano .env
```

编辑 `.env` 文件：
```bash
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com
MODEL=claude-opus-5
NUM_TASKS=2
```

### 3. 一键启动

```bash
chmod +x deploy.sh
./deploy.sh
```

## 手动部署（详细步骤）

### 构建镜像
```bash
docker compose build
```

### 运行测试（前台）
```bash
docker compose up
```

### 后台运行
```bash
docker compose up -d
docker compose logs -f  # 查看日志
```

### 停止
```bash
docker compose down
```

## 查看结果

结果保存在 `./results/` 目录：

```bash
ls -lh results/
cat results/swe_bench_*.json | jq '.scores'
```

## 预期输出

```
┌─────────────────────────────────────────┐
│  SWE-bench Lite Real Evaluation         │
│  Model: claude-opus-5                   │
│  Tasks: 2                               │
└─────────────────────────────────────────┘

✓ Loaded 2 tasks from SWE-bench Lite

Processing astropy__astropy-12907...
  Extracting files from astropy/astropy...
  Found 3 files (inferred: 2, source: 0, test: 1)
  ✓ Extracted astropy/modeling/separable.py
  ✓ Extracted astropy/modeling/tests/test_separable.py
  
Generating patch for astropy__astropy-12907...
Cloning astropy/astropy...
Checking out d16bfe05...
✓ Patch applied for astropy__astropy-12907
Running tests...
✓ Tests passed for astropy__astropy-12907
```

## 常见问题

### 补丁无法应用

**原因**：Claude 生成的补丁可能包含：
- 假的 git index 行
- 不匹配的行号
- prompt 泄露的文本

**已修复**：现在会自动清理这些问题。

### 测试失败

检查 `results/*.json` 中的 `error` 字段：

```bash
cat results/swe_bench_*.json | jq '.results[].evaluation.error'
```

### Docker 构建失败

确保 Docker 已启动并且有足够的磁盘空间：

```bash
docker info
df -h
```

## 性能优化建议

### 1. 增加任务数
```bash
# .env 文件中
NUM_TASKS=10  # 默认 2 个
```

### 2. 使用更快的模型
```bash
MODEL=claude-sonnet-5  # 更快但可能准确度稍低
```

### 3. 并行运行
当前是串行执行，可以修改代码支持多进程。

## 成本估算

基于 claude-opus-5 的定价：
- 每个任务约 3000-6000 tokens (input)
- 每个任务约 1000-2000 tokens (output)
- SWE-bench Lite 全集 300 个任务
- 预计总成本：约 $2-5

## 下一步优化

如果需要跑完整的 300 个任务，建议：

1. **批量运行**：修改代码支持断点续跑
2. **结果缓存**：避免重复生成相同任务的补丁
3. **Docker 隔离**：每个任务用独立容器（真正的 SWE-bench 方式）
4. **并行执行**：多进程/多容器加速

当前版本适合快速验证模型在 SWE-bench 上的表现！
