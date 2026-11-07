# ask_dam (1).md — V3-only acceptance

The user replaced the original V2 tasks with a standalone V3 experiment: 300 receipt pairs and 3,000 images/configuration. These changes implement the feedback on V3; no claim is made that cancelled V2 ablations were completed.

- T1: ExternalMaps.predict returns (map, native_score). --score native uses the native score when present and labels map-max fallback explicitly. score_source is written in per_image.csv. Both GT evaluations and per-compression detection AUC are generated. Validation requires native scores for all TruFor rows.
- T2: ELA/random det_AUC, det_F1@0.5, det_F1_best are N/A in summarize(), regardless of incoming score values. Pixel metrics retained.
- T3: ADCD 512/1024/2048 on identical V3 images. A comparison report distinguishes mean per-image maximum probability from mean pixel probability, measures threshold crossing, F1/IoU and detection AUC. Caps do not upscale images. V3 sensitivity alone cannot prove the cause of the historical V2 result.
- T4: --vis 200 --vis-authentic 200 uses paired receipt/variant IDs. The completion validator checks paired coverage. A local ZIP packages 100 receipt pairs and 800 raw maps with images, GT and metadata. GitHub receives at least 100 paired receipts/configuration as heatmap panels after validation. See benchmarks/PREDS_LOCATION.md and v3_published.json.
- T5: Missing TextShield dependencies/checkpoint and linked CAFTB search evidence are in benchmarks/README.md. The unsupported blanket no-public-weights assertion has been withdrawn; no CAFTB result is fabricated.
- T6: README and handoff point to current V3 status; publication uses git add -f for markdown.
- T7: V3 generated from pinned upstream code, seed/content checked and strict RGB/mask audit passed. Both mask evaluations compare three ADCD caps, TruFor, ELA and random. V1/V2 active artifacts were deleted at the user request.

Live stage: feedback_stage.txt; logs: v3_resolution_stdout.log and v3_resolution_stderr.log. v3_complete.json requires results verification, packaging and a verified push to dam. Until it exists, completion and team accessibility remain pending.
