# Annotated V2 benchmark complete

Completed 2026-11-06 approximately 17:59 Asia/Bangkok.

- Original metadata.json and manifest.jsonl imported from main commit 48c20726262658da76db6b751fc46db4d517b43c; both contain the same 500 source annotations.
- Source dimensions, mask areas, mask boxes, and generator-style difference counts matched all local V2 pairs.
- All 5,000 benchmark records now carry source template and tamper-type labels. Edited field text is preserved and field boxes are scaled for social_sim.
- All 10,000 generated image/mask files were byte-identical after annotation integration. Existing predictions remain compatible.
- ADCD-Net predictions were regenerated for all 5,000 images. TruFor's inference script reused its existing 5,000 V2 predictions; they were not regenerated during this rerun.
- ELA, random, ADCD-Net, and TruFor evaluation completed against both official and difference masks.
- Each result set contains 20,000 rows, exact 5,000-image coverage per model, four template groups (1,250 images each), and 120 visualizations. Total visualizations: 240.
- No fatal errors in the annotated run log.

## Current reports

benchmarks/results_v2_annotated/official_mask/summary.md
benchmarks/results_v2_annotated/diff_mask/summary.md

Previous unlabeled-category reports remain in benchmarks/results_v2 for history. The annotated reports supersede those category breakdowns. Detection AUC remains near 0.50; complete execution does not imply useful model performance. Detection AUC within an individual tamper-type group is undefined when only one class is present.

## Reproduction

run_v2.ps1 runs preparation, inference and evaluation. run_v2.ps1 -EvaluateOnly reuses saved predictions and regenerates reports. Raw images, large prediction maps and model weights remain local. Source annotations and benchmark metadata are included in the GitHub handoff.

Validation: v2_annotation_validation.json. Logs: v2_annotated_stdout.log and v2_annotated_stderr.log.
