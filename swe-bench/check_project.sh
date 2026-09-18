#!/bin/bash
# 项目完整性检查

echo "🔍 检查项目完整性..."
echo ""

MISSING=0
TOTAL=0

check_file() {
    TOTAL=$((TOTAL + 1))
    if [ -f "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ $1 (缺失)"
        MISSING=$((MISSING + 1))
    fi
}

check_executable() {
    TOTAL=$((TOTAL + 1))
    if [ -f "$1" ] && [ -x "$1" ]; then
        echo "✓ $1 (可执行)"
    elif [ -f "$1" ]; then
        echo "⚠ $1 (存在但不可执行)"
        chmod +x "$1"
        echo "  → 已设置执行权限"
    else
        echo "✗ $1 (缺失)"
        MISSING=$((MISSING + 1))
    fi
}

echo "核心文件:"
check_file "run_swe_agent.py"
check_file "run_benchmark.py"
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file "requirements.txt"

echo ""
echo "配置文件:"
check_file ".env.example"
check_file ".gitignore"
check_file ".dockerignore"

echo ""
echo "脚本文件:"
check_executable "deploy.sh"
check_executable "test_setup.sh"

echo ""
echo "文档文件:"
check_file "README.md"
check_file "QUICKSTART.md"
check_file "DEPLOY_GUIDE.md"
check_file "FILES.md"
check_file "SUMMARY.md"

echo ""
echo "================================"
if [ $MISSING -eq 0 ]; then
    echo "✅ 所有 $TOTAL 个文件检查通过！"
    echo ""
    echo "下一步:"
    echo "1. cp .env.example .env"
    echo "2. 编辑 .env 填入 ANTHROPIC_API_KEY"
    echo "3. ./test_setup.sh"
    echo "4. ./deploy.sh"
else
    echo "❌ 发现 $MISSING 个问题，共检查 $TOTAL 个文件"
    exit 1
fi
