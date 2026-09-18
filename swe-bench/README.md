# SWE-agent with Claude Opus 5 on SWE-bench Lite

使用官方 [SWE-agent](https://github.com/princeton-nlp/SWE-agent) + claude-opus-5 运行 SWE-bench Lite 测试。

## 架构

```
┌─────────────────────────────────────────┐
│  Docker Container                       │
│  ┌───────────────────────────────────┐  │
│  │  Official SWE-agent               │  │
│  │  (克隆自 Princeton)               │  │
│  └───────────────────────────────────┘  │
│             ↓                           │
│  ┌───────────────────────────────────┐  │
│  │  Claude Opus 5                    │  │
│  │  - 读取文件                        │  │
│  │  - 编辑文件                        │  │
│  │  - 搜索代码                        │  │
│  │  - 运行测试                        │  │
│  └───────────────────────────────────┘  │
│             ↓                           │
│  ┌───────────────────────────────────┐  │
│  │  测试环境 (Docker-in-Docker)      │  │
│  │  - 独立的 Python 环境             │  │
│  │  - 运行实际的 pytest              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 特点

✅ **真正的 Agent 模式** - Claude 用工具直接编辑文件，不生成 patch  
✅ **官方实现** - Princeton 维护的成熟框架  
✅ **完整隔离** - 每个任务独立的 Docker 环境  
✅ **自动调试** - Agent 会运行测试并根据失败信息继续修复  

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
nano .env
```

填写：
```bash
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com
MODEL=claude-opus-5
NUM_TASKS=2
```

### 2. 运行

```bash
./deploy.sh
```

或手动：
```bash
docker compose build
docker compose up
```

## 配置说明

### [config/default.yaml](config/default.yaml)

```yaml
model:
  name: claude-opus-5
  temperature: 0.0
  max_tokens: 4096

agent:
  max_turns: 30          # 每个任务最多 30 轮对话
  max_cost: 10.0         # 每个任务最多花费 $10

environment:
  timeout: 1800          # 每个任务超时 30 分钟
```

## 结果

结果保存在 `./results/` 目录：

```bash
results/
├── trajectories/      # 每个任务的完整对话记录
├── patches/          # 生成的修改（如果成功）
└── summary.json      # 总体统计
```

查看统计：
```bash
cat results/summary.json | jq '.resolve_rate'
```

## SWE-agent 的工作流程

对于每个 SWE-bench 任务：

1. **环境准备**
   - 克隆指定的 GitHub 仓库
   - 切换到指定的 commit
   - 安装依赖

2. **Agent 循环**（最多 30 轮）
   ```
   Claude: 我需要先看看问题相关的文件
   → search_file "separable"
   
   Claude: 找到了，让我读取这个文件
   → open astropy/modeling/separable.py
   
   Claude: 问题在 _cstack 函数，我需要修改它
   → edit 176:195
   < 旧代码
   > 新代码
   
   Claude: 让我运行测试验证
   → pytest tests/test_separable.py
   
   (如果失败)
   Claude: 测试失败了，我看看错误信息...继续修复
   
   (如果成功)
   Claude: 测试通过了！
   → submit
   ```

3. **评估**
   - 应用生成的修改
   - 运行完整的测试套件
   - 记录是否解决问题

## 与之前 patch 方案的对比

| 特性 | Patch 方案 | SWE-agent 方案 |
|------|-----------|----------------|
| 生成方式 | 一次性生成完整 patch | 多轮交互式编辑 |
| 调试能力 | ❌ 无法调试 | ✅ 可以根据测试结果调试 |
| 格式问题 | ❌ 容易出现格式错误 | ✅ 直接文件操作，无格式问题 |
| 成功率 | 低（补丁经常无法应用）| 高（Agent 会重试） |
| 成本 | 低（单次调用） | 高（多轮对话） |

## 预期表现

根据 SWE-agent 论文：
- **claude-2.1**: ~12.3% resolve rate  
- **claude-3-opus**: ~18.4% resolve rate  
- **claude-opus-5**: 应该更高（未公开数据）

## 成本估算

每个任务约：
- 10-30 轮对话
- 每轮 2000-5000 tokens (input)
- 每轮 500-1500 tokens (output)
- 总计约 0.5-2 USD/任务

SWE-bench Lite 全集 300 个任务：
- 预计总成本：$150-600

## 故障排除

### Docker-in-Docker 权限问题

确保 `privileged: true` 已设置，或者挂载 Docker socket：
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### SWE-agent 克隆失败

手动预先克隆：
```bash
cd swe-bench
git clone https://github.com/princeton-nlp/SWE-agent.git
# 修改 Dockerfile 使用本地副本
```

### API 配置问题

确认环境变量已正确传递：
```bash
docker compose config
```

## 参考

- [SWE-agent GitHub](https://github.com/princeton-nlp/SWE-agent)
- [SWE-bench 论文](https://arxiv.org/abs/2310.06770)
- [SWE-agent 论文](https://arxiv.org/abs/2405.15793)
