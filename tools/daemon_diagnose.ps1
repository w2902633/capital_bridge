$base="C:\Capital\SKDLLPythonTester"
$files=@("capital_market_data.log","capital_market_data.log.err")
foreach($f in $files){
  $p=Join-Path $base $f
  Write-Host ("FILE="+$p)
  if(Test-Path $p){
    Get-Content $p -Tail 120
  } else {
    Write-Host "MISSING"
  }
}

Write-Host "SPOT_TICK_SUBSCRIPTIONS"
$lp=Join-Path $base "capital_market_data.log"
if(Test-Path $lp){ Select-String -Path $lp -Pattern "spot_tick_subscribe" | Select-Object -Last 20 | ForEach-Object { Write-Host $_.Line } }
