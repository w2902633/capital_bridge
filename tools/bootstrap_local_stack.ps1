$ErrorActionPreference = "Stop"
$base = "C:\Capital\SKDLLPythonTester"
$repo = Join-Path $base "actions-runner\_work\capital_bridge\capital_bridge"
$credFile = Join-Path $base "capital_bridge_credentials.json"
$stackSrc = Join-Path $repo "tools\start_local_stack.ps1"
$stackDst = Join-Path $base "start_local_stack.ps1"
$vbs = Join-Path $base "start_local_stack_hidden.vbs"

if (-not $env:CAPITAL_USER_ID -or -not $env:CAPITAL_PASSWORD) {
  throw "Capital credentials are not present in the current runner environment."
}

function Protect([string]$plain) {
  ConvertTo-SecureString $plain -AsPlainText -Force | ConvertFrom-SecureString
}

$c = @{
  user = Protect $env:CAPITAL_USER_ID
  password = Protect $env:CAPITAL_PASSWORD
  authority = Protect ($(if ($env:CAPITAL_AUTHORITY) {$env:CAPITAL_AUTHORITY} else {"0"}))
}
$c | ConvertTo-Json | Set-Content -Path $credFile -Encoding UTF8
Copy-Item $stackSrc $stackDst -Force

$vbsText = @'
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Capital\SKDLLPythonTester\start_local_stack.ps1""", 0, False
'@
Set-Content -Path $vbs -Value $vbsText -Encoding ASCII

$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
New-Item -Path $runKey -Force | Out-Null
New-ItemProperty -Path $runKey -Name "CapitalLocalStack" -Value ('wscript.exe "' + $vbs + '"') -PropertyType String -Force | Out-Null

Write-Host "CREDENTIAL_STORE=READY"
Write-Host "STARTUP_ENTRY=READY"
Write-Host "HIDDEN_LAUNCHER=READY"
