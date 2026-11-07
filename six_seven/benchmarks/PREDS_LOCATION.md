# Published V3 failure-analysis handoff (T4 option b)

## Confirmed team-accessible paired probability maps

Each folder below contains 100 distinct receipt IDs, with authentic and tampered heatmap panels of the same receipt/variant (200 PNGs per configuration). Each panel is original | official ground truth | predicted forgery probability.

- [ADCD 512](https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask/vis/ext_adcdnet)
- [ADCD 1024](https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask/vis/ext_adcdnet_1024)
- [ADCD 2048](https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask/vis/ext_adcdnet_2048)
- [TruFor](https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask/vis/ext_trufor)

This satisfies the MD's >=100-pair visualization alternative. The run generated 200 paired examples/configuration per GT locally. The full numerical evaluation tables include every image, not only the visualization sample.

## Quantitative reports

- [Official-mask reports](https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask)
- [Difference-mask reports](https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/diff_mask)
- [Resolution comparison](https://github.com/dogtoro/six_seven/blob/dam/six_seven/benchmarks/results_v3_realistic/RESOLUTION_REPORT.md)

Native TruFor scores are in per_image.csv with score_source=native. ELA/random detection metrics are N/A. Both summaries provide compression breakdowns.

## Local optional raw arrays

Raw NPY/NPZ arrays remain in benchmarks/preds_v3/{adcdnet,adcdnet_1024,adcdnet_2048,trufor}/. v3_failure_analysis_maps.zip is a local 100-pair bundle containing 800 raw predictions, images, masks and metadata. These arrays have not been uploaded. The user cancelled full archive publication; its draft release was removed. No Drive link or full raw-map download is claimed.
