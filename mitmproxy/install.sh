#!/bin/bash

# 定义虚拟环境目录名称
VENV_DIR="./mitm"

echo "开始安装 mitmproxy 环境..."

# 1. 检查 Python3 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到 python3，请先安装 (sudo apt install python3)"
    exit 1
fi

# 2. 安装必要的系统依赖 (针对 Ubuntu)
echo "正在安装必要的系统依赖..."
sudo apt update && sudo apt install -y python3-venv python3-pip

# 3. 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "正在创建虚拟环境 $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "虚拟环境已存在，跳过创建。"
fi

# 4. 在虚拟环境中安装 mitmproxy
echo "正在安装/更新 mitmproxy..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install mitmproxy

echo "------------------------------------------------"
echo "安装完成！"
echo "你可以通过以下命令启动项目："
echo "source $VENV_DIR/bin/activate"
echo "mitmdump --set listen_host=0.0.0.0 --set block_global=false"
echo "------------------------------------------------"