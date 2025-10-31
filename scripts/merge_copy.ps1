# merge_copy.ps1
# Safely copy selected folders from free-react project into QUANTUM_FORGE target
$src = 'C:\Users\G_R_E\Downloads\free-react-tailwind-admin-dashboard-main'
$dst = 'C:\QUANTUM_FORGE\QUANTUM_FORGE'
$folders = @(
    @{Name='docs'; Target='docs'},
    @{Name='scripts'; Target='scripts'},
    @{Name='notebooks'; Target='notebooks'},
    @{Name='deploy'; Target='deploy'},
    @{Name='react-tailwind-frontend-main-template-files'; Target='frontend\templates'}
)

foreach($entry in $folders){
    $f = $entry.Name
    $tp = $entry.Target
    $sp = Join-Path $src $f
    $dp = Join-Path $dst $tp
    if(Test-Path $sp){
        New-Item -ItemType Directory -Path $dp -Force | Out-Null
        robocopy $sp $dp /E /COPY:DAT /XO /NFL /NDL /NJH /NJS | Out-Null
        Write-Host "Copied $f -> $dp"
    } else {
        Write-Host "Skipped $f (not found)"
    }
}

Write-Host "\nTarget top-level directories:"
Get-ChildItem -Path $dst -Directory | Select-Object Name,LastWriteTime | Format-Table -AutoSize
