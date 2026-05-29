# run_rsshub.ps1 — 重启 RSSHub 容器(从 .env.rsshub 加载 cookie)
#
# 用法:
#   .\tools\run_rsshub.ps1            # stop 旧容器 + 重新 run(用 .env.rsshub 注入 cookie)
#
# 关联:
#   .env.rsshub        — cookie 机密文件,gitignored
#   docs/rsshub_cookie_setup.md — cookie 抓取流程
#   WRITE_AGENT.md Preflight 红线第 5 项

[CmdletBinding()]
param()

$envFile = "D:\Dev\ai-wechat-pipeline\.env.rsshub"
$image = "diygod/rsshub:chromium-bundled"
$containerName = "rsshub"
$port = 1200

if (-not (Test-Path $envFile)) {
    Write-Host "[FAIL] 找不到 $envFile" -ForegroundColor Red
    Write-Host "       先按 docs/rsshub_cookie_setup.md 抓 cookie 写进去" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 重启 RSSHub 容器 (注入 cookie)" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. 停旧容器
Write-Host "[1/3] 停旧容器 ..." -NoNewline
docker stop $containerName 2>&1 | Out-Null
docker rm $containerName 2>&1 | Out-Null
Write-Host " OK" -ForegroundColor Green

# 2. 新建容器,注入 env
Write-Host "[2/3] 新建容器(--env-file 加载 cookie)..." -NoNewline
$dockerOut = docker run -d `
    --name $containerName `
    --restart unless-stopped `
    -p "${port}:${port}" `
    -e "TZ=Asia/Shanghai" `
    --env-file $envFile `
    $image 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host $dockerOut
    exit 1
}
Write-Host " OK (容器 ID: $($dockerOut.Substring(0,12)))" -ForegroundColor Green

# 3. 等容器就绪
Write-Host "[3/3] 等容器启动 ..." -NoNewline
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$port/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
}
if ($ready) {
    Write-Host " 就绪($($i+1)s)" -ForegroundColor Green
} else {
    Write-Host " 超时(30s 未就绪)" -ForegroundColor Yellow
    Write-Host "   docker logs $containerName --tail 30 查错误" -ForegroundColor Gray
}

Write-Host ""
docker ps --filter "name=$containerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""
Write-Host "下一步:跑 preflight 验证 cookie 注入成功" -ForegroundColor Cyan
Write-Host "  .\tools\preflight.ps1" -ForegroundColor Gray

