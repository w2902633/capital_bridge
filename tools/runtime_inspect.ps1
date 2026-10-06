$ErrorActionPreference = "Stop"
$runner = "C:\Capital\SKDLLPythonTester\actions-runner"
$svcCmd = Join-Path $runner "svc.cmd"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host ("IS_ADMIN=" + $isAdmin)
Write-Host ("SVC_CMD_EXISTS=" + (Test-Path $svcCmd))

$svcs = Get-Service | Where-Object { $_.Name -like "actions.runner.*" -or $_.DisplayName -like "*Actions Runner*" }
if ($svcs) {
  foreach ($s in $svcs) {
    Write-Host ("RUNNER_SERVICE=" + $s.Name + "|" + $s.Status + "|" + $s.StartType)
  }
} else {
  Write-Host "RUNNER_SERVICE=NONE"
}

$task = Get-ScheduledTask -TaskName "CapitalGitHubRunner" -ErrorAction SilentlyContinue
if ($task) {
  Write-Host ("RUNNER_TASK=" + $task.State)
} else {
  Write-Host "RUNNER_TASK=NONE"
}

$daemon = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*market_data_daemon.py*" }
if ($daemon) {
  foreach ($p in $daemon) { Write-Host ("DAEMON_PID=" + $p.ProcessId) }
} else {
  Write-Host "DAEMON_PID=NONE"
}

try {
  $h=Invoke-RestMethod -Uri "http://127.0.0.1:8877/health" -TimeoutSec 3
  Write-Host ("DAEMON_HEALTH=" + $h.ok)
} catch {
  Write-Host ("DAEMON_HEALTH=FALSE")
}
