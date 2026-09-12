$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw "Ollama is not installed or not on PATH." }
ollama pull qwen2.5:14b
python -m venv .venv-medical-mesh
& .\.venv-medical-mesh\Scripts\python.exe -m pip install --upgrade pip
& .\.venv-medical-mesh\Scripts\pip.exe install -r requirements-medical-agent-mesh.txt
& .\.venv-medical-mesh\Scripts\python.exe agent_mesh.py --check

$Action = New-ScheduledTaskAction -Execute "$Root\.venv-medical-mesh\Scripts\python.exe" -Argument "$Root\agent_mesh.py" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "AlreadyHere-MedicalAgentMesh" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Local medical logistics lead and compliance pipeline" -Force
Write-Host "Installed. Scheduled daily for 8:00 AM local Phoenix time."
