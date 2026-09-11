#!/bin/bash

# 防暴力破解脚本
# 监控 journalctl 日志，统计失败登录次数，使用 iptables 封禁恶意 IP

set -euo pipefail

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/anti-bruteforce.conf"
STATE_FILE="${SCRIPT_DIR}/.anti-bruteforce.state"
BANNED_IPS_FILE="${SCRIPT_DIR}/.banned_ips"

# 加载配置
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 默认值
TIME_WINDOW=${TIME_WINDOW:-30}
FAIL_THRESHOLD=${FAIL_THRESHOLD:-100}
BAN_DURATION=${BAN_DURATION:-1440}
LOG_FILE=${LOG_FILE:-/var/log/anti-bruteforce.log}
MONITOR_SERVICES=${MONITOR_SERVICES:-"sshd"}

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 权限运行此脚本"
    exit 1
fi

# 初始化 iptables 链
init_iptables() {
    # 检查是否存在 ANTI_BRUTEFORCE 链
    if ! iptables -L ANTI_BRUTEFORCE -n >/dev/null 2>&1; then
        log "创建 iptables 链: ANTI_BRUTEFORCE"
        iptables -N ANTI_BRUTEFORCE
        iptables -I INPUT 1 -j ANTI_BRUTEFORCE
    fi

    # IPv6 支持
    if command -v ip6tables >/dev/null 2>&1; then
        if ! ip6tables -L ANTI_BRUTEFORCE -n >/dev/null 2>&1; then
            log "创建 ip6tables 链: ANTI_BRUTEFORCE"
            ip6tables -N ANTI_BRUTEFORCE
            ip6tables -I INPUT 1 -j ANTI_BRUTEFORCE
        fi
    fi
}

# 检查 IP 是否在 CIDR 网段内
ip_in_cidr() {
    local ip="$1"
    local cidr="$2"

    # 如果不包含 /，则是单个 IP，直接比较
    if [[ ! "$cidr" =~ / ]]; then
        [ "$ip" = "$cidr" ] && return 0 || return 1
    fi

    # 解析 CIDR
    local network="${cidr%/*}"
    local mask="${cidr#*/}"

    # 转换 IP 为整数
    ip_to_int() {
        local ip=$1
        local a b c d
        IFS=. read -r a b c d <<< "$ip"
        echo $((a * 256 ** 3 + b * 256 ** 2 + c * 256 + d))
    }

    # 计算网络地址
    local ip_int=$(ip_to_int "$ip")
    local network_int=$(ip_to_int "$network")
    local mask_int=$(((0xFFFFFFFF << (32 - mask)) & 0xFFFFFFFF))

    # 检查 IP 是否在网段内
    [ $((ip_int & mask_int)) -eq $((network_int & mask_int)) ] && return 0 || return 1
}

# 检查 IP 是否在白名单
is_whitelisted() {
    local ip="$1"

    # 跳过 IPv6（暂不支持 IPv6 CIDR 匹配）
    if [[ "$ip" =~ : ]]; then
        for white_ip in $WHITELIST_IPS; do
            if [ "$ip" = "$white_ip" ]; then
                return 0
            fi
        done
        return 1
    fi

    # IPv4：支持单个 IP 和 CIDR 网段
    for white_entry in $WHITELIST_IPS; do
        if ip_in_cidr "$ip" "$white_entry"; then
            return 0
        fi
    done
    return 1
}

# 检查 IP 是否已被封禁
is_banned() {
    local ip="$1"
    if iptables -L ANTI_BRUTEFORCE -n | grep -q "$ip"; then
        return 0
    fi
    return 1
}

# 封禁 IP
ban_ip() {
    local ip="$1"
    local reason="${2:-暴力破解}"

    # 检查白名单
    if is_whitelisted "$ip"; then
        log "IP $ip 在白名单中，跳过封禁"
        return
    fi

    # 检查是否已封禁
    if is_banned "$ip"; then
        log "IP $ip 已被封禁"
        return
    fi

    # 判断 IPv4 或 IPv6
    if echo "$ip" | grep -q ':'; then
        # IPv6
        log "封禁 IPv6: $ip ($reason)"
        ip6tables -I ANTI_BRUTEFORCE 1 -s "$ip" -j DROP
    else
        # IPv4
        log "封禁 IPv4: $ip ($reason)"
        iptables -I ANTI_BRUTEFORCE 1 -s "$ip" -j DROP
    fi

    # 记录封禁信息
    echo "$(date +%s)|$ip|$reason" >> "$BANNED_IPS_FILE"
}

# 解封 IP
unban_ip() {
    local ip="$1"

    # 判断 IPv4 或 IPv6
    if echo "$ip" | grep -q ':'; then
        # IPv6
        if ip6tables -L ANTI_BRUTEFORCE -n | grep -q "$ip"; then
            log "解封 IPv6: $ip"
            ip6tables -D ANTI_BRUTEFORCE -s "$ip" -j DROP
        fi
    else
        # IPv4
        if iptables -L ANTI_BRUTEFORCE -n | grep -q "$ip"; then
            log "解封 IPv4: $ip"
            iptables -D ANTI_BRUTEFORCE -s "$ip" -j DROP
        fi
    fi
}

# 清理过期的封禁
cleanup_expired_bans() {
    if [ "$BAN_DURATION" -eq 0 ]; then
        return
    fi

    if [ ! -f "$BANNED_IPS_FILE" ]; then
        return
    fi

    local current_time=$(date +%s)
    local ban_seconds=$((BAN_DURATION * 60))
    local temp_file="${BANNED_IPS_FILE}.tmp"

    > "$temp_file"

    while IFS='|' read -r ban_time ip reason; do
        local elapsed=$((current_time - ban_time))
        if [ $elapsed -lt $ban_seconds ]; then
            echo "$ban_time|$ip|$reason" >> "$temp_file"
        else
            log "解封过期 IP: $ip (已封禁 $((elapsed / 60)) 分钟)"
            unban_ip "$ip"
        fi
    done < "$BANNED_IPS_FILE"

    mv "$temp_file" "$BANNED_IPS_FILE"
}

