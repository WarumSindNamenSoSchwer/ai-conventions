# Connect this project to the MCS conventions (Windows).
# Run from the project root:  powershell -ExecutionPolicy Bypass -File .mcs\setup.ps1
# Checks prerequisites, then hands over to `mcs setup` (Python).
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Find-Python {
    # "python3"/"python" may be the Windows Store stub; probe the version.
    foreach ($cand in @(@('py', '-3'), @('python'), @('python3'))) {
        $exe = $cand[0]
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        $pre = @($cand | Select-Object -Skip 1)
        & $exe @pre -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return , $cand }
    }
    return $null
}

$py = Find-Python
if ($null -eq $py) {
    Write-Error "setup: Python 3.10 or newer is required (winget install Python.Python.3.12)."
    exit 1
}

$missing = @()
foreach ($tool in @('git', 'node', 'clang-format')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { $missing += $tool }
}
if (-not (Get-Command bash -ErrorAction SilentlyContinue)) {
    Write-Warning "setup: 'bash' not on PATH. Claude Code hooks need Git Bash (part of Git for Windows)."
}
if ($missing.Count -gt 0) {
    Write-Error ("setup: missing on PATH: " + ($missing -join ', ') +
        ". Install with: winget install Git.Git OpenJS.NodeJS.LTS LLVM.LLVM")
    exit 1
}

$exe = $py[0]
$pre = @($py | Select-Object -Skip 1)
& $exe @pre (Join-Path $here 'bin\mcs') setup @args
exit $LASTEXITCODE
