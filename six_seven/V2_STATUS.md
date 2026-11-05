# Current status: FULL V2 RUN COMPLETE

Verified on 2026-11-06. Run finished approximately 01:19 Asia/Bangkok.

- OCR preparation: 5,000/5,000 records.
- ADCD-Net: all 5,000 expected prediction files present, nonempty.
- TruFor: all 5,000 expected prediction files present, nonempty.
- Official and difference-mask evaluations: each contains 20,000 rows, exact 5,000-image coverage per model, 2,500 authentic and 2,500 tampered per model, and 120 visualizations.
- Both summary CSV/Markdown files present. No fatal traceback or runner failure markers in the resumed log.
- Results: benchmarks/results_v2/official_mask/ and benchmarks/results_v2/diff_mask/.
- Model performance is poor: overall detection AUC approximately 0.496-0.500. Completion does not imply useful detection performance.
- Original template/tamper-type annotations remain missing; unknown labels must not be interpreted as verified semantic categories.
- Logs: v2_resume_stdout.log and v2_resume_stderr.log. Previous paused checkpoints below are historical.

---

# Dataset V2 preparation

Source: dataset_moi ZIP supplied on 2026-11-05.

- Raw images: dataset_v2/ (500 authentic, 500 tampered, 500 masks).
- Audit: dataset_v2_audit.json; all 500 pairs have zero changed pixels outside the official mask.
- The official mask and exact pixel difference mask are not identical. Coverage does not imply equality.
- Compression variants: dataset_sample_v2/; all 5,000 records and referenced image/mask files checked.
- Source metadata.json and manifest.jsonl are missing from the supplied ZIP. Template and tamper-type names currently fall back to width/region counts, and must not be reported as the actual V2 category labels.
- The builder supports the supplied note's list format for metadata.json, keyed by sample_id. Add that file to dataset_v2/ and rebuild before final evaluation.
- Existing V1 data, predictions, and results are preserved. V1 predictions must not be reused for V2, even though sample IDs match.
- The 20-image pilot passed on 2026-11-05: 20 finite prediction maps per neural model and 80 evaluation rows per ground truth across four models. Outputs: `benchmarks/results_v2_pilot_2/`; log: `v2_pilot_run.log`.
- Full V2 pipeline started with `run_v2.ps1` on 2026-11-05 as a persistent hidden process. Live logs: `v2_full_stdout.log`, `v2_full_stderr.log`; PID: `v2_full_process.pid`. ADCD-Net OCR preparation, inference, TruFor, and evaluation run in sequence. Completion is not yet verified.

## Search for missing inputs

Checked Downloads metadata/manifest filenames, project ZIPs (benchmark for sth.zip, six_seven.zip, files.zip, both dataset archives), and GitHub main/dam/zang trees (my shares the zang commit). Only old generated benchmark metadata was found. GitHub main contains the V2 generator, saved as generate_dataset_v2_source.py for reference. A reproduction of receipt_0001 with the documented seed and locally available DejaVu fonts did not match the supplied authentic image, tampered image, or mask pixel-for-pixel, so its generated metadata was not adopted. Original V2 metadata.json and manifest.jsonl remain required for verified category and field-level labels.

Full run stopped at the user's request on 2026-11-05. Existing OCR cache, predictions, datasets and pilot results retained. The OCR preparation stage supports reuse of completed ocr_base files; inference stages may rerun existing predictions with the current runner. No benchmark processes remain active.

Full run resumed at the user's request on 2026-11-05. Current logs: v2_resume_stdout.log and v2_resume_stderr.log. The runner reuses the OCR base cache; previous paused checkpoint is historical. Completion remains pending.
