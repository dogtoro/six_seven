#!/usr/bin/env bash
# Run on Machine B (needs internet access to Google Drive / grip-unina.it). Repos + qt_table.pk are already in third_party/.
set -e
cd "$(dirname "$0")/third_party/weights"
pip install gdown
# ADCD-Net: ADCDNet.pth + docres.pkl (+ DocTamperOCR/) in one archive
gdown 1-5BU3Bavs6SGJpaByua_FhDuUJGoo-iS -O adcdnet_data.zip || { echo "gdown failed -> open https://drive.google.com/file/d/1-5BU3Bavs6SGJpaByua_FhDuUJGoo-iS/view in a browser and save it here"; exit 1; }
unzip -q -n adcdnet_data.zip
ls -la ADCDNet.pth docres.pkl qt_table.pk   # if unzipped into a subfolder, move the 3 files here
# TruFor weights are downloaded automatically by its Docker build:  cd ../TruFor/test_docker && bash docker_build.sh
#   (or manually: wget https://www.grip.unina.it/download/prog/TruFor/TruFor_weights.zip)
# TextShield-R1 weights: Baidu Cloud https://pan.baidu.com/s/1sAJ0SkJbCW0MKW-K30tEAg  (extraction code: text)  -> browser only
