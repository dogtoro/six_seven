# V2 annotations ready

Source: dogtoro/six_seven main, commit 48c20726262658da76db6b751fc46db4d517b43c.
Original files are installed in dataset_v2/metadata.json and dataset_v2/manifest.jsonl.

Validation: both files contain the same 500 unique records. Template counts are cafe=125, supermarket=125, convenience=125, custom=125. Tamper counts are full_financial=159, grand_total_only=162, qty_and_total=179. Every annotated mask area, image dimension, bounding-box union, and generator-style grayscale difference count matched the local V2 data. Our stricter RGB difference counts are retained in benchmark metadata; grayscale conversion rounds away some small RGB differences.

The builder preserves semantic labels, original/forged field text, and field boxes. Social-simulation field boxes are scaled to their resized images (PIL inclusive coordinates). Source metadata/manifest disagreements and missing sample IDs fail explicitly. Metadata readers use UTF-8.

## Tonight's evaluation

From this project directory, run:

    powershell -ExecutionPolicy Bypass -File ./run_v2.ps1 -EvaluateOnly

This uses existing full V2 predictions and writes new labeled reports to benchmarks/results_v2_annotated/official_mask and diff_mask. Previous reports remain in benchmarks/results_v2. No GPU inference is needed if image and mask hashes are unchanged (validation recorded separately).

For a deliberate complete model rerun instead:

    powershell -ExecutionPolicy Bypass -File ./run_v2.ps1

No model or evaluation run was started during annotation integration. The earlier full run completed; new category-level reports subsequently completed on 2026-11-06; see V2_STATUS.md.

Validation finished: all 10,000 existing image/mask files are byte-identical, all 5,000 benchmark labels and fields match source annotations, and both metadata loaders accept the UTF-8 records. PowerShell syntax passed and four existing unit tests passed. The unrelated jpeg2dct shim test could not import its missing jpegio dependency; no dependency was installed. Annotation integration itself did not start a run; the subsequent user-requested annotated run is now complete.
