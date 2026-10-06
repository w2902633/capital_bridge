$ErrorActionPreference = "SilentlyContinue"
$base = "C:\Capital\SKDLLPythonTester"
$runner = Join-Path $base "actions-runner"
$repo = Join-Path $runner "_work\capital_bridge\capital_bridge"
$daemonScript = Join-Path $repo "tools\start_market_data_daemon.ps1"
$credFile = Join-Path $base "capital_bridge_credentials.json"

function Unprotect([string]$cipher) {
  $sec = ConvertTo-SecureString $cipher
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

if ((-not $env:CAPITAL_USER_ID -or -not $env:CAPITAL_PASSWORD) -and (Test-Path $credFile)) {
  try {
    $c = Get-Content $credFile -Raw | ConvertFrom-Json
    $env:CAPITAL_USER_ID = Unprotect $c.user
    $env:CAPITAL_PASSWORD = Unprotect $c.password
    $env:CAPITAL_AUTHORITY = Unprotect $c.authority
  } catch {}
}

$listener = Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue
if (-not $listener) {
  $runCmd = Join-Path $runner "run.cmd"
  if (Test-Path $runCmd) {
    Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", ('"' + $runCmd + '"')) -WorkingDirectory $runner -WindowStyle Hidden
  }
}

Start-Sleep -Seconds 8
try {
  Invoke-RestMethod -Uri "http://127.0.0.1:8877/health" -TimeoutSec 2 | Out-Null
} catch {
  if (Test-Path $daemonScript) {
    powershell -ExecutionPolicy Bypass -File $daemonScript | Out-Null
  }
}
