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