# 解析日志并提取失败的 IP
extract_failed_ips() {
    local service="$1"
    local since_time="$2"

    case "$service" in
        sshd)
            # SSH 失败登录模式
            journalctl -u ssh -u sshd --since "$since_time" 2>/dev/null | \
                grep -iE "Failed password|Invalid user|Connection closed by authenticating user" | \
                grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-f:]+:+)+[0-9a-f]+' | \
                sort | uniq -c | sort -rn
            ;;
        nginx)
            # Nginx 失败登录模式（401/403）
            journalctl -u nginx --since "$since_time" 2>/dev/null | \
                grep -E '" (401|403) ' | \
                grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-f:]+:+)+[0-9a-f]+' | \
                sort | uniq -c | sort -rn
            ;;
        *)
            # 通用模式：查找 "failed" "invalid" "unauthorized" 等关键词
            journalctl -u "$service" --since "$since_time" 2>/dev/null | \
                grep -iE "fail|invalid|unauthorized|denied" | \
                grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-f:]+:+)+[0-9a-f]+' | \
                sort | uniq -c | sort -rn
            ;;
    esac
}

# 主监控循环
monitor_loop() {
    log "启动防暴力破解监控 (时间窗口: ${TIME_WINDOW}分钟, 阈值: ${FAIL_THRESHOLD}次)"
    log "监控服务: $MONITOR_SERVICES"

    # 初始化
    init_iptables
    touch "$BANNED_IPS_FILE"

    while true; do
        # 清理过期封禁
        cleanup_expired_bans

        # 计算时间窗口
        local since_time="${TIME_WINDOW} minutes ago"

        # 遍历监控的服务
        for service in $MONITOR_SERVICES; do
            log "检查服务: $service"

            # 提取失败 IP 及次数
            while read -r count ip; do
                # 跳过空行
                [ -z "$ip" ] && continue

                log "检测到 IP: $ip, 失败次数: $count"

                # 检查是否超过阈值
                if [ "$count" -ge "$FAIL_THRESHOLD" ]; then
                    ban_ip "$ip" "${service} 暴力破解 (${count}次失败)"
                fi
            done < <(extract_failed_ips "$service" "$since_time")
        done

        # 休眠一段时间再检查（避免频繁扫描）
        sleep 60
    done
}

# 显示统计信息
show_stats() {
    echo "=== 防暴力破解统计 ==="
    echo "当前封禁的 IP 数量:"
    iptables -L ANTI_BRUTEFORCE -n | grep -c DROP || echo "0"

    echo ""
    echo "已封禁的 IP 列表:"
    iptables -L ANTI_BRUTEFORCE -n -v

    if command -v ip6tables >/dev/null 2>&1; then
        echo ""
        echo "IPv6 已封禁列表:"
        ip6tables -L ANTI_BRUTEFORCE -n -v
    fi

    if [ -f "$BANNED_IPS_FILE" ]; then
        echo ""
        echo "封禁记录 (最近 10 条):"
        tail -10 "$BANNED_IPS_FILE" | while IFS='|' read -r ban_time ip reason; do
            echo "  $(date -d @$ban_time '+%Y-%m-%d %H:%M:%S') | $ip | $reason"
        done
    fi
}

# 手动封禁 IP
manual_ban() {
    local ip="$1"
    ban_ip "$ip" "手动封禁"
}

# 手动解封 IP
manual_unban() {
    local ip="$1"
    unban_ip "$ip"

    # 从记录中删除
    if [ -f "$BANNED_IPS_FILE" ]; then
        grep -v "|$ip|" "$BANNED_IPS_FILE" > "${BANNED_IPS_FILE}.tmp" || true
        mv "${BANNED_IPS_FILE}.tmp" "$BANNED_IPS_FILE"
    fi
}

# 清空所有封禁
clear_all_bans() {
    log "清空所有封禁"
    iptables -F ANTI_BRUTEFORCE 2>/dev/null || true
    if command -v ip6tables >/dev/null 2>&1; then
        ip6tables -F ANTI_BRUTEFORCE 2>/dev/null || true
    fi
    > "$BANNED_IPS_FILE"
}

# 命令行参数处理
case "${1:-monitor}" in
    monitor)
        monitor_loop
        ;;
    stats)
        show_stats
        ;;
    ban)
        if [ -z "${2:-}" ]; then
            echo "用法: $0 ban <IP>"
            exit 1
        fi
        manual_ban "$2"
        ;;
    unban)
        if [ -z "${2:-}" ]; then
            echo "用法: $0 unban <IP>"
            exit 1
        fi
        manual_unban "$2"
        ;;
    clear)
        clear_all_bans
        ;;
    init)
        init_iptables
        log "iptables 链初始化完成"
        ;;
    *)
        echo "用法: $0 {monitor|stats|ban <IP>|unban <IP>|clear|init}"
        echo ""
        echo "命令说明:"
        echo "  monitor  - 启动监控模式（默认）"
        echo "  stats    - 显示统计信息"
        echo "  ban      - 手动封禁 IP"
        echo "  unban    - 手动解封 IP"
        echo "  clear    - 清空所有封禁"
        echo "  init     - 初始化 iptables 链"
        exit 1
        ;;
esac
