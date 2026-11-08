# Current benchmark: V3 only

From the project root, run run_v3.ps1. It uses --score native --vis 200 --vis-authentic 200 and writes results_v3_realistic/{official_mask,diff_mask}. Missing detection scores fall back to max(map) with score_source=map_max. ELA/random detection is N/A. See V3_STATUS.md for progress and cancelled V2 work. The older commands below are historical references and point to datasets intentionally removed locally.

# benchmarks/ — Dâm Nguyễn (Machine B)

Verified against the real repos on 2026-11-04 (code read, NOT run on a GPU — expect small fixes).

## Historical run order (V1/V2; current V3 command is below)
```
python build_dataset_sample.py --raw <unzipped Zang dataset> --out ../dataset_sample   # metadata.json + png/jpeg95/85/75/social_sim variants (Zang's zip has none)
bash setup_sota.sh                                   # clone ADCD-Net, patch ds.py line 91 (save_ckpt -> save: confirmed real bug)
python make_mock_dataset.py && python eval_sota.py --data ../dataset_sample_mock --models ela random   # smoke test (works)

# --- ADCD-Net (github.com/KahimWong/ADCD-Net) ---
python adcdnet_infer.py --stage prep  --data ../dataset_sample --work work_adcd     # PaddleOCR text masks + blank masks for authentic
python adcdnet_infer.py --stage infer --data ../dataset_sample --work work_adcd --repo third_party/ADCD-Net \
       --ckpt /abs/ADCDNet.pth --docres /abs/docres.pkl --qt /abs/qt_table.pk --out preds/adcdnet

# --- TruFor (github.com/grip-unina/TruFor, test_docker/: docker_build.sh downloads weights, docker_run.sh runs images/) ---
#   copy dataset images into TruFor's images/ dir, run, copy the output .npz files to preds/trufor/ (named <id>.npz, key 'map')

# --- TextShield-R1 (github.com/qcf-568/TextShield, Qwen2.5-VL, ms-swift==3.5.0, transformers==4.56.0) ---
#   see header of textshield_to_maps.py

python eval_sota.py --data ../dataset_sample --models ext:adcdnet ext:trufor ext:textshield ela random --out results
```

## Things I found in ADCD-Net's code that matter for Mỹ's analysis (cite file/line in the report)
1. **No inference script**: `main.py` only prints F1 (DDP, 4 GPUs by default); `adcdnet_infer.py` reimplements single-GPU inference.
2. **Needs OCR text masks** (PaddleOCR PP-OCRv5 detection) as an extra model input; text-detection quality on invoices affects results.
3. **Downscales to 512 px longest side** (`cfg.val_max_size`, `GeneralValDs`). Phone-screenshot invoices (~1080x2400) lose 4-5x resolution, which destroys small-font edits and DCT traces. Try `--max-size 1024/2048` as an ablation.
4. **Grayscale**: `multi_jpeg()` in ds.py does `img.convert("L")` then re-saves as JPEG QF100, so the "RGB" input is effectively grayscale. This supports the "colour-blind" hypothesis in the kick-off doc.
5. Trained on DocTamper (scanned/photographed docs). Zero-shot on digital invoices is a domain shift.
6. Needs `jpeg2dct` (painful to build), `qt_table.pk` from github.com/qcf-568/DocTamper, and the Google Drive archive from the ADCD-Net README (ADCDNet.pth, docres.pkl).

## Model caveats
- **TruFor**: outputs a probability map + `score` (use its own score if you prefer; the V3 runner uses its native detection-head score). License: non-commercial research only.
- **TextShield-R1**: an MLLM, outputs text + boxes, not a heatmap. We rasterize boxes; image score is binary, so AUC is degenerate: report accuracy/F1. License CC-BY-NC-4.0.
- CAFTB-Net: I did not find a public repo/weights; skipped (ask the supervisor/authors, or drop it).

## Metadata expected from Zang
`id, image, mask (null for authentic), label (0/1), template, tamper_type, compression (jpeg95/jpeg85/jpeg75/zalo/...), bbox`.
**Authentic images at every compression level are required**, else detection AUC/F1 are meaningless.

## Metrics (eval_sota.py)
Pixel (tampered only): IoU/F1 @0.5, per-image oracle threshold (upper bound), global dynamic threshold. Image: max-of-map score, AUC, detection F1 @0.5 / best.
Grouped overall / compression / template / tamper_type. `ela` and `random` are sanity baselines.


## Follow-up scoring and model limitations (2026-11-07)

ExternalMaps.predict returns (probability_map, native_score). Use --score native: TruFor uses its detection head when saved; a missing native score falls back to map maximum and is labeled score_source=map_max. All current V2 TruFor files contain native scores. ELA/random detection metrics are N/A, with pixel metrics retained. Per-image output records score_source. Use --vis 200 --vis-authentic 200 for paired views selected across the dataset. Corrected reports: results_v2_native/.

TextShield-R1 has not run: the active Python environment lacks both transformers and ms-swift (checked with importlib), and no fine-tuned TextShield checkpoint is installed in this project. The [official inference instructions](https://github.com/ant-research/TextShield#model-inference) require the checkpoint and the documented dependencies. No unmeasured minimum-VRAM claim is made. It remains an untested model, not a reported failure result.

CAFTB-Net search evidence: [ForensicHub's official model table](https://scu-zjz.github.io/ForensicHub-doc/zh/summary/model.html) lists a public CAFTB_Net reimplementation and no original-code link; the [paper](https://doi.org/10.1145/3686158) was also checked (publisher access denied). I did not verify an original-author downloadable checkpoint. This does NOT establish that no public checkpoint exists: ForensicHub's reproduction and [checkpoint discussion](https://github.com/scu-zjz/ForensicHub/issues/20) are leads. CAFTB-Net is excluded from this run pending verified weights/setup, and the former blanket no-public-weights claim is withdrawn.

V3: generated locally from upstream commit 76b49d061d8215f31bc3b12ecb5c2d7dacb032b9, reusing authentic V2 bytes. Run run_feedback.ps1 from the project root for V2 resolution ablations and V3; run_v3.ps1 requires best_adcd_resolution.json from the V2 report. V3 uses preds_v3 and results_v3_realistic/{official_mask,diff_mask}. All dataset paths and model folders are kept separate from V2.
