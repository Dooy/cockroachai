# 防暴力破解系统

自动监控系统日志，检测并封禁暴力破解的 IP 地址。

## 功能特性

- 实时监控 journalctl 日志
- 自动统计时间窗口内的失败登录次数
- 达到阈值自动使用 iptables 封禁 IP
- 支持 IPv4 和 IPv6
- 支持多服务监控（SSH、Nginx 等）
- 可配置时间窗口和失败次数阈值
- 支持临时封禁和永久封禁
- IP 白名单功能
- 手动封禁/解封功能

## 文件说明

- `anti-bruteforce.sh` - 主程序脚本
- `anti-bruteforce.conf` - 配置文件
- `anti-bruteforce.service` - systemd 服务文件

## 配置说明

编辑 `anti-bruteforce.conf`:

```bash
# 时间窗口（分钟），默认 30 分钟
TIME_WINDOW=30

# 失败次数阈值，默认 100 次
FAIL_THRESHOLD=100

# 封禁时长（分钟），0 表示永久封禁，默认 1440 分钟（24小时）
BAN_DURATION=1440

# 日志文件路径
LOG_FILE=/var/log/anti-bruteforce.log

# 白名单 IP（用空格分隔）
WHITELIST_IPS="127.0.0.1 ::1"

# 监控的服务（可以是 sshd、nginx 等，用空格分隔）
MONITOR_SERVICES="sshd"
```

## 安装步骤

### 1. 赋予执行权限

```bash
chmod +x anti-bruteforce.sh
```

### 2. 测试运行

先手动运行测试是否正常：

```bash
sudo ./anti-bruteforce.sh init    # 初始化 iptables 链
sudo ./anti-bruteforce.sh stats   # 查看当前状态
```

### 3. 安装为 systemd 服务

```bash
# 进入 anti 目录
cd /path/to/mydownload/anti

# 修改 service 文件中的路径
sudo sed -i "s|/path/to/mydownload/anti|$(pwd)|g" anti-bruteforce.service

# 复制 service 文件到 systemd 目录
sudo cp anti-bruteforce.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start anti-bruteforce

# 查看服务状态
sudo systemctl status anti-bruteforce

# 设置开机自启
sudo systemctl enable anti-bruteforce
```

### 4. 查看日志

```bash
# 查看服务日志
sudo journalctl -u anti-bruteforce -f

# 查看程序日志（如果配置了 LOG_FILE）
sudo tail -f /var/log/anti-bruteforce.log
```

## 使用方法

### 监控模式（后台运行）

```bash
sudo ./anti-bruteforce.sh monitor
```

### 查看统计信息

```bash
sudo ./anti-bruteforce.sh stats
```

### 手动封禁 IP

```bash
sudo ./anti-bruteforce.sh ban 192.168.1.100
```

### 手动解封 IP

```bash
sudo ./anti-bruteforce.sh unban 192.168.1.100
```

### 清空所有封禁

```bash
sudo ./anti-bruteforce.sh clear
```

### 初始化 iptables 链

```bash
sudo ./anti-bruteforce.sh init
```

## 工作原理

1. 脚本每分钟扫描一次 journalctl 日志
2. 统计指定时间窗口（默认 30 分钟）内每个 IP 的失败登录次数
3. 如果某个 IP 的失败次数超过阈值（默认 100 次），自动封禁该 IP
4. 封禁使用 iptables 的自定义链 `ANTI_BRUTEFORCE`
5. 如果设置了封禁时长，到期后自动解封

## 支持的服务

- **sshd**: SSH 登录失败检测
- **nginx**: HTTP 401/403 错误检测
- 其他服务：通用失败关键词检测

可以在配置文件中添加多个服务，用空格分隔：

```bash
MONITOR_SERVICES="sshd nginx"
```

## 注意事项

1. **必须使用 root 权限运行**
2. **务必配置白名单**，避免误封自己的 IP
3. 首次使用建议先调高阈值，观察一段时间后再调整
4. 封禁规则在系统重启后会丢失，需要配合 systemd 服务或 iptables-persistent
5. 如果使用 Docker，需要注意 iptables 规则的优先级

## 持久化 iptables 规则（可选）

如果希望封禁规则在重启后保留：

```bash
# 安装 iptables-persistent
sudo apt install iptables-persistent

# 保存当前规则
sudo netfilter-persistent save
```

## 卸载

```bash
# 停止服务
sudo systemctl stop anti-bruteforce
sudo systemctl disable anti-bruteforce

# 删除服务文件
sudo rm /etc/systemd/system/anti-bruteforce.service
sudo systemctl daemon-reload

# 清空封禁规则
sudo ./anti-bruteforce.sh clear

# 删除 iptables 链
sudo iptables -D INPUT -j ANTI_BRUTEFORCE
sudo iptables -X ANTI_BRUTEFORCE
sudo ip6tables -D INPUT -j ANTI_BRUTEFORCE 2>/dev/null
sudo ip6tables -X ANTI_BRUTEFORCE 2>/dev/null
```

## 故障排查

### 服务无法启动

检查日志：
```bash
sudo journalctl -u anti-bruteforce -n 50
```

### 没有检测到攻击

1. 确认 journalctl 可以读取到日志：
   ```bash
   sudo journalctl -u sshd --since "30 minutes ago" | grep -i failed
   ```

2. 检查服务名称是否正确（sshd vs ssh）

3. 调整日志匹配模式

### 误封了自己的 IP

```bash
# 立即解封
sudo ./anti-bruteforce.sh unban YOUR_IP

# 添加到白名单
echo 'WHITELIST_IPS="127.0.0.1 ::1 YOUR_IP"' >> anti-bruteforce.conf
```

## 性能影响

- 每分钟扫描一次日志，对系统性能影响极小
- iptables DROP 规则效率高，对网络性能影响可忽略
- 建议封禁的 IP 数量不要超过 10000 个

## 安全建议

1. 配合使用其他安全措施（fail2ban、密钥登录等）
2. 定期审查封禁列表和日志
3. 为重要 IP 设置白名单
4. 合理设置时间窗口和阈值，避免误封
