$ErrorActionPreference="Stop"
$s=Invoke-RestMethod -Uri "http://127.0.0.1:8877/symbols" -TimeoutSec 4
$all=@($s.primary_tick_symbols)+@($s.watch_symbols)
$symbols=($all | Select-Object -Unique) -join ","
$q=Invoke-RestMethod -Uri ("http://127.0.0.1:8877/quotes?symbols="+$symbols) -TimeoutSec 5
Write-Host ("SYMBOLS="+$symbols)
Write-Host ("SNAPSHOT="+($q | ConvertTo-Json -Depth 8 -Compress))
foreach($sym in $s.primary_tick_symbols){
  foreach($tf in @("1m","5m","15m","1h")){
    try {
      $b=Invoke-RestMethod -Uri ("http://127.0.0.1:8877/bars/"+$sym+"?tf="+$tf+"&limit=120") -TimeoutSec 3
      Write-Host ("BARS_"+$sym+"_"+$tf+"="+($b | ConvertTo-Json -Depth 8 -Compress))
    } catch {}
  }
}