param([Parameter(Mandatory=$true)][ValidateSet('1','2')][string]$Snapshot)
$ErrorActionPreference='Stop'
$ptpWorkspace='C:\Users\User\Documents\Codex\2026-10-28\task-2'
$ptpUserProfile=[Environment]::GetFolderPath('UserProfile')
$ptpKey=Join-Path $ptpUserProfile '.ssh\id_ed25519_dr_train'
$ptpOptions=@('-i',$ptpKey,'-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','BatchMode=yes','-o','ForwardAgent=no','-o','ConnectTimeout=15','-o','ConnectionAttempts=1','-o','LogLevel=ERROR')
$ptpProbe=Join-Path $ptpWorkspace 'dr_train_resource_probe.py'
$ptpStart=[DateTime]::UtcNow.ToString('o')
$ptpOutput=Get-Content -LiteralPath $ptpProbe -Raw | & ssh @ptpOptions 'chaw@100.77.149.83' 'python3 -B -'
$ptpExitCode=$LASTEXITCODE
if($ptpExitCode -ne 0){throw "Strict read-only SSH preflight exited $ptpExitCode; no retry or alternate route attempted"}
$ptpParsed=$ptpOutput | ConvertFrom-Json
if($ptpParsed.host -ne 'dr-train'){throw 'Unexpected remote hostname; stop without additional action'}
$ptpRecord=[ordered]@{local_start_utc=$ptpStart;local_finish_utc=[DateTime]::UtcNow.ToString('o');snapshot=[int]$Snapshot;destination='chaw@100.77.149.83';ssh_exit_code=$ptpExitCode;strict_host_key_checking='yes';batch_mode=$true;probe_sha256=(Get-FileHash -LiteralPath $ptpProbe -Algorithm SHA256).Hash.ToLower();remote=$ptpParsed}
$ptpDestination=Join-Path $ptpWorkspace ('dr-train-resource-snapshot-'+$Snapshot+'.json')
if(Test-Path -LiteralPath $ptpDestination){throw 'Snapshot file already exists; inspect outcome before repeating operation'}
[IO.File]::WriteAllText($ptpDestination,($ptpRecord|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
Write-Output ('Snapshot '+$Snapshot+' saved locally at '+$ptpDestination)
Write-Output ('Remote timestamp '+$ptpParsed.timestamp_utc)
$ptpParsed.gpu.gpus | Format-Table
