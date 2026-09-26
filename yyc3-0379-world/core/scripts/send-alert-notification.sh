#!/bin/bash

# 告警通知脚本
# 支持：邮件、钉钉、企业微信

NOTIFICATION_TYPE="${1:-email}"
ALERT_TITLE="${2:-告警通知}"
ALERT_MESSAGE="${3:-检测到系统告警}"
ALERT_LEVEL="${4:-warning}"

echo "发送告警通知..."
echo "类型: $NOTIFICATION_TYPE"
echo "标题: $ALERT_TITLE"
echo "消息: $ALERT_MESSAGE"
echo "级别: $ALERT_LEVEL"

# 邮件通知
send_email() {
    local title="$1"
    local message="$2"
    local level="$3"
    
    local recipient="${ALERT_EMAIL_RECIPIENT:-admin@example.com}"
    local sender="${ALERT_EMAIL_SENDER:-noreply@example.com}"
    local smtp_server="${ALERT_SMTP_SERVER:-smtp.example.com}"
    local smtp_port="${ALERT_SMTP_PORT:-587}"
    local smtp_user="${ALERT_SMTP_USER:-user}"
    local smtp_password="${ALERT_SMTP_PASSWORD:-password}"
    
    echo "发送邮件通知..."
    
    # 使用 sendmail 或 mail 命令
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "[$level] $title" "$recipient"
        echo "✓ 邮件通知已发送"
    elif command -v sendmail &> /dev/null; then
        (
            echo "Subject: [$level] $title"
            echo "From: $sender"
            echo "To: $recipient"
            echo ""
            echo "$message"
        ) | sendmail -t
        echo "✓ 邮件通知已发送"
    else
        echo "⚠ 未找到邮件发送工具"
    fi
}

# 钉钉通知
send_dingtalk() {
    local title="$1"
    local message="$2"
    local level="$3"
    
    local webhook_url="${ALERT_DINGTALK_WEBHOOK}"
    
    if [ -z "$webhook_url" ]; then
        echo "⚠ 未配置钉钉 Webhook URL"
        return 1
    fi
    
    echo "发送钉钉通知..."
    
    # 根据告警级别设置颜色
    local color="#FF0000"
    case "$level" in
        critical) color="#FF0000" ;;
        warning)  color="#FFCC00" ;;
        info)     color="#00CC00" ;;
    esac
    
    local payload=$(cat <<EOF
{
  "msgtype": "markdown",
  "markdown": {
    "title": "[$level] $title",
    "text": "### [$level] $title\n\n$message"
  },
  "at": {
    "atMobiles": [],
    "isAtAll": false
  }
}
EOF
)
    
    curl -s -X POST "$webhook_url" \
        -H "Content-Type: application/json" \
        -d "$payload" > /dev/null
    
    echo "✓ 钉钉通知已发送"
}

# 企业微信通知
send_wechat() {
    local title="$1"
    local message="$2"
    local level="$3"
    
    local webhook_url="${ALERT_WECHAT_WEBHOOK}"
    
    if [ -z "$webhook_url" ]; then
        echo "⚠ 未配置企业微信 Webhook URL"
        return 1
    fi
    
    echo "发送企业微信通知..."
    
    local payload=$(cat <<EOF
{
  "msgtype": "markdown",
  "markdown": {
    "content": "## [$level] $title\n\n$message"
  }
}
EOF
)
    
    curl -s -X POST "$webhook_url" \
        -H "Content-Type: application/json" \
        -d "$payload" > /dev/null
    
    echo "✓ 企业微信通知已发送"
}

# 主逻辑
case "$NOTIFICATION_TYPE" in
    email)
        send_email "$ALERT_TITLE" "$ALERT_MESSAGE" "$ALERT_LEVEL"
        ;;
    dingtalk)
        send_dingtalk "$ALERT_TITLE" "$ALERT_MESSAGE" "$ALERT_LEVEL"
        ;;
    wechat)
        send_wechat "$ALERT_TITLE" "$ALERT_MESSAGE" "$ALERT_LEVEL"
        ;;
    all)
        send_email "$ALERT_TITLE" "$ALERT_MESSAGE" "$ALERT_LEVEL"
        send_dingtalk "$ALERT_TITLE" "$ALERT_MESSAGE" "$ALERT_LEVEL"
        send_wechat "$ALERT_TITLE" "$ALERT_MESSAGE" "$ALERT_LEVEL"
        ;;
    *)
        echo "错误: 不支持的通知类型 '$NOTIFICATION_TYPE'"
        echo "支持类型: email, dingtalk, wechat, all"
        exit 1
        ;;
esac

echo ""
echo "告警通知发送完成"