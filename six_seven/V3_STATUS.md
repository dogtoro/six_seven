# V3 benchmark complete — MD-scoped team handoff

The user requested V3 only, replacing the original V2 5,000-image checklist. This experiment has 300 receipt pairs and 3,000 images per configuration. All six configurations and both mask evaluations completed and passed coverage checks.

## Required deliverables published on dam

- Both evaluation tables: 18,000 rows per GT, exact 3,000-image coverage per configuration.
- TruFor native detection scores with score_source=native, plus per-compression AUC.
- ELA/random detection metrics N/A, pixel metrics retained.
- ADCD 512/1024/2048 resolution comparison, probability statistics, pixel F1/IoU and detection AUC.
- 100 distinct authentic/tampered receipt pairs per neural configuration as probability-heatmap panels on GitHub (T4 option b). The local run generated 200/class/configuration for both GTs.
- Metadata, audit/provenance, source generator, scoring code, tests, missing-model evidence and updated handoff docs.

Initial result commit: f2be654c6384820d2508c849ec925dcc7d9106e2. Confirmed links are in benchmarks/PREDS_LOCATION.md. Model weights, runtime binaries and large raw-map archives are not required for option b and are not uploaded.

The later 19.16 GiB bulk upload was cancelled at the user's request; its draft release and partial assets were removed. Local raw maps and the 100-pair raw-map ZIP remain available. No bulk release is part of this handoff.

## Results and limitations

Official-mask ADCD F1@0.5: 512=0.02653, 1024=0.13735, 2048=0.15018. Detection AUC: 0.56188, 0.68336, 0.70025. Higher resolution helps V3 performance; this does not establish the sole cause of historical V2 behavior. Mean pixel probability decreases while mean per-image maximum probability rises. TextShield was not run (dependencies/checkpoint missing); the original-author CAFTB checkpoint was not verified. See benchmarks/README.md for source links.

V3 generation used pinned upstream code and bundled fonts; authentic images are byte-identical to the source V2 images. Seed/content and strict RGB/mask checks passed. OCR used the same detector with GPU acceleration after ten cached-mask comparisons passed. Source/font and OCR validation details accompany the repository handoff.
