#!/usr/bin/env bash
# Run from six_seven/benchmarks on Machine B (GPU). Before: bash ../download_weights.sh
set -e
W=../third_party/weights
for f in ADCDNet.pth docres.pkl qt_table.pk; do [ -f $W/$f ] || { echo "missing $W/$f (run ../download_weights.sh)"; exit 1; }; done
bash setup_sota.sh
python build_dataset_sample.py --raw ../dataset_raw --out ../dataset_sample
python adcdnet_infer.py --stage prep  --data ../dataset_sample --work work_adcd
python adcdnet_infer.py --stage infer --data ../dataset_sample --work work_adcd
# MANUAL: TruFor -> copy ../dataset_sample/images to third_party/TruFor/test_docker/images, bash docker_build.sh && bash docker_run.sh, then cp output/* preds/trufor/
# MANUAL: TextShield-R1 -> see textshield_to_maps.py (images must be resized to multiples of 28 first)
MODELS="ext:adcdnet ela random"
[ -d preds/trufor ] && MODELS="ext:trufor $MODELS"
[ -d preds/textshield ] && MODELS="ext:textshield $MODELS"
python eval_sota.py --data ../dataset_sample --models $MODELS --out results/official_mask
python eval_sota.py --data ../dataset_sample --models $MODELS --out results/diff_mask --mask-key mask_diff
