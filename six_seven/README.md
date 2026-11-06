# six_seven — Dâm Nguyễn (Machine B) package
```
kick_off.md            sprint brief
dataset_raw/           Zang's 500 receipt triplets (authentic/ tampered/ masks/)
benchmarks/            scripts: build_dataset_sample, adcdnet_infer, textshield_to_maps, eval_sota, models, run_all.sh, setup_sota.sh, README.md (details)
third_party/           ADCD-Net (ds.py patched), TruFor/test_docker, TextShield, weights/qt_table.pk
download_weights.sh    fetches ADCDNet.pth + docres.pkl (Google Drive); lists TruFor/TextShield weight sources
results_baseline/      ELA + random sanity-baseline results already computed on the real data
HANDOFF_dataset_audit_and_baselines.md   dataset audit + baseline numbers for Mỹ/Zang
```
**Windows (native, RTX 4060): see `README_WINDOWS.md`** (`setup_windows.ps1`, `run_all.ps1`). Linux: `bash download_weights.sh` then `cd benchmarks && bash run_all.sh`. SOTA numbers do NOT exist yet (no GPU/weights where this was prepared).
