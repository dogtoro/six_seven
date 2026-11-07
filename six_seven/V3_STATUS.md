# Active work: V3 only

At the user request, V1/V2 active-project datasets, predictions, result folders and OCR caches were removed after verifying V3 independence. Shared code, model weights, V3 inputs and Git history were retained. Cleanup: v3_only_cleanup.json. Historical V1/V2 reports remain in GitHub and the separate Git checkout; they are not active inputs.

Standalone command: powershell -ExecutionPolicy Bypass -File ./run_v3.ps1

Current run: ADCD-Net at max-size 512/1024/2048, TruFor (native detection head), ELA and random (pixel metrics only). 300 pairs, 3000 compression variants. No V2 runs or V2/V3 comparison are run. A V3-only resolution ablation compares identical images at 512/1024/2048. Source authentic hashes are retained in dataset_v3_source_hashes.json; the audit does not require deleted V2 images.

Outputs: benchmarks/preds_v3/ and benchmarks/results_v3_realistic/{official_mask,diff_mask}/. Live stage: feedback_stage.txt. Logs: v3_resolution_stdout.log, v3_resolution_stderr.log. Completion requires v3_complete.json and a COMPLETE stage; at launch completion is pending.

## ask_dam (1).md applied to current scope

T1: native TruFor scores, map-max fallback when absent, and score_source CSV column. T2: ELA/random detection N/A. T4: 200 paired authentic/tampered views per model, with team publication pending completion. T5: TextShield dependency/checkpoint blocker and linked CAFTB search evidence in benchmarks/README.md. T6: root README and handoff updated to V3. T7: V3 generator/audit/preparation complete; model run underway. T3 and the V2/V3 comparison are cancelled by the user's V3-only scope change. They are not being claimed as complete.

Resolution update: six configurations (ADCD 512/1024/2048, TruFor, ELA, random), 18,000 rows per ground truth. Outputs include per-image prob_max, prob_mean, prob_fraction_ge_0_5 and results_v3_realistic/resolution_comparison.csv plus RESOLUTION_REPORT.md. The resolution comparison tests V3 sensitivity, not the sole cause of the historical V2 result.

## Team-analysis acceptance

T1/T2 are enforced in evaluation and completion checks: score_source=native for every TruFor row; ELA/random detection columns are N/A even if finite baseline scores are supplied. Three ADCD caps use identical V3 image IDs. T4: paired 200/class heatmaps, plus a 100-pair raw-map bundle. Final validation packages maps and publishes verified reports plus at least 100 paired receipts/configuration to dam. v3_complete.json is written only after the report checks, packaging and verified GitHub push succeed. Missing-model evidence remains in benchmarks/README.md. All work is V3 only; the literal V2 5,000-image tasks are cancelled. Resolution statistics and missing models are limitations to report, not assumed evidence of model success.

OCR accelerated on the RTX 4060 after matching-runtime validation; cached masks retained. Current logs: v3_fast_stdout.log and v3_fast_stderr.log. See OCR_ACCELERATION.md.
