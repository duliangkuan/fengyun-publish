# preflight.ps1 — AI 公众号系统启动前置自检
#
# 用法:
#   .\tools\preflight.ps1
#   .\tools\preflight.ps1 -Strict     # 任一项 FAIL 则 exit 1(供 CI / pipeline 拦截用)
#   .\tools\preflight.ps1 -Verbose    # 显示每项详细输出
#
# 检查范围(2026-05-25 v1.0):
#   1. Docker Desktop 运行状态
#   2. we-mp-rss 容器(localhost:8001)
#   3. we-mp-rss cookie 新鲜度(抽 1 个 feed 看内容非空)
#   4. TrendRadar latest_daily.md mtime ≤ 36h
#   5. HF Spaces RSSHub 自建实例(配置后激活)
#   6. Email-to-RSS Worker(配置后激活)
#   7. rsshub.app 公共实例(预期 403,提醒已挂)
#
# 退出码:
#   0 = 所有 P0 通过(可跑 ship pipeline)
#   1 = P0 失败(strict 模式)或 -Strict 下任一 FAIL
#
# 关联:
#   D:\Dev\ai-wechat-pipeline\WRITE_AGENT.md Preflight 红线
#   D:\Dev\ai-wechat-pipeline\docs\rsshub_hf_spaces_setup.md
#   D:\Dev\ai-wechat-pipeline\docs\email_to_rss_setup.md

[CmdletBinding()]
param(
    [switch]$Strict,
    [switch]$VerboseMode
)

$ErrorActionPreference = "Continue"

# 强制 console 输出 UTF-8(PowerShell 5.1 Windows 默认 GBK 会乱码中文)
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

# ============================================================
# 配置(用户部署完 HF Spaces / Email-to-RSS 后填这里)
# ============================================================
$RSSHUB_URL = "http://localhost:1200"        # 本机 Docker RSSHub(diygod/rsshub:chromium-bundled)
$RSSHUB_COOKIE_TEST_PATH = "/bilibili/user/video/1567748478"  # B 站李沐 UID,无 cookie 100% 503 + 有 cookie 200,差异最稳定;知乎话题 API 已废,不适合做 lint
$EMAIL_RSS_URL = "https://rss.fengyunlove.xyz"  # Email-to-RSS Cloudflare Worker(2026-05-26 部署)
$WE_MP_RSS_PORT = 8001
$WE_MP_RSS_SAMPLE_BIZ = "MP_WXS_3949607775"  # DeepSeek 公众号
$TRENDRADAR_LATEST = "D:\Dev\TrendRadar\output\latest_daily.md"
$TRENDRADAR_MAX_AGE_HOURS = 36

# ============================================================
# 结果收集
# ============================================================
$results = @()
$p0_fail = $false
$any_fail = $false

function Add-Result {
    param(
        [string]$Name,
        [string]$Status,   # PASS / FAIL / WARN / SKIP
        [string]$Detail,
        [string]$Fix,
        [string]$Priority  # P0 / P1
    )
    $script:results += [PSCustomObject]@{
        Name = $Name
        Status = $Status
        Detail = $Detail
        Fix = $Fix
        Priority = $Priority
    }
    if ($Status -eq "FAIL") {
        $script:any_fail = $true
        if ($Priority -eq "P0") { $script:p0_fail = $true }
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host " AI 公众号系统 Preflight 自检" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 1. Docker Desktop
# ============================================================
Write-Host "[1/7] Docker Desktop ..." -NoNewline
try {
    $docker_out = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " PASS" -ForegroundColor Green
        Add-Result "Docker Desktop" "PASS" "docker daemon 响应正常" "" "P0"
    } else {
        Write-Host " FAIL" -ForegroundColor Red
        Add-Result "Docker Desktop" "FAIL" "docker daemon 未运行" "打开 Docker Desktop GUI,等其完全启动(系统托盘鲸鱼图标变绿)" "P0"
    }
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Add-Result "Docker Desktop" "FAIL" "docker 命令不存在" "安装 Docker Desktop 或检查 PATH" "P0"
}

# ============================================================
# 2. we-mp-rss 容器
# ============================================================
Write-Host "[2/7] we-mp-rss 容器 (localhost:$WE_MP_RSS_PORT) ..." -NoNewline
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$WE_MP_RSS_PORT/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-Host " PASS" -ForegroundColor Green
        Add-Result "we-mp-rss 容器" "PASS" "HTTP 200 响应" "" "P0"
    } else {
        Write-Host " WARN (HTTP $($resp.StatusCode))" -ForegroundColor Yellow
        Add-Result "we-mp-rss 容器" "WARN" "HTTP $($resp.StatusCode)" "docker logs we-mp-rss 看错误" "P0"
    }
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Add-Result "we-mp-rss 容器" "FAIL" "无响应/连接拒绝" "docker start we-mp-rss(若已建)或 docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest" "P0"
}

