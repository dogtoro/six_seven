param([string]$Python = 'c:\Src\.conda\python.exe')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location (Join-Path $root 'benchmarks')
$env:CUDA_VISIBLE_DEVICES = '0'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
function Run([string[]]$ScriptArgs) {
    & $Python @ScriptArgs
    if ($LASTEXITCODE -ne 0) { throw "Python failed: $ScriptArgs" }
}
function Stage([string]$Name) {
    $Name | Set-Content -LiteralPath (Join-Path $root 'feedback_stage.txt')
    Write-Host $Name
}
trap { Stage "FAILED: $($_.Exception.Message)"; exit 1 }
Stage 'V3 only: audit and prepare 3000 compression variants'
Run @('validate_v3.py')
if (-not (Test-Path -LiteralPath '..\dataset_sample_v3\metadata.json')) {
    Run @('build_dataset_sample.py','--raw','..\dataset_v3_realistic','--out','..\dataset_sample_v3')
}
Stage 'V3 only: OCR preparation (3000 records)'
Run @('adcdnet_infer.py','--stage','prep','--data','..\dataset_sample_v3','--work','work_adcd_v3','--ocr-device','gpu:0','--paddle-runtime',(Join-Path $root '.ocr_gpu_runtime'),'--cpu-threads','1')
$models = @('ext:trufor','ext:adcdnet','ela','random')
foreach ($resolution in @(512,1024,2048)) {
    $name = if ($resolution -eq 512) { 'adcdnet' } else { "adcdnet_$resolution" }
    Stage "V3 only: ADCD-Net inference at $resolution (3000 images)"
    Run @('adcdnet_infer.py','--stage','infer','--data','..\dataset_sample_v3','--work','work_adcd_v3','--max-size',"$resolution",'--out',"preds_v3\$name")
    if ($resolution -ne 512) { $models += "ext:$name" }
}
$img = (Resolve-Path '..\dataset_sample_v3\images').Path
$out = Join-Path (Get-Location).Path 'preds_v3\trufor'
New-Item -ItemType Directory -Force $out | Out-Null
Push-Location (Join-Path $root 'third_party\TruFor\test_docker\src')
Stage 'V3 only: TruFor inference (3000 images)'
try {
    & $Python trufor_test.py --gpu 0 --input $img --output $out
    if ($LASTEXITCODE -ne 0) { throw 'V3 TruFor failed' }
} finally { Pop-Location }
foreach ($mask in @('mask','mask_diff')) {
    $folder = if ($mask -eq 'mask') { 'official_mask' } else { 'diff_mask' }
    Stage "V3 only: evaluate $folder"
    Run (@('eval_sota.py','--data','..\dataset_sample_v3','--pred-root','preds_v3','--models') + $models + @('--score','native','--vis','200','--vis-authentic','200','--mask-key',$mask,'--out',"results_v3_realistic\$folder"))
}
Run @('v3_resolution_report.py')
Run @('validate_v3_results.py')
Stage 'COMPLETE: V3 reports and 512/1024/2048 resolution comparison verified'
