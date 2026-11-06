# Full V2 benchmark; preserves V1 inputs and results.
param([string]$Python = 'c:\Src\.conda\python.exe', [ValidateRange(0,500)][int]$Limit = 0, [switch]$EvaluateOnly)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location (Join-Path $root 'benchmarks')
$env:CUDA_VISIBLE_DEVICES = '0'
$env:PYTHONIOENCODING = 'utf-8'
function Run([string[]]$ScriptArgs) {
    & $Python @ScriptArgs
    if ($LASTEXITCODE -ne 0) { throw "Python failed: $ScriptArgs" }
}
$data = '..\dataset_sample_v2'
$work = 'work_adcd_v2'
$pred = 'preds_v2'
$results = 'results_v2'
if ($Limit -gt 0) {
    $data = "..\dataset_sample_v2_pilot_$Limit"
    $work = "work_adcd_v2_pilot_$Limit"
    $pred = "preds_v2_pilot_$Limit"
    $results = "results_v2_pilot_$Limit"
    Run @('build_dataset_sample.py','--raw','..\dataset_v2','--out',$data,'--limit',"$Limit")
}
New-Item -ItemType Directory -Force $pred | Out-Null
if (-not $EvaluateOnly) {
Run @('adcdnet_infer.py','--stage','prep','--data',$data,'--work',$work)
Run @('adcdnet_infer.py','--stage','infer','--data',$data,'--work',$work,'--out',"$pred\adcdnet")
$img = (Resolve-Path "$data\images").Path
$out = Join-Path (Get-Location).Path "$pred\trufor"
New-Item -ItemType Directory -Force $out | Out-Null
Push-Location (Join-Path $root 'third_party\TruFor\test_docker\src')
try {
    & $Python trufor_test.py --gpu 0 --input $img --output $out
    if ($LASTEXITCODE -ne 0) { throw 'TruFor failed' }
} finally { Pop-Location }
}
$results += '_annotated'
$models = @('ext:trufor','ext:adcdnet','ela','random')
Run (@('eval_sota.py','--data',$data,'--pred-root',$pred,'--models') + $models + @('--out',"$results\official_mask"))
Run (@('eval_sota.py','--data',$data,'--pred-root',$pred,'--models') + $models + @('--out',"$results\diff_mask",'--mask-key','mask_diff'))
Write-Host "V2 results complete in benchmarks\$results"
