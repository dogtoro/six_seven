# Native Windows setup (PowerShell, run from the six_seven folder).  Needs: Python 3.10 (py -3.10), NVIDIA driver (RTX 4060 OK), internet.
$ErrorActionPreference = "Stop"
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Install Python 3.10 from python.org (tick 'py launcher')" }
py -3.10 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cu121
& $py -m pip install "numpy==1.26.4" albumentations==2.0.8 lmdb six einops efficientnet_pytorch segmentation_models_pytorch `
    opencv-python pandas scikit-learn scipy pillow tabulate matplotlib tqdm tensorboard gdown timm==0.9.16 yacs
# NOTE: no jpeg2dct needed - a pure-Python replacement ships in third_party\ADCD-Net\jpeg2dct
& $py -m pip install paddlepaddle paddleocr
& $py -m pip install "numpy==1.26.4"      # paddle may upgrade numpy; torch 2.3 needs <2
& $py -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"

# ---- weights ----
$W = "third_party\weights"
if (-not (Test-Path "$W\ADCDNet.pth")) {
    & .\.venv\Scripts\gdown.exe 1-5BU3Bavs6SGJpaByua_FhDuUJGoo-iS -O "$W\adcdnet_data.zip"
    Expand-Archive "$W\adcdnet_data.zip" -DestinationPath "$W\_x" -Force
    Get-ChildItem "$W\_x" -Recurse -Include ADCDNet.pth, docres.pkl | Move-Item -Destination $W -Force
    Remove-Item "$W\_x" -Recurse -Force
}
$TF = "third_party\TruFor\test_docker"
if (-not (Test-Path "$TF\weights\trufor.pth.tar")) {
    Invoke-WebRequest https://www.grip.unina.it/download/prog/TruFor/TruFor_weights.zip -OutFile "$TF\TruFor_weights.zip"
    Expand-Archive "$TF\TruFor_weights.zip" -DestinationPath $TF -Force; Remove-Item "$TF\TruFor_weights.zip"
}
foreach ($f in "ADCDNet.pth","docres.pkl","qt_table.pk") { if (-not (Test-Path "$W\$f")) { Write-Warning "MISSING $W\$f (download it in a browser: see README_WINDOWS.md)" } }
if (-not (Test-Path "$TF\weights\trufor.pth.tar")) { Write-Warning "MISSING $TF\weights\trufor.pth.tar" }
Write-Host "Setup finished."
