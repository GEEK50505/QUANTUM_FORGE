# merge_preview.ps1
# Scans two directories for common top-level files and large files. Writes output to stdout and a temp file.
$roots = @('C:\QUANTUM_FORGE\QUANTUM_FORGE','C:\Users\G_R_E\Downloads\free-react-tailwind-admin-dashboard-main')
$names = @('README.md','LICENSE.md','CHANGELOG.md','package.json','vite.config.ts','postcss.config.js','tsconfig.json')
$out = "$env:TEMP\merge_preview_$(Get-Date -Format yyyyMMdd_HHmmss).txt"
Add-Content -Path $out -Value "Merge preview run at $(Get-Date)"
Add-Content -Path $out -Value "Scanning roots: $($roots -join ', ')"

foreach($n in $names){
    Add-Content -Path $out -Value "`n--- $n ---"
    $found = Get-ChildItem -Path $roots -Filter $n -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
    if($found){
        foreach($f in $found){
            Add-Content -Path $out -Value $f.FullName
        }
    } else {
        Add-Content -Path $out -Value "(not found)"
    }
}

Add-Content -Path $out -Value "`nLarge files (>=5MB) in roots:"
$large = Get-ChildItem -Path $roots -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -ge 5MB } | Select-Object FullName,@{Name='MB';Expression={[math]::Round($_.Length/1MB,2)}},LastWriteTime
if($large){
    foreach($l in $large){ Add-Content -Path $out -Value ("$($l.FullName) - $($l.MB) MB - $($l.LastWriteTime)") }
} else {
    Add-Content -Path $out -Value "(none)"
}

Write-Host "Merge preview written to: $out"
Write-Host "--- Begin preview ---"
Get-Content -Path $out | Write-Host
Write-Host "--- End preview ---"
