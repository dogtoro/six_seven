# Run everything natively on Windows (RTX 4060)
1. Install Python 3.10 (python.org, tick "py launcher") and the latest NVIDIA driver.
2. Open PowerShell in this `six_seven` folder:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\setup_windows.ps1          # venv + packages + weights (ADCD-Net via gdown, TruFor via direct download)
   .\run_all.ps1 -Limit 20      # quick test (200 images)
   .\run_all.ps1                # full run (5000 images)
   ```
3. Results: `benchmarks\results\official_mask\summary.md` and `...\diff_mask\summary.md`; heatmap pictures in `...\vis\<model>\`.

If gdown fails: open https://drive.google.com/file/d/1-5BU3Bavs6SGJpaByua_FhDuUJGoo-iS/view in a browser, unzip, put `ADCDNet.pth` and `docres.pkl` into `third_party\weights\` (next to `qt_table.pk`).
Not run on Windows: TextShield-R1 (needs ~16 GB VRAM; use a bigger GPU) and CAFTB-Net (no public code).
What was changed for Windows: `jpeg2dct` replaced by a pure-Python version (checked against libjpeg: identical or +-1 at quality 100), `ds.py` temp-file handling fixed, TruFor run natively (output-path bug fixed) instead of Docker.
Untested on a real GPU/Windows by the author: if a step errors, send the full message.
