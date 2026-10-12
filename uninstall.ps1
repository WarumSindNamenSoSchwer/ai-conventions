# Remove what setup.ps1 wrote into this project (Windows).
# The machine-wide Jcode dispatcher is removed only when no other project uses it.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach ($cand in @(@('py', '-3'), @('python'), @('python3'))) {
    $exe = $cand[0]
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $pre = @($cand | Select-Object -Skip 1)
    & $exe @pre -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { continue }
    & $exe @pre (Join-Path $here 'bin\mcs') uninstall @args
    exit $LASTEXITCODE
}
Write-Error "uninstall: Python 3.10 or newer is required."
exit 1
