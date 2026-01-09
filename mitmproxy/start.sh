#!/bin/bash

# --- 配置信息 ---
VENV_PATH="./mitm/bin/activate"
PORT=8080
USER_AUTH="suno:Aa112211"
SCRIPT_NAME="./modify.py"
# 如果有特定域名需求，可以把上面提到的 ignore-hosts 加上，目前此脚本为全量代理

# 1. 检查虚拟环境
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ 错误: 未找到虚拟环境，请确认路径是否正确: ./mitm"
    exit 1
fi

# 2. 激活虚拟环境
source "$VENV_PATH"

# 3. 清理已存在的 mitmdump 进程 (避免端口占用)
# 使用 pkill 匹配包含特定端口和名称的进程
pkill -f "mitmdump.*@$PORT" && echo "清理旧进程..."

echo "正在获取公网 IP..."
PUBLIC_IP=$(curl -s myip.ipip.net | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -n 1)

if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP="[无法获取公网IP，请手动检查]"
fi

# 4. 启动程序 > /dev/null 2>&1 & --proxyauth "$USER_AUTH" \
echo "正在后台启动 mitmdump (端口: $PORT, 用户: suno)..."
nohup mitmdump \
    -s "$SCRIPT_NAME" \
    --set listen_host=0.0.0.0 \
    --mode regular@$PORT \
    --mode socks5@8081 \
    --set block_global=false \
    --set flow_detail=0 \
    --set authentication "$USER_AUTH" \
    > /dev/null 2>&1 &

# 5. 验证是否启动成功
sleep 2
PID=$(pgrep -f "mitmdump.*@$PORT")
if [ -n "$PID" ]; then
    echo "✅ 启动成功！"
    echo "进程 PID: $PID"
    echo "代理地址: http://$USER_AUTH@$PUBLIC_IP:$PORT"
    echo "代理地址: socks5://$USER_AUTH@$PUBLIC_IP:8081"
    echo "内网代理地址: http://$USER_AUTH@127.0.0.1:$PORT"
else
    echo "❌ 启动失败，请检查端口 $PORT 是否被占用或 Python 环境是否正常。"
fi