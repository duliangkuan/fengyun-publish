# cookie_alert.ps1 — 检测 we-mp-rss cookie 失效 + 推送企微告警
#
# 机制:
#   1. 抽 wechat-deepseek feed(/feed/MP_WXS_3949607775.atom),看 <entry> 是否存在
#   2. 失效 → 推企微 webhook(复用 TrendRadar 已配置的 webhook)
#   3. 去重:state 文件记录上次告警状态,失效持续时不重复 push,恢复时清除 state
#
# 触发:
#   Windows 计划任务 "WeMpRssCookieAlert",每 2 小时跑一次
#
# 关联:
#   .\tools\preflight.ps1 第 3 项(cookie 新鲜度)
#   D:\Dev\TrendRadar\config\config.yaml notification.channels.wework.webhook_url

[CmdletBinding()]
param(
    [switch]$Force  # 强制 push 一次(测试用)
)

$ErrorActionPreference = "Continue"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

# ============================================================
# 配置
# ============================================================
$WEMP_FEED_URL = "http://localhost:8001/feed/MP_WXS_3949607775.atom?limit=3"  # DeepSeek
$WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0d7d5bad-70f7-4cf3-8413-7681b64bacf1"
$STATE_FILE = "D:\Dev\ai-wechat-pipeline\output\cookie_alert_state.json"

# 加载 TrendRadar/.env 获取 EMAIL_FROM / EMAIL_TO / EMAIL_PASSWORD
$envFile = "D:\Dev\TrendRadar\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $idx = $line.IndexOf("=")
            $key = $line.Substring(0, $idx).Trim()
            $val = $line.Substring($idx + 1).Trim().Trim('"').Trim("'")
            Set-Item -Path "env:$key" -Value $val
        }
    }
}

# ============================================================
# 邮件发送函数(走 QQ SMTP)
# ============================================================
function Send-AlertEmail {
    param([string]$Subject, [string]$Body)
    if (-not $env:EMAIL_FROM -or -not $env:EMAIL_PASSWORD -or -not $env:EMAIL_TO) {
        Write-Host "[skip] EMAIL_FROM / PASSWORD / TO 未配置,跳过邮件" -ForegroundColor Gray
        return
    }
    try {
        # QQ 邮箱:587 STARTTLS(.NET SmtpClient 支持)而非 465 implicit SSL(.NET 不原生支持)
        $smtp = New-Object Net.Mail.SmtpClient("smtp.qq.com", 587)
        $smtp.EnableSsl = $true
        $smtp.Credentials = New-Object Net.NetworkCredential($env:EMAIL_FROM, $env:EMAIL_PASSWORD)
        $msg = New-Object Net.Mail.MailMessage
        $msg.From = $env:EMAIL_FROM
        $msg.To.Add($env:EMAIL_TO)
        $msg.Subject = $Subject
        $msg.Body = $Body
        $msg.IsBodyHtml = $false
        $msg.BodyEncoding = [System.Text.Encoding]::UTF8
        $msg.SubjectEncoding = [System.Text.Encoding]::UTF8
        $smtp.Send($msg)
        Write-Host "[OK] 邮件已发到 $($env:EMAIL_TO)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] 邮件发送失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ============================================================
# 1. 检测 cookie 是否活
# ============================================================
$alive = $false
$detail = ""
try {
    $resp = Invoke-WebRequest -Uri $WEMP_FEED_URL -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($resp.StatusCode -eq 200 -and $resp.Content -match "<entry>") {
        $alive = $true
        $detail = "DeepSeek feed 含 entry,cookie 有效"
    } elseif ($resp.StatusCode -eq 200) {
        $alive = $false
        $detail = "feed HTTP 200 但无 entry,cookie 可能过期"
    } else {
        $alive = $false
        $detail = "HTTP $($resp.StatusCode)"
    }
} catch {
    $alive = $false
    $detail = "无响应/连接拒绝: $($_.Exception.Message)"
}

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$now] cookie alive: $alive ($detail)"

# ============================================================
# 2. 读上次 state
# ============================================================
$prev_alerted = $false
if (Test-Path $STATE_FILE) {
    try {
        $state = Get-Content $STATE_FILE -Raw | ConvertFrom-Json
        $prev_alerted = [bool]$state.alerted
    } catch { }
}

# ============================================================
# 3. 决策:要不要推送
# ============================================================
$should_push = $false
$msg_type = ""
if ($Force) {
    # -Force 强制推一条测试消息(模拟失效场景)
    $should_push = $true
    $msg_type = "TEST"
} elseif (-not $alive -and -not $prev_alerted) {
    # cookie 失效 + 之前没告警过 = 第一次告警
    $should_push = $true
    $msg_type = "FAIL"
} elseif ($alive -and $prev_alerted) {
    # cookie 恢复 + 之前告警过 = 恢复通知
    $should_push = $true
    $msg_type = "RECOVER"
}

# ============================================================
# 4. 推送企微
# ============================================================
if ($should_push) {
    if ($msg_type -eq "FAIL") {
        $title = "we-mp-rss cookie 失效"
        $body = @"
[AI 公众号信源系统]
告警: we-mp-rss cookie 失效或公众号无新文
检测时间: $now
详情: $detail
影响: 16 个公众号 feed 拉空(包括 DeepSeek/Kimi/智谱/通义/MiniMax/卡兹克 等)

救场操作(30 秒):
1. 浏览器打开 http://localhost:8001
2. 看到二维码 → 微信扫码登录
3. 回到本机 cookie 自动续期

恢复后系统自动检测,不需要再操作。
"@
    } elseif ($msg_type -eq "RECOVER") {
        $title = "we-mp-rss cookie 已恢复"
        $body = @"
[AI 公众号信源系统]
恢复: we-mp-rss cookie 已重新生效
检测时间: $now
详情: $detail

16 个公众号 feed 已恢复正常拉取。
"@
    } else {
        # TEST
        $title = "[TEST] cookie_alert 链路测试"
        $body = @"
[AI 公众号信源系统]
这是 cookie_alert.ps1 双通道(企微 + 邮件)测试
检测时间: $now
当前 cookie 状态: $(if ($alive) { 'alive' } else { 'fail' }) ($detail)

实际告警内容会包含 we-mp-rss 失效详情 + 救场指南。
"@
    }

    # 推企微
    $payload = @{
        msgtype = "markdown"
        markdown = @{
            content = "## $title`n`n$body"
        }
    } | ConvertTo-Json -Depth 5 -Compress

    try {
        $resp = Invoke-WebRequest `
            -Uri $WEBHOOK_URL `
            -Method POST `
            -Body $payload `
            -ContentType "application/json; charset=utf-8" `
            -UseBasicParsing `
            -TimeoutSec 10
        Write-Host "[OK] 已推送企微通知($msg_type)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] 企微推送失败: $($_.Exception.Message)" -ForegroundColor Red
    }

    # 发邮件(走 QQ SMTP,.env 加载的 EMAIL_FROM/PASSWORD/TO)
    Send-AlertEmail -Subject $title -Body $body
}

# ============================================================
# 5. 更新 state
# ============================================================
$new_state = @{
    alerted = (-not $alive)
    last_check = $now
    last_detail = $detail
} | ConvertTo-Json
$state_dir = Split-Path $STATE_FILE -Parent
if (-not (Test-Path $state_dir)) { New-Item -ItemType Directory -Path $state_dir -Force | Out-Null }
$new_state | Out-File -FilePath $STATE_FILE -Encoding utf8

Write-Host "[$now] state 更新:alerted=$(-not $alive)"
