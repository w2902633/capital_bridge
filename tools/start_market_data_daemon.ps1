$ErrorActionPreference = "Stop"
$base = "C:\Capital\SKDLLPythonTester"
$repo = Join-Path $base "actions-runner\_work\capital_bridge\capital_bridge"
$script = Join-Path $repo "tools\market_data_daemon.py"
$pidFile = Join-Path $base "capital_market_data.pid"
$logFile = Join-Path $base "capital_market_data.log"

if (Test-Path $pidFile) {
  $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
  if ($oldPid) {
    $p = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($p) {
      try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:8877/health" -TimeoutSec 2
        if ($h.ok) {
          Write-Host "daemon already healthy"
          exit 0
        }
      } catch {}
      Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
    }
  }
}

$env:RUNNER_TRACKING_ID = ""
$proc = Start-Process -FilePath "python" -ArgumentList @($script) -WorkingDirectory $base -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError ($logFile + ".err") -PassThru
Set-Content -Path $pidFile -Value $proc.Id
Start-Sleep -Seconds 8
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8877/health" -TimeoutSec 5
if (-not $health.ok) { throw "daemon failed health check" }
Write-Host ("daemon healthy; symbols=" + ($health.symbols -join ","))