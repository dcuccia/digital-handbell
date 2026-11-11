# SPDX-License-Identifier: MIT
<#
.SYNOPSIS
  Standard post-processing of a DeepPCB result onto a frozen KiCad baseline (private copies).
.DESCRIPTION
  merge router copper (open nets only) -> GND stitch -> DRC -> remove new conflicting copper
  -> remove new B.Cu copper inside contact guards -> gap route -> stitch -> gap route -> DRC
  -> standard check. Every stage writes its own folder under a new -Work.
  Child failures stop the pipeline; receipts, stderr and intermediate boards are retained.
  The baseline DRC must also use --all-track-errors.
#>
param(
    [Parameter(Mandatory)] [string] $Base,        # folder with frozen handbell.kicad_pcb/.pro/.sch and drc.json
    [Parameter(Mandatory)] [string] $Router,      # router output .kicad_pcb
    [Parameter(Mandatory)] [string] $Work,        # output folder (created)
    [string[]] $AllowMove = @(),
    [string[]] $Layers = @('F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu')
)
$ErrorActionPreference = 'Stop'
$py = 'C:\Users\david.cuccia\AppData\Local\Programs\Python\Python311\python.exe'
$kicad = 'C:\Users\david.cuccia\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe'
$tools = $PSScriptRoot
$Base = (Resolve-Path -LiteralPath $Base).Path
$Router = (Resolve-Path -LiteralPath $Router).Path
$Work = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Work)
foreach ($file in @('handbell.kicad_pcb', 'handbell.kicad_pro', 'handbell.kicad_sch', 'drc.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Base $file) -PathType Leaf)) {
        throw "Missing baseline input: $file"
    }
}
if (Test-Path -LiteralPath $Work) {
    throw "Work path already exists; choose a new path to preserve prior evidence: $Work"
}
New-Item -ItemType Directory -Path $Work | Out-Null

function New-Stage($name) {
    $d = Join-Path $Work $name
    New-Item -ItemType Directory -Path $d | Out-Null
    Copy-Item "$Base\handbell.kicad_pro", "$Base\handbell.kicad_sch" $d
    return $d
}
function Invoke-Supervised {
    param(
        [string] $Directory,
        [string] $Name,
        [string] $Executable,
        [string[]] $Arguments,
        [double] $LimitSeconds = 120
    )
    $receipt = Join-Path $Directory "$Name.receipt.json"
    $stdout = Join-Path $Directory "$Name.out"
    $stderr = Join-Path $Directory "$Name.err"
    & $py "$tools\supervise_process.py" --receipt $receipt --stdout $stdout --stderr $stderr --cwd $Directory --limit $LimitSeconds -- $Executable @Arguments
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        if (Test-Path -LiteralPath $stderr) {
            Get-Content -LiteralPath $stderr -Tail 20 | Write-Warning
        }
        throw "$Name failed (exit $code). Evidence: $receipt"
    }
}
function Invoke-Drc($d) {
    Invoke-Supervised -Directory $d -Name 'drc' -Executable $kicad -Arguments @(
        'pcb', 'drc', '--format', 'json', '--units', 'mm', '--refill-zones',
        '--schematic-parity', '--severity-all', '--all-track-errors',
        '--output', "$d\drc.json", "$d\handbell.kicad_pcb"
    )
    $r = Get-Content "$d\drc.json" -Raw | ConvertFrom-Json
    $err = ($r.violations | Where-Object severity -eq 'error' | Group-Object type | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ', '
    Write-Output ("{0}: opens {1}; errors: {2}" -f (Split-Path $d -Leaf), $r.unconnected_items.Count, $err)
}
function Invoke-Gaps($src, $dst) {
    $routeArgs = @("$tools\route_gaps.py", '--board', "$src\handbell.kicad_pcb",
        '--drc', "$src\drc.json", '--out', "$dst\handbell.kicad_pcb",
        '--report', "$dst\route.json", '--layers') + $Layers +
        @('--net-width', 'VO+', '0.6', '--net-width', 'VO-', '0.6', '--margin', '6')
    Invoke-Supervised -Directory $dst -Name 'route' -Executable $py -Arguments $routeArgs -LimitSeconds 300
}

$s1 = New-Stage '1-merge'
Invoke-Supervised -Directory $s1 -Name 'merge' -Executable $py -Arguments @(
    "$tools\merge_router_nets.py", '--base', "$Base\handbell.kicad_pcb", '--router', $Router,
    '--base-drc', "$Base\drc.json", '--out', "$s1\merged.kicad_pcb"
)
Invoke-Supervised -Directory $s1 -Name 'stitch' -Executable $py -Arguments @(
    "$tools\stitch_gnd_islands.py", '--board', "$s1\merged.kicad_pcb",
    '--out', "$s1\handbell.kicad_pcb", '--report', "$s1\stitch.json"
)
Invoke-Drc $s1
$s2 = New-Stage '2-clean'
Invoke-Supervised -Directory $s2 -Name 'clean' -Executable $py -Arguments @(
    "$tools\clean_drc_conflicts.py", '--board', "$s1\handbell.kicad_pcb",
    '--drc', "$s1\drc.json", '--baseline-drc', "$Base\drc.json",
    '--base-board', "$Base\handbell.kicad_pcb", '--out', "$s2\cleaned.kicad_pcb"
)
Invoke-Supervised -Directory $s2 -Name 'guards' -Executable $py -Arguments @(
    "$tools\remove_guard_copper.py", '--base', "$Base\handbell.kicad_pcb",
    '--board', "$s2\cleaned.kicad_pcb", '--out', "$s2\handbell.kicad_pcb"
)
Invoke-Drc $s2
$s3 = New-Stage '3-gaps'
Invoke-Gaps $s2 $s3
Invoke-Drc $s3
$s4 = New-Stage '4-stitch'
Invoke-Supervised -Directory $s4 -Name 'stitch' -Executable $py -Arguments @(
    "$tools\stitch_gnd_islands.py", '--board', "$s3\handbell.kicad_pcb",
    '--out', "$s4\handbell.kicad_pcb", '--report', "$s4\stitch.json"
)
Invoke-Drc $s4
$s5 = New-Stage '5-gaps'
Invoke-Gaps $s4 $s5
Invoke-Drc $s5
$checkArgs = @('--base', "$Base\handbell.kicad_pcb", '--candidate', "$s5\handbell.kicad_pcb", '--base-drc', "$Base\drc.json", '--candidate-drc', "$s5\drc.json", '--report', "$s5\check.json")
if ($AllowMove) { $checkArgs += @('--allow-move') + $AllowMove }
Invoke-Supervised -Directory $s5 -Name 'check' -Executable $py -Arguments (@("$tools\check_routing_result.py") + $checkArgs)
$c = Get-Content "$s5\check.json" -Raw | ConvertFrom-Json
Write-Output ("CHECK {0} :: {1}" -f $c.status, ($c.failures -join '; '))