# ============================================================
# 3. we-mp-rss cookie 新鲜度(抽 DeepSeek 公众号 feed)
# ============================================================
Write-Host "[3/7] we-mp-rss cookie 新鲜度 ..." -NoNewline
try {
    $feed_url = "http://localhost:$WE_MP_RSS_PORT/feed/$WE_MP_RSS_SAMPLE_BIZ.atom"
    $resp = Invoke-WebRequest -Uri $feed_url -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($resp.StatusCode -eq 200 -and $resp.Content -match "<entry>") {
        Write-Host " PASS" -ForegroundColor Green
        Add-Result "cookie 新鲜度" "PASS" "DeepSeek feed 含 entry,cookie 有效" "" "P0"
    } elseif ($resp.StatusCode -eq 200) {
        Write-Host " WARN (无 entry)" -ForegroundColor Yellow
        Add-Result "cookie 新鲜度" "WARN" "feed 返回但无 entry,可能 cookie 过期或公众号无新文" "浏览器开 http://localhost:8001 确认是否要求扫码登录" "P0"
    } else {
        Write-Host " FAIL (HTTP $($resp.StatusCode))" -ForegroundColor Red
        Add-Result "cookie 新鲜度" "FAIL" "HTTP $($resp.StatusCode)" "浏览器开 http://localhost:8001 重新扫码" "P0"
    }
} catch {
    Write-Host " SKIP (we-mp-rss 不可达)" -ForegroundColor Gray
    Add-Result "cookie 新鲜度" "SKIP" "依赖项 2 失败" "先修 we-mp-rss 容器" "P0"
}

# ============================================================
# 4. TrendRadar latest_daily.md mtime
# ============================================================
Write-Host "[4/7] TrendRadar latest_daily.md 新鲜度 ..." -NoNewline
if (Test-Path $TRENDRADAR_LATEST) {
    $file = Get-Item $TRENDRADAR_LATEST
    $age = (Get-Date) - $file.LastWriteTime
    $age_hours = [math]::Round($age.TotalHours, 1)
    if ($age.TotalHours -le $TRENDRADAR_MAX_AGE_HOURS) {
        Write-Host " PASS ($age_hours h)" -ForegroundColor Green
        Add-Result "TrendRadar 新鲜度" "PASS" "mtime $($file.LastWriteTime),$age_hours h 前更新" "" "P0"
    } else {
        Write-Host " FAIL ($age_hours h > $TRENDRADAR_MAX_AGE_HOURS h)" -ForegroundColor Red
        Add-Result "TrendRadar 新鲜度" "FAIL" "已过期 $age_hours h(阈值 $TRENDRADAR_MAX_AGE_HOURS h),iti_collect 会 skip" ".\tools\run_trendradar.ps1  # 推荐:已修 GBK 编码 emoji 崩" "P0"
    }
} else {
    Write-Host " FAIL (文件不存在)" -ForegroundColor Red
    Add-Result "TrendRadar 新鲜度" "FAIL" "$TRENDRADAR_LATEST 不存在" "TrendRadar 从未跑过?.\tools\run_trendradar.ps1  # 推荐:已修 GBK 编码 emoji 崩 跑一次" "P0"
}

# ============================================================
# 5. 本机 RSSHub 容器(localhost:1200,容器 + cookie 双测)
# ============================================================
Write-Host "[5/7] 本机 RSSHub ($RSSHUB_URL) ..." -NoNewline
$rsshubAlive = $false
try {
    $resp = Invoke-WebRequest -Uri "$RSSHUB_URL/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        $rsshubAlive = $true
    }
} catch { }

