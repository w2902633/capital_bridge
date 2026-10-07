$ErrorActionPreference = "Stop"
$sw=[System.Diagnostics.Stopwatch]::StartNew()
$h=Invoke-RestMethod -Uri "http://127.0.0.1:8877/health" -TimeoutSec 3
$q=Invoke-RestMethod -Uri "http://127.0.0.1:8877/quotes?symbols=PBF00,QEF00,DQF00,VBF00,CCF00,TM0000,2344,3036,6024,709092" -TimeoutSec 3
$b=Invoke-RestMethod -Uri "http://127.0.0.1:8877/bars/PBF00?tf=1m&limit=3" -TimeoutSec 3
$sw.Stop()
Write-Host ("LOCAL_QUERY_MS=" + $sw.ElapsedMilliseconds)
Write-Host ("HEALTH_OK=" + $h.ok)
$q | ConvertTo-Json -Depth 6 -Compress
$b | ConvertTo-Json -Depth 6 -Compress
# day-session live validation
