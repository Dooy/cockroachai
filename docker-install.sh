#!/bin/bash

# Step 1: 更新apt包索引
sudo apt-get update

# Step 2: 安装必要的软件包
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

# Step 3: 添加 Docker 的官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Step 4: 设置 Docker 的稳定版本仓库
echo "deb [signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 5: 更新 apt 包索引
sudo apt-get update

# Step 6: 安装 Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Step 7: 验证 Docker 是否安装成功
docker --version