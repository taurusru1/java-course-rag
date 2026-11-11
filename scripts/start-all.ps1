# 一键启动：MySQL 容器 + Python 检索服务 + Spring Boot 后端 + Vue 前端
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1 -NoBuild   # 跳过编译
#   powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1 -Stop      # 停止全部
param(
    [switch]$NoBuild,
    [switch]$Stop
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Root '.runtime'
$BackendPort = 18082
$AiPort = 9000
$FrontendPort = 5173

New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "    $text" -ForegroundColor Green }
function Write-Warn($text) { Write-Host "    $text" -ForegroundColor Yellow }

function Test-Port($port) {
    $conn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    return [bool]$conn
}

function Start-Detached($name, $workDir, $commandLine, $logFile) {
    $full = "cmd /c cd /d `"$workDir`" && $commandLine > `"$logFile`" 2>&1"
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $full } | Out-Null
    Write-Ok "已启动 $name（日志：$logFile）"
}

function Wait-Port($port, $name, $seconds = 60) {
    for ($i = 0; $i -lt $seconds; $i++) {
        if (Test-Port $port) { Write-Ok "$name 已就绪（端口 $port）"; return $true }
        Start-Sleep -Seconds 1
    }
    Write-Warn "$name 在 $seconds 秒内未监听端口 $port，请查看日志"
    return $false
}

if ($Stop) {
    Write-Step '停止服务'
    Get-CimInstance Win32_Process -Filter "Name='java.exe'" |
        Where-Object { $_.CommandLine -like '*javacourse-backend*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Ok "已停止后端 PID $($_.ProcessId)" }
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like '*offline_service*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Ok "已停止 AI 服务 PID $($_.ProcessId)" }
    Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
        Where-Object { $_.CommandLine -like '*vite*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Ok "已停止前端 PID $($_.ProcessId)" }
    Write-Ok 'MySQL 容器保持运行（如需停止：docker stop javacourse-mysql）'
    exit 0
}

Write-Step '1/4 检查 MySQL'
$mysql = docker ps --filter 'name=javacourse-mysql' --format '{{.Status}}'
if (-not $mysql) {
    Write-Warn 'MySQL 容器未运行，正在启动…'
    Push-Location $Root
    docker compose -f docker-compose.dev.yml up -d | Out-Null
    Pop-Location
    Start-Sleep -Seconds 6
}
Write-Ok "MySQL：$(docker ps --filter 'name=javacourse-mysql' --format '{{.Status}}')"

Write-Step '2/4 启动 Python 检索服务（离线模式）'
if (Test-Port $AiPort) {
    Write-Ok "端口 $AiPort 已在监听，跳过"
} else {
    $py = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { throw '缺少 .venv，请先执行：uv venv .venv --python 3.11; uv pip install -r requirements.txt' }
    Start-Detached 'AI 服务' $Root "`"$py`" -m uvicorn web.offline_service:app --host 127.0.0.1 --port $AiPort" (Join-Path $Runtime 'ai.log')
    Wait-Port $AiPort 'AI 服务' 60 | Out-Null
}

Write-Step '3/4 启动 Spring Boot 后端'
if (Test-Port $BackendPort) {
    Write-Ok "端口 $BackendPort 已在监听，跳过"
} else {
    $jar = Get-ChildItem (Join-Path $Root 'backend\target') -Filter 'javacourse-backend-*.jar' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '*.original' } | Select-Object -First 1
    if (-not $jar -or -not $NoBuild) {
        Write-Warn '正在编译后端…'
        & 'D:\Develop\apache-maven-3.9.4\bin\mvn.cmd' -q -DskipTests -f (Join-Path $Root 'backend\pom.xml') package
        $jar = Get-ChildItem (Join-Path $Root 'backend\target') -Filter 'javacourse-backend-*.jar' |
            Where-Object { $_.Name -notlike '*.original' } | Select-Object -First 1
    }
    $java = 'D:\Develop\JDK\jdk-17\bin\java.exe'
    Start-Detached '后端' $Root "`"$java`" -jar `"$($jar.FullName)`" --server.port=$BackendPort" (Join-Path $Runtime 'backend.log')
    Wait-Port $BackendPort '后端' 90 | Out-Null
}

Write-Step '4/4 启动 Vue 前端'
if (Test-Port $FrontendPort) {
    Write-Ok "端口 $FrontendPort 已在监听，跳过"
} else {
    $fe = Join-Path $Root 'frontend'
    if (-not (Test-Path (Join-Path $fe 'node_modules'))) {
        Write-Warn '正在安装前端依赖…'
        Push-Location $fe
        npm install --silent
        Pop-Location
    }
    Start-Detached '前端' $fe "set VITE_API_TARGET=http://127.0.0.1:$BackendPort&& npm run dev -- --port $FrontendPort" (Join-Path $Runtime 'frontend.log')
    Wait-Port $FrontendPort '前端' 60 | Out-Null
}

Write-Host ''
Write-Host '服务地址' -ForegroundColor Cyan
Write-Host "  前端      http://127.0.0.1:$FrontendPort"
Write-Host "  后端      http://127.0.0.1:$BackendPort/api"
Write-Host "  AI 服务   http://127.0.0.1:$AiPort/health"
Write-Host '演示账号' -ForegroundColor Cyan
Write-Host '  学生  student / 123456'
Write-Host '  教师  teacher / 123456'
Write-Host ''
Write-Host "停止服务：powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1 -Stop" -ForegroundColor DarkGray
