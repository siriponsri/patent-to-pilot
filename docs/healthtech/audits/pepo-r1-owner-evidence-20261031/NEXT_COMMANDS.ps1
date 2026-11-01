# Run only from Luna's existing owner CLI context. No elevation or access bypass.
# The Pepo executor's original Git recheck was rejected for dubious ownership;
# its project-filtered Get-CimInstance query was rejected with Access denied.
# If either operation is denied here, stop that action; do not change ACL,
# safe.directory, execution policy, credentials, or use a different access route.
param(
    [string]$Repo = 'C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-o3-safety-repair-20261031',
    [string]$Patch = 'C:/Users/User/Documents/Codex/2026-10-31/task-5/r1-owner-evidence-recovery.patch'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $Repo
$initialHead = & git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Git access failed; stop without changing ownership/security settings.' }
$initialStatus = & git status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'Git status failed; stop.' }
if ($initialStatus) { throw 'Preserve dirty files. Choose an isolated checkout from the current candidate before proceeding.' }
& git apply --check $Patch
if ($LASTEXITCODE -ne 0) { throw 'Patch does not apply. Inspect current source; use the followup patch only when the prior delivery is already integrated.' }
$repairBranch = 'codex/r1-owner-evidence-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
& git switch -c $repairBranch
if ($LASTEXITCODE -ne 0) { throw 'Branch creation failed; stop.' }
& git apply $Patch
if ($LASTEXITCODE -ne 0) { throw 'Patch application failed; preserve work and inspect.' }
& git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Diff validation failed.' }
$testDirectory = Join-Path ([IO.Path]::GetTempPath()) ('ptp-r1-owner-verify-' + [Guid]::NewGuid().ToString('N'))
& python -B -m pytest -q -p no:cacheprovider --basetemp $testDirectory
if ($LASTEXITCODE -ne 0) { throw 'Candidate tests failed; do not activate paid dispatch.' }

# Metadata only. Never print CommandLine because it could contain private values.
$filter = "(Name='python.exe' OR Name='pythonw.exe' OR Name='node.exe' OR Name='ssh.exe') AND (CommandLine LIKE '%patent-to-pilot%' OR CommandLine LIKE '%dispatch_provider_pilot.py%' OR CommandLine LIKE '%run_openrouter_generation_evidence_pack.py%')"
try { $projectProcesses = @(Get-CimInstance Win32_Process -Filter $filter -ErrorAction Stop) }
catch { throw 'Project process query failed/denied. Do not interpret this as an empty list or bypass the denial.' }
$processReceipt = @($projectProcesses | Select-Object ProcessId,ParentProcessId,Name,CreationDate,@{Name='PotentialPaidEntryPoint';Expression={$_.CommandLine -match 'dispatch_provider_pilot|run_openrouter_generation_evidence_pack|b4_live'}})
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$receiptDirectory = Join-Path $env:LOCALAPPDATA ('PatentToPilot/recovery-observations/' + $stamp)
New-Item -ItemType Directory -Path $receiptDirectory -ErrorAction Stop | Out-Null
$processReceipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $receiptDirectory 'project-processes.json') -Encoding utf8
if (@($processReceipt | Where-Object PotentialPaidEntryPoint).Count -gt 0) {
    throw 'Potential provider dispatcher exists. Inspect ownership/state; do not kill it or start an overlapping run.'
}
# An empty filtered list is only one observation, not proof of global no-pending.
# Inspect relevant existing CLI/service queue roots and remote owned jobs, then
# record quiescence and any unresolved reservations before reviewed migration.

# The owner has explicitly authorized this bounded metadata-only key use.
& python -B scripts/healthtech/collect_openrouter_metadata.py --key-file C:/Users/User/Desktop/myProject/patent-to-pilot/.env --output (Join-Path $receiptDirectory 'key-observation.json')
if ($LASTEXITCODE -ne 0) { throw 'Metadata observation failed; no paid activation.' }
$observed = Get-Content -Raw -LiteralPath (Join-Path $receiptDirectory 'key-observation.json') | ConvertFrom-Json
if ($observed.key_endpoint.status -ne 'OBSERVED') { throw 'No successful metadata observation; no paid activation.' }
[pscustomobject]@{
    InitialHead = $initialHead
    Branch = $repairBranch
    KeyUsageUsd = $observed.key_metadata.usage
    ObservationUtc = $observed.completed_at_utc
    PrivateReceipts = $receiptDirectory
    PaidDispatchActivated = $false
    Next = 'Finish writer-state checks; use the accepted parent visual credit receipt. Implement/test conservative carryover migration, then fresh pricing/credit and the prepared canary. No paid command is run by this script.'
} | ConvertTo-Json
