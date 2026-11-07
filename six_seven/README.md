# Six-Seven: active V3 benchmark

The active experiment is V3 realistic forgery: 300 authentic/tampered receipt pairs and 3,000 compression variants. Run from this directory:

    powershell -ExecutionPolicy Bypass -File ./run_v3.ps1

Models: ADCD-Net at 512/1024/2048 longest-side caps, TruFor, ELA and random. TruFor uses its native detection head. Baseline detection metrics are N/A; their localization metrics remain. Both official and difference masks are evaluated. Paired authentic/tampered visualizations are generated.

Inputs: dataset_v3_realistic/ and dataset_sample_v3/. Outputs: benchmarks/preds_v3/ and benchmarks/results_v3_realistic/{official_mask,diff_mask}/. See V3_STATUS.md, feedback_stage.txt and v3_only_stdout.log for progress. A successful full run creates v3_complete.json.

At the user's request, old active-project V1/V2 datasets and outputs were deleted; shared model weights, code, Git history and V3 data remain. The V2 resolution ablations and V2/V3 comparison are cancelled. Historical results remain in the separate Git checkout and GitHub history.

Limitations and missing-model evidence are documented in benchmarks/README.md. Model inputs, metadata, masks and generator/font provenance should accompany interpretation; completed execution alone does not establish model quality.
