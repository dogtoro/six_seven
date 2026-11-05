# Native Windows pipeline.  Usage:  .\run_all.ps1 -Limit 20      (quick test: 20 receipts = 200 images)
#                                   .\run_all.ps1               (all 500 receipts = 5000 images)
param([int]$Limit = 0, [switch]$SkipTruFor, [string]$Python = "")
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot; Set-Location "$root\benchmarks"
# Python: -Python <path>, else the project .venv if it exists, else whatever "python" is active (your own conda/venv)
if ($Python) { $py = $Python } elseif (Test-Path "$root\.venv\Scripts\python.exe") { $py = "$root\.venv\Scripts\python.exe" } else { $py = (Get-Command python).Source }
Write-Host "Using Python: $py"; $env:CUDA_VISIBLE_DEVICES = "0"; $env:PYTHONIOENCODING = "utf-8"
$lim = @(); if ($Limit -gt 0) { $lim = @("--limit", $Limit) }
function Run($a) { & $py @a; if ($LASTEXITCODE -ne 0) { throw "failed: python $a" } }

Remove-Item ..\dataset_sample -Recurse -Force -ErrorAction SilentlyContinue
Run (@("build_dataset_sample.py","--raw","..\dataset_raw","--out","..\dataset_sample") + $lim)

# ---- ADCD-Net ----
Run (@("adcdnet_infer.py","--stage","prep","--data","..\dataset_sample","--work","work_adcd") + $lim)
Run @("adcdnet_infer.py","--stage","infer","--data","..\dataset_sample","--work","work_adcd")

# ---- TruFor (native, no Docker) ----
if (-not $SkipTruFor) {
    $img = (Resolve-Path "..\dataset_sample\images").Path
    Remove-Item "preds\trufor" -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force "preds\trufor" | Out-Null; $out = (Resolve-Path "preds\trufor").Path
    Push-Location "$root\third_party\TruFor\test_docker\src"
    & $py trufor_test.py --gpu 0 --input $img --output $out
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "TruFor failed" }
    Pop-Location
}
# ---- evaluation (TextShield-R1 skipped: needs ~16 GB VRAM, not an 8 GB 4060) ----
$models = @("ext:adcdnet","ela","random"); if (-not $SkipTruFor) { $models = @("ext:trufor") + $models }
Run (@("eval_sota.py","--data","..\dataset_sample","--models") + $models + @("--out","results\official_mask"))
Run (@("eval_sota.py","--data","..\dataset_sample","--models") + $models + @("--out","results\diff_mask","--mask-key","mask_diff"))
Write-Host "DONE. Results: $root\benchmarks\results\official_mask\summary.md  and  diff_mask\summary.md"
