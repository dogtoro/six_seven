#!/usr/bin/env bash
# Run from six_seven/benchmarks on Machine B. Repos are already in ../third_party (ds.py line 91 already patched).
set -e
mkdir -p preds results
pip install numpy pandas scikit-learn pillow tabulate matplotlib scipy
grep -n "im_ori.save(tmp1" ../third_party/ADCD-Net/ds.py || echo "WARN: ds.py line 91 not patched"
echo "Deps for ADCD-Net: Python 3.10, torch 2.3.0+cu121, albumentations==2.0.8, jpeg2dct lmdb six einops efficientnet_pytorch segmentation_models_pytorch paddlepaddle paddleocr"
echo "Single GPU: export CUDA_VISIBLE_DEVICES=0 (adcdnet_infer.py already runs on one GPU, no DDP)."
