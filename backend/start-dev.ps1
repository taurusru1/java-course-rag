$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot ".env"

if (-not (Test-Path $envFile)) {
    throw "Missing environment file: $envFile"
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $name, $value = $line -split "=", 2
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
    }
}

Write-Host "Starting backend with MySQL at $env:MYSQL_HOST`:$env:MYSQL_PORT/$env:MYSQL_DATABASE"
& mvn spring-boot:run
