#!/usr/bin/env python3
"""
SWE-bench Lite 测试脚本
使用官方 SWE-agent + Claude Opus 5
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # 从环境变量读取配置
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    model = os.getenv("MODEL", "claude-opus-5")
    num_tasks = os.getenv("NUM_TASKS", "2")

    if not api_key:
        print("错误: 缺少 ANTHROPIC_API_KEY 环境变量")
        sys.exit(1)

    # 确保输出目录存在
    output_dir = Path("/app/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 开始测试...")
    print(f"📦 模型: {model}")
    print(f"📊 任务数: {num_tasks}")
    print(f"🔗 API: {base_url}")
    print()

    # 使用 sweagent CLI（正确的方式）
    cmd = [
        "sweagent", "run",
        "--model_name", model,
        "--data_path", "princeton-nlp/SWE-bench_Lite",
        "--split", "test",
        "--instance_filter", f"0:{num_tasks}",
        "--output_dir", str(output_dir),
        "--per_instance_cost_limit", "10.0",
    ]

    # 设置环境变量
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = api_key
    if base_url != "https://api.anthropic.com":
        env["ANTHROPIC_BASE_URL"] = base_url

    # 运行 SWE-agent
    try:
        subprocess.run(cmd, env=env, check=True)
        print("\n✅ 测试完成！")
        print(f"📁 结果保存在: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
