#!/usr/bin/env bash
# ==============================================================================
# SWE-agent v1.1.0+ & SWE-bench Lite Pipeline (Anthropic API Native Format)
# ==============================================================================

set -eo pipefail

# ------------------------------------------------------------------------------
# 1. 基础参数与配置
# ------------------------------------------------------------------------------
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-sk-ant-your-key-here}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"

# 若使用自定义中转 API 端点，设置 LiteLLM 环境变量
export OPENAI_API_BASE="${ANTHROPIC_BASE_URL}"

MODEL_NAME="anthropic/claude-3-5-sonnet-20241022"
DATASET_NAME="princeton-nlp/SWE-bench_Lite"
SPLIT="test"
NUM_INSTANCES=2
NUM_WORKERS=2

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXP_NAME="swe_eval_anthropic_${TIMESTAMP}"

echo "=========================================================="
echo "🚀 开始 SWE-agent + SWE-bench Lite 自动化测试流程"
echo "=========================================================="
echo "Model:         ${MODEL_NAME}"
echo "Base URL:      ${ANTHROPIC_BASE_URL}"
echo "Dataset:       ${DATASET_NAME} (${SPLIT})"
echo "Tasks Count:   ${NUM_INSTANCES}"
echo "Experiment:    ${EXP_NAME}"
echo "=========================================================="

# ------------------------------------------------------------------------------
# 2. 前置检查
# ------------------------------------------------------------------------------
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未检测到 Docker，请确保 Docker 已运行。"
    exit 1
fi

if ! command -v sweagent &> /dev/null; then
    echo "❌ 错误: 未检测到 sweagent 命令。"
    exit 1
fi

CONFIG_FILE=""
if [ -f "config/swebench.yaml" ]; then
    CONFIG_FILE="config/swebench.yaml"
elif [ -f "config/default.yaml" ]; then
    CONFIG_FILE="config/default.yaml"
fi

if [ -n "${CONFIG_FILE}" ]; then
    echo "ℹ️ 使用配置文件: ${CONFIG_FILE}"
    CONFIG_ARG="--config ${CONFIG_FILE}"
else
    CONFIG_ARG=""
fi

# ------------------------------------------------------------------------------
# 3. 第一阶段: 运行 SWE-agent
# ------------------------------------------------------------------------------
echo -e "\n[Phase 1/2] 正在运行 SWE-agent 产生 Patch..."

# SWE-agent v1.1.0+ 适配修改：
# - 必须设置 --instances.type swebench (嵌套展开格式: --instances.type=swebench)
# - 使用 --instances.dataset_name 替代默认读取方式
sweagent run-batch \
  ${CONFIG_ARG} \
  --agent.model.name "${MODEL_NAME}" \
  --agent.model.api_key "${ANTHROPIC_API_KEY}" \
  --instances.type "swebench" \
  --instances.dataset_name "${DATASET_NAME}" \
  --instances.split "${SPLIT}" \
  --instances.slice ":${NUM_INSTANCES}" \
  --num_workers ${NUM_WORKERS}

# 动态查找最新生成的 preds.json 补丁文件
PREDS_PATH=$(find trajectories -name "preds.json" | sort -r | head -n 1)

if [ -z "${PREDS_PATH}" ] || [ ! -f "${PREDS_PATH}" ]; then
    echo "❌ 阶段 1 失败: 未能搜寻到生成的 preds.json！"
    exit 1
fi

echo "✅ 阶段 1 完成！Patch 汇总文件位置: ${PREDS_PATH}"

# ------------------------------------------------------------------------------
# 4. 第二阶段: 运行 SWE-bench 单元测试校验
# ------------------------------------------------------------------------------
echo -e "\n[Phase 2/2] 正在使用 SWE-bench 官方 Evaluation Harness 进行单元测试校验..."

if ! python3 -c "import swebench" &> /dev/null; then
    echo "ℹ️ 正在安装 swebench 评估依赖包..."
    pip install swebench -q
fi

python3 -m swebench.harness.run_evaluation \
  --dataset_name "${DATASET_NAME}" \
  --split "${SPLIT}" \
  --predictions_path "${PREDS_PATH}" \
  --max_workers ${NUM_WORKERS} \
  --run_id "eval_${EXP_NAME}"

echo "=========================================================="
echo "🎉 自动化评测全流程顺利完成！"
echo "Patch 存储位置: ${PREDS_PATH}"
echo "=========================================================="