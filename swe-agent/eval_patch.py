#!/usr/bin/env python3
import json
from datasets import load_dataset

# 加载数据集
print("正在加载 SWE-bench_Lite 数据集...")
dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

# 加载预测
preds_path = "/root/swebench/SWE-agent/trajectories/root/opus5__anthropic--claude-opus-5__t-1.00__p-1.00__c-10.00___swe_bench_lite_test/preds.json"
print(f"正在加载预测文件: {preds_path}")
with open(preds_path, "r") as f:
    predictions = json.load(f)

# 合并数据集和预测
merged = []
for item in dataset:
    instance_id = item["instance_id"]
    if instance_id in predictions:
        item["model_patch"] = predictions[instance_id]["model_patch"]
        item["model_name_or_path"] = predictions[instance_id]["model_name_or_path"]
        merged.append(item)

# 保存合并后的数据
output_path = "/tmp/merged_predictions.json"
with open(output_path, "w") as f:
    json.dump(merged, f, indent=2)

print(f"✅ 合并完成，共 {len(merged)} 个实例")
print(f"✅ 输出文件: {output_path}")
print("\n现在可以运行评估：")
print(f"python3 -m swebench.harness.run_evaluation \\")
print(f"  --predictions_path {output_path} \\")
print(f"  --max_workers 2 \\")
print(f"  --run_id eval_test")
