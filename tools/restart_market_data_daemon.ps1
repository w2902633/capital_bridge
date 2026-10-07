$ErrorActionPreference = "Stop"
$base="C:\Capital\SKDLLPythonTester"
$pidFile=Join-Path $base "capital_market_data.pid"
if(Test-Path $pidFile){
  $pids=Get-Content $pidFile -ErrorAction SilentlyContinue
  foreach($p in $pids){
    if($p){ Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }
  }
}
Start-Sleep -Seconds 1
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start_market_data_daemon.ps1")
Start-Sleep -Seconds 8
$h=Invoke-RestMethod -Uri "http://127.0.0.1:8877/health" -TimeoutSec 4
$s=Invoke-RestMethod -Uri "http://127.0.0.1:8877/symbols" -TimeoutSec 4
Write-Host ("HEALTH_OK="+$h.ok)
Write-Host ("SYMBOL_COUNT="+$s.watch_symbols.Count)
Write-Host ("PRIMARY_COUNT="+$s.primary_tick_symbols.Count)
Write-Host ("WATCH="+($s.watch_symbols -join ","))

# retry after SKCOM reconnect hardening

# load Best5 depth and flow metrics

# morning session reconnect 2026-10-07

# reload latest paired spot streaming