if (-not $rsshubAlive) {
    Write-Host " FAIL" -ForegroundColor Red
    Add-Result "本机 RSSHub 容器" "FAIL" "$RSSHUB_URL 无响应" "docker start rsshub(若已建)或参考 docs/rsshub_cookie_setup.md" "P0"
} else {
    # 容器活,测 cookie 是否注入(用 B 站 UP 路由,503 = cookie 没配)
    try {
        $resp2 = Invoke-WebRequest -Uri "$RSSHUB_URL$RSSHUB_COOKIE_TEST_PATH" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
        if ($resp2.StatusCode -eq 200 -and $resp2.Content -match "<item>|<entry>") {
            Write-Host " PASS (容器+cookie 都 OK)" -ForegroundColor Green
            Add-Result "本机 RSSHub 容器" "PASS" "$RSSHUB_URL 容器 alive + B 站 cookie 有效" "" "P0"
        } elseif ($resp2.StatusCode -eq 200) {
            Write-Host " WARN (无 item,cookie 可能过期)" -ForegroundColor Yellow
            Add-Result "本机 RSSHub 容器" "WARN" "容器 alive,但 B 站测试 feed 无 item,cookie 可能过期" "重抓 B 站 cookie,docs/rsshub_cookie_setup.md" "P0"
        } else {
            Write-Host " WARN (cookie 未配,B 站 HTTP $($resp2.StatusCode))" -ForegroundColor Yellow
            Add-Result "本机 RSSHub 容器" "WARN" "容器 alive,但 B 站测试 503 — cookie 没注入" "docs/rsshub_cookie_setup.md 配 BILIBILI_COOKIE_* + ZHIHU_COOKIES,docker stop/rm/run" "P0"
        }
    } catch {
        Write-Host " WARN (容器活,B 站测试超时)" -ForegroundColor Yellow
        Add-Result "本机 RSSHub 容器" "WARN" "容器 alive 但 B 站路由超时" "docker logs rsshub --tail 30 看错误" "P0"
    }
}

# ============================================================
# 6. Email-to-RSS Worker(用户部署后激活)
# ============================================================
Write-Host "[6/7] Email-to-RSS Worker ..." -NoNewline
if ([string]::IsNullOrWhiteSpace($EMAIL_RSS_URL)) {
    Write-Host " SKIP (未配置)" -ForegroundColor Gray
    Add-Result "Email-to-RSS Worker" "SKIP" "EMAIL_RSS_URL 未配置" "完成 Cloudflare Workers 部署后,在本脚本顶部填 EMAIL_RSS_URL" "P1"
} else {
    try {
        $resp = Invoke-WebRequest -Uri $EMAIL_RSS_URL -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host " PASS" -ForegroundColor Green
            Add-Result "Email-to-RSS Worker" "PASS" "HTTP 200" "" "P1"
        } else {
            Write-Host " WARN (HTTP $($resp.StatusCode))" -ForegroundColor Yellow
            Add-Result "Email-to-RSS Worker" "WARN" "HTTP $($resp.StatusCode)" "Cloudflare dashboard → Workers → Logs" "P1"
        }
    } catch {
        Write-Host " FAIL" -ForegroundColor Red
        Add-Result "Email-to-RSS Worker" "FAIL" "无响应" "Cloudflare dashboard → Workers → 检查部署状态" "P1"
    }
}

# ============================================================
# 7. rsshub.app 公共实例(预期 403,验证已挂)
# ============================================================
Write-Host "[7/7] rsshub.app 公共实例(预期已挂) ..." -NoNewline
try {
    $resp = Invoke-WebRequest -Uri "https://rsshub.app/bilibili/user/video/1567748478" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-Host " WARN (居然活了!)" -ForegroundColor Yellow
        Add-Result "rsshub.app 公共实例" "WARN" "意外 alive,2026-05-25 实测 403 但本次 200" "可能临时复活,长期不可靠,仍建议自建" "P1"
    } else {
        Write-Host " EXPECTED-FAIL (HTTP $($resp.StatusCode))" -ForegroundColor Gray
        Add-Result "rsshub.app 公共实例" "WARN" "HTTP $($resp.StatusCode),已挂(符合预期)" "8 个 RSSHub feed 全拉空,跟 docs/rsshub_hf_spaces_setup.md 自建" "P1"
    }
} catch {
    Write-Host " EXPECTED-FAIL" -ForegroundColor Gray
    Add-Result "rsshub.app 公共实例" "WARN" "已挂(符合预期)" "8 个 RSSHub feed 全拉空,跟 docs/rsshub_hf_spaces_setup.md 自建" "P1"
}

# ============================================================
# 总结
# ============================================================
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host " 总结" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
$results | Format-Table -Property Priority,Name,Status,Detail -AutoSize -Wrap

# 救场建议
$fails = $results | Where-Object { $_.Status -eq "FAIL" }
if ($fails.Count -gt 0) {
    Write-Host ""
    Write-Host "需要救场:" -ForegroundColor Red
    foreach ($f in $fails) {
        Write-Host "  [$($f.Priority)] $($f.Name): $($f.Fix)" -ForegroundColor Yellow
    }
}

Write-Host ""
if ($p0_fail) {
    Write-Host "[P0 FAIL] 不要跑 ship pipeline,先修上面 P0 项。" -ForegroundColor Red
    exit 1
} elseif ($any_fail -and $Strict) {
    Write-Host "[STRICT MODE] 有非-P0 FAIL,strict 模式下退出。" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "[OK] P0 全通过,可以跑 ship pipeline。" -ForegroundColor Green
    exit 0
}
