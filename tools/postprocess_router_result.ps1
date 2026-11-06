# SPDX-License-Identifier: MIT
<#
.SYNOPSIS
  Standard post-processing of a DeepPCB result onto a frozen KiCad baseline (private copies).
.DESCRIPTION
  merge router copper (open nets only) -> GND stitch -> DRC -> remove new conflicting copper
  -> remove new B.Cu copper inside contact guards -> gap route -> stitch -> gap route -> DRC
  -> standard check. Every stage writes its own folder under -Work.
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
function New-Stage($name) {
    $d = Join-Path $Work $name
    New-Item -ItemType Directory -Force $d | Out-Null
    Copy-Item "$Base\handbell.kicad_pro", "$Base\handbell.kicad_sch" $d
    return $d
}
function Invoke-Drc($d) {
    Remove-Item "$d\drc.*" -ErrorAction SilentlyContinue
    python "$tools\supervise_process.py" --receipt "$d\drc.receipt.json" --stdout "$d\drc.out" --stderr "$d\drc.err" --cwd $d --limit 400 -- $kicad pcb drc --format json --units mm --refill-zones --schematic-parity --severity-all --output "$d\drc.json" "$d\handbell.kicad_pcb" | Out-Null
    $r = Get-Content "$d\drc.json" -Raw | ConvertFrom-Json
    $err = ($r.violations | Where-Object severity -eq 'error' | Group-Object type | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ', '
    Write-Output ("{0}: opens {1}; errors: {2}" -f (Split-Path $d -Leaf), $r.unconnected_items.Count, $err)
}
function Invoke-Py { & $py @args 2>$null | Out-Null }
function Invoke-Gaps($src, $dst) {
    python "$tools\supervise_process.py" --receipt "$dst\route.receipt.json" --stdout "$dst\route.out" --stderr "$dst\route.err" --cwd $dst --limit 2400 -- $py "$tools\route_gaps.py" --board "$src\handbell.kicad_pcb" --drc "$src\drc.json" --out "$dst\handbell.kicad_pcb" --report "$dst\route.json" --layers @Layers --narrow-net VCORE VHI --margin 6 | Out-Null
}

$s1 = New-Stage '1-merge'
Invoke-Py "$tools\merge_router_nets.py" --base "$Base\handbell.kicad_pcb" --router $Router --base-drc "$Base\drc.json" --out "$s1\merged.kicad_pcb"
Invoke-Py "$tools\stitch_gnd_islands.py" --board "$s1\merged.kicad_pcb" --out "$s1\handbell.kicad_pcb" --report "$s1\stitch.json"
Remove-Item "$s1\merged.kicad_pcb"
Invoke-Drc $s1
$s2 = New-Stage '2-clean'
Invoke-Py "$tools\clean_drc_conflicts.py" --board "$s1\handbell.kicad_pcb" --drc "$s1\drc.json" --baseline-drc "$Base\drc.json" --base-board "$Base\handbell.kicad_pcb" --out "$s2\cleaned.kicad_pcb"
Invoke-Py "$tools\remove_guard_copper.py" --base "$Base\handbell.kicad_pcb" --board "$s2\cleaned.kicad_pcb" --out "$s2\handbell.kicad_pcb"
Remove-Item "$s2\cleaned.kicad_pcb"
Invoke-Drc $s2
$s3 = New-Stage '3-gaps'
Invoke-Gaps $s2 $s3
Invoke-Drc $s3
$s4 = New-Stage '4-stitch'
Invoke-Py "$tools\stitch_gnd_islands.py" --board "$s3\handbell.kicad_pcb" --out "$s4\handbell.kicad_pcb" --report "$s4\stitch.json"
Invoke-Drc $s4
$s5 = New-Stage '5-gaps'
Invoke-Gaps $s4 $s5
Invoke-Drc $s5
$checkArgs = @('--base', "$Base\handbell.kicad_pcb", '--candidate', "$s5\handbell.kicad_pcb", '--base-drc', "$Base\drc.json", '--candidate-drc', "$s5\drc.json", '--report', "$s5\check.json")
if ($AllowMove) { $checkArgs += @('--allow-move') + $AllowMove }
& $py "$tools\check_routing_result.py" @checkArgs 2>$null | Out-Null
$c = Get-Content "$s5\check.json" -Raw | ConvertFrom-Json
Write-Output ("CHECK {0} :: {1}" -f $c.status, ($c.failures -join '; '))
